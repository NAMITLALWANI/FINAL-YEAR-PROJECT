"""Author-candidate (R0, R2) and enrichment capture with per-response save + SHA-256.

Every HTTP response is written to its own file and indexed (append-only) *before* the next request is
issued. Raw bodies are preserved verbatim, including provider errors and malformed bodies. API keys and the
polite-pool mailto are never written to any file (parameters are sanitised).

R0: raw trimmed query, filter=display_name.search, per-page 10, page 1, no normalisation, no fallback.
R2: committed ``clean_query_name`` + initials-only fallback (``search=``) after a *successful empty* primary.
Enrichment (C1 / C1x only) runs the production ``CandidateEnrichmentService`` through the recording transport,
so replay exercises exactly the same request code. Identical requests are captured once and shared.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from author_resolution.candidates import (
    AuthorCandidateInput, OpenAlexCandidate, _has_initial_token, clean_query_name,
)
from author_resolution.context import QueryContext
from author_resolution.enrichment import CandidateEnrichmentService
from hammer_pilot.common import (
    SECRET_PARAMS, PilotDataError, canonical_json, parse_ts, read_csv, sha256_bytes, sha256_file,
    write_bytes_exclusive, write_text_exclusive,
)
from hammer_pilot.context_rules import derive_contexts, register_by_case

AUTHORS_URL = "https://api.openalex.org/authors"
PER_PAGE = 10


class BudgetExhausted(RuntimeError):
    pass


class ProviderStop(RuntimeError):
    """Authentication (401/403) or rate-limit (429) response: the capture must stop immediately, never retry."""

    def __init__(self, status: int):
        super().__init__(f"provider returned HTTP {status}; capture stopped")
        self.status = status


def _now() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds") + "Z"


def request_key(request: httpx.Request) -> str:
    params = sorted((k, v) for k, v in request.url.params.multi_items() if k not in SECRET_PARAMS)
    return f"{request.method} {request.url.path}?{urlencode(params)}"


def sanitized_params(request: httpx.Request) -> dict[str, str]:
    return {k: v for k, v in request.url.params.multi_items() if k not in SECRET_PARAMS}


def classify_author_response(status: int | None, body: bytes | None, error: str | None) -> tuple[str, str | None, list[dict[str, Any]]]:
    """Return (status, error_code, result_items). status: ok | empty | provider_failed | malformed."""
    if error:
        return "provider_failed", error, []
    if status == 429:
        return "provider_failed", "rate_limited", []
    if status is None or status >= 400:
        return "provider_failed", "http_error", []
    try:
        parsed = json.loads(body or b"")
    except ValueError:
        return "malformed", "invalid_json", []
    results = parsed.get("results") if isinstance(parsed, dict) else None
    if not isinstance(results, list):
        return "malformed", "missing_results", []
    items = [r for r in results if isinstance(r, dict)]
    valid = [r for r in items if OpenAlexCandidate.from_openalex(r, AuthorCandidateInput("x"), datetime(2000, 1, 1)) is not None]
    return ("ok" if valid else "empty"), None, valid


def candidate_ids_in_order(items: list[dict[str, Any]], exclude: set[str] | None = None) -> list[str]:
    seen: list[str] = []
    for item in items:
        c = OpenAlexCandidate.from_openalex(item, AuthorCandidateInput("x"), datetime(2000, 1, 1))
        if c and c.source_author_id not in seen and c.source_author_id not in (exclude or set()):
            seen.append(c.source_author_id)
    return seen


class RecordingTransport(httpx.AsyncBaseTransport):
    """Delegates to ``inner``; saves and hashes each new response before returning it; enforces a budget."""

    def __init__(self, inner: httpx.AsyncBaseTransport, capture_dir: Path, budget: int):
        self.inner = inner
        self.dir = Path(capture_dir)
        self.budget = budget
        self.made = 0
        self.seq = 0
        self.cache: dict[str, dict[str, Any]] = {}
        self.label = "unlabelled"
        self.index_path = self.dir / "capture_index.jsonl"

    def load_existing(self) -> None:
        if self.index_path.is_file():
            for line in self.index_path.read_text(encoding="utf-8").splitlines():
                entry = json.loads(line)
                self.cache[entry["key"]] = entry
                self.seq = max(self.seq, entry["seq"])

    def _append(self, entry: dict[str, Any]) -> None:
        with open(self.index_path, "a", encoding="utf-8") as stream:
            stream.write(canonical_json(entry) + "\n")
            stream.flush()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        key = request_key(request)
        if key in self.cache:
            return self._from_entry(self.cache[key], request)
        if self.made >= self.budget:
            raise BudgetExhausted(f"request budget of {self.budget} reached")
        self.made += 1
        self.seq += 1
        entry: dict[str, Any] = {"seq": self.seq, "label": self.label, "key": key, "method": request.method,
                                 "endpoint": f"{request.url.scheme}://{request.url.host}{request.url.path}",
                                 "params": sanitized_params(request), "captured_at": _now()}
        try:
            response = await self.inner.handle_async_request(request)
            body = await response.aread()
        except httpx.HTTPError as exc:
            entry.update({"status": None, "error": type(exc).__name__, "body_file": None, "sha256": None, "bytes": 0, "json_valid": False})
            self._append(entry)
            self.cache[key] = entry
            raise
        name = f"{self.seq:05d}_{self.label}.body"
        write_bytes_exclusive(self.dir / "bodies" / name, body)
        try:
            json.loads(body)
            valid = True
        except ValueError:
            valid = False
        entry.update({"status": response.status_code, "error": None, "body_file": f"bodies/{name}", "sha256": sha256_bytes(body),
                      "bytes": len(body), "json_valid": valid,
                      "content_type": response.headers.get("content-type", "application/json")})
        self._append(entry)
        self.cache[key] = entry
        if response.status_code in (401, 403, 429):
            raise ProviderStop(response.status_code)          # response is already saved and hashed
        return httpx.Response(response.status_code, content=body, headers={"content-type": entry["content_type"]}, request=request)

    def _from_entry(self, entry: dict[str, Any], request: httpx.Request) -> httpx.Response:
        if entry.get("error"):
            raise _exception_for(entry["error"], request)
        body = (self.dir / entry["body_file"]).read_bytes()
        return httpx.Response(entry["status"], content=body, headers={"content-type": entry.get("content_type", "application/json")}, request=request)


def _exception_for(name: str, request: httpx.Request) -> httpx.HTTPError:
    if "Timeout" in name:
        return httpx.ReadTimeout("recorded timeout", request=request)
    return httpx.ConnectError("recorded request failure", request=request)


@dataclass
class CaptureResult:
    completed_cases: list[str]
    budget_exhausted: bool
    requests_made: int
    provider_stop_status: int | None = None


def verify_seed_freeze(pilot_dir: Path) -> dict[str, Any]:
    freeze_path = pilot_dir / "seed_freeze.json"
    if not freeze_path.is_file():
        raise PilotDataError("seed_freeze.json is required: seeds must be frozen before any candidate generation")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for name, key in (("seeds.csv", "seeds_sha256"), ("doi_register.csv", "doi_register_sha256")):
        if sha256_file(pilot_dir / name) != freeze.get(key):
            raise PilotDataError(f"{name} changed after the seed freeze; create a new dataset version instead of editing it")
    parse_ts(freeze.get("frozen_at", ""), "frozen_at")
    return freeze


async def run_capture(pilot_dir: Path, *, inner_transport: httpx.AsyncBaseTransport, budget: int, resume: bool = False,
                      mailto: str | None = None, api_key: str | None = None) -> CaptureResult:
    pilot_dir = Path(pilot_dir)
    freeze = verify_seed_freeze(pilot_dir)
    seeds = sorted(read_csv(pilot_dir / "seeds.csv", {"case_id", "query_text", "context_c1_json", "context_c1x_json"}), key=lambda r: r["case_id"])
    register = register_by_case(read_csv(pilot_dir / "doi_register.csv", {"case_id", "doi", "purpose"}) if (pilot_dir / "doi_register.csv").stat().st_size else [])
    cap = pilot_dir / "captures"
    progress_path = cap / "progress.jsonl"
    if cap.exists() and any(cap.iterdir()) and not resume:
        raise PilotDataError("captures/ already exists; refusing to overwrite or mix data (use --resume only to continue an interrupted run)")
    recorder = RecordingTransport(inner_transport, cap, budget)
    done: set[str] = set()
    if resume and progress_path.is_file():
        events = [json.loads(line) for line in progress_path.read_text(encoding="utf-8").splitlines()]
        if any(e.get("seeds_sha256") != freeze["seeds_sha256"] for e in events):
            raise PilotDataError("existing captures belong to a different seed freeze")
        if any(e["event"] in ("budget_exhausted", "provider_stop") for e in events):
            raise PilotDataError("a previous run stopped with a partially captured case; resume would mix data. Start a new capture directory")
        done = {e["case_id"] for e in events if e["event"] == "case_done"}
        recorder.load_existing()
    if not (cap / "capture_config.json").exists():
        write_text_exclusive(cap / "capture_config.json", canonical_json({
            "toolkit": "hammer_pilot", "request_budget": budget, "authors_endpoint": AUTHORS_URL, "per_page": PER_PAGE,
            "r0": "filter=display_name.search:{trimmed query}, no normalisation, no fallback",
            "r2": "clean_query_name + initials-only search= fallback after successful empty primary",
            "enrichment": "production CandidateEnrichmentService via recording transport; C1 and C1x only",
            "seeds_sha256": freeze["seeds_sha256"], "secrets_stored": False}) + "\n")

    def log(event: dict[str, Any]) -> None:
        with open(progress_path, "a", encoding="utf-8") as stream:
            stream.write(canonical_json({**event, "seeds_sha256": freeze["seeds_sha256"]}) + "\n")

    base = {**({"mailto": mailto} if mailto else {}), **({"api_key": api_key} if api_key else {})}
    completed: list[str] = []
    exhausted = False
    stop_status: int | None = None
    async with httpx.AsyncClient(transport=recorder, timeout=30) as client:
        for seed in seeds:
            case = seed["case_id"].strip()
            if case in done:
                continue
            try:
                summary = await _capture_case(client, recorder, seed, register.get(case, []), base)
                write_text_exclusive(cap / "cases" / f"{case}.json", canonical_json(summary) + "\n")
                log({"event": "case_done", "case_id": case})
                completed.append(case)
            except BudgetExhausted:
                log({"event": "budget_exhausted", "case_id": case})
                exhausted = True
                break
            except ProviderStop as stop:
                log({"event": "provider_stop", "case_id": case, "http_status": stop.status})
                stop_status = stop.status
                break
    return CaptureResult(completed, exhausted, recorder.made, stop_status)


async def _get_author_page(client: httpx.AsyncClient, recorder: RecordingTransport, label: str, params: dict[str, Any], base: dict[str, str]) -> dict[str, Any]:
    recorder.label = label
    error = None
    status = None
    body = None
    try:
        response = await client.get(AUTHORS_URL, params={**base, **params})
        status, body = response.status_code, response.content
    except httpx.HTTPError as exc:
        error = type(exc).__name__
    entry = recorder.cache[request_key(client.build_request("GET", AUTHORS_URL, params={**base, **params}))]
    kind, code, items = classify_author_response(status, body, error)
    return {"seq": entry["seq"], "sha256": entry["sha256"], "body_file": entry["body_file"], "http_status": status, "status": kind, "error_code": code,
            "candidate_ids": candidate_ids_in_order(items)}


async def _capture_case(client: httpx.AsyncClient, recorder: RecordingTransport, seed: dict[str, str], register_rows: list[dict[str, str]], base: dict[str, str]) -> dict[str, Any]:
    case = seed["case_id"].strip()
    query = seed["query_text"].strip()
    contexts = derive_contexts(seed, register_rows)
    r0 = await _get_author_page(client, recorder, f"{case}_R0", {"filter": f"display_name.search:{query}", "per-page": PER_PAGE}, base)
    cleaned = clean_query_name(query) or query
    r2p = await _get_author_page(client, recorder, f"{case}_R2_primary", {"filter": f"display_name.search:{cleaned}", "per-page": PER_PAGE}, base)
    r2f = None
    if r2p["status"] == "empty" and _has_initial_token(cleaned):
        r2f = await _get_author_page(client, recorder, f"{case}_R2_fallback", {"search": cleaned, "per-page": PER_PAGE}, base)
    pool = list(r2p["candidate_ids"])
    if r2f:
        pool += [i for i in r2f["candidate_ids"] if i not in pool]
    if r2p["status"] in ("provider_failed", "malformed") or (r2f and r2f["status"] in ("provider_failed", "malformed")):
        pool_status = "provider_failed"
    else:
        pool_status = "ok" if pool else "empty"
    enrichment: dict[str, Any] = {}
    if pool_status == "ok":
        items = _pool_items(recorder, r2p, r2f)
        for condition in ("C1", "C1x"):
            ctx = QueryContext.from_any(contexts[condition])
            if not (ctx.has_publications or ctx.has_coauthor_ids):
                enrichment[condition] = "not_required"
                continue
            recorder.label = f"{case}_enrich_{condition}"
            candidates = [c for c in (OpenAlexCandidate.from_openalex(i, AuthorCandidateInput(query), datetime(2000, 1, 1)) for i in items) if c]
            report = await CandidateEnrichmentService(transport=recorder).enrich(candidates, ctx)
            enrichment[condition] = report.summary()["candidates"] | {"_query_works_status": report.query_works_status}
    return {"case_id": case, "query_text": query, "cleaned_query": cleaned, "R0": r0, "R2_primary": r2p, "R2_fallback": r2f,
            "r2_pool_candidate_ids": pool, "r2_pool_status": pool_status, "enrichment": enrichment}


def _pool_items(recorder: RecordingTransport, r2p: dict[str, Any], r2f: dict[str, Any] | None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for part in (r2p, r2f):
        if not part:
            continue
        entry = next(e for e in recorder.cache.values() if e["seq"] == part["seq"])
        items += classify_author_response(entry["status"], (recorder.dir / entry["body_file"]).read_bytes() if entry["body_file"] else None, entry.get("error"))[2]
    return items
