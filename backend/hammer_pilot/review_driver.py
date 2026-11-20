"""Review driver (T017): candidate-works capture and the packet release for the independent review (Decision B, runbook step 11).

Nothing here judges identity. It (1) lists the cases that need review (every automatic assignment of the primary pair plus the audit draw), (2) captures each pool
candidate's works from OpenAlex through the same hashed, budgeted recording transport as the candidate capture, and (3) builds Stage A and Stage B packets from explicit
allow-lists with `dossier`, scans them, and writes the reviewer-facing directory and a separate protected directory. It never chooses K, the works cap or a seed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import httpx

from hammer_pilot import dossier
from hammer_pilot.capture import RecordingTransport, classify_author_response, request_key
from hammer_pilot.common import canonical_json, write_text_exclusive
from hammer_pilot.replay import load_index

WORKS_URL = "https://api.openalex.org/works"
WORKS_SELECT = "id,doi,title,publication_year,primary_location,authorships"
ANY_FAILURE = ("provider_failed", "malformed")


class DriverError(ValueError):
    pass


def plan_reviewed(primary_case_ids: Sequence[str], predictions: Sequence[Mapping[str, str]], audit_case_ids: Sequence[str], *, condition: str = "C1",
                  policy: str = "selective_policy_v2") -> tuple[list[str], dict[str, str]]:
    """Cases to review and their (protected) origin flag. Automatic assignments of the primary pair are all reviewed; audit cases must be non-automatic primaries."""
    primary = set(primary_case_ids)
    outcome = {r["case_id"]: r["outcome"] for r in predictions if r["condition"] == condition and r["policy"] == policy and r["case_id"] in primary}
    if set(outcome) != primary:
        raise DriverError("every primary case needs a prediction")
    auto = sorted(c for c, o in outcome.items() if o == "auto")
    audit = sorted(set(audit_case_ids))
    bad = [c for c in audit if c not in primary or outcome[c] == "auto"]
    if bad:
        raise DriverError(f"audit cases must be non-automatic primary cases: {bad[:3]}")
    flags = {**{c: "automatic" for c in auto}, **{c: "audit_sample" for c in audit}}
    return sorted(flags), flags


def pool_items(capture_dir: Path, case_id: str) -> list[dict[str, Any]]:
    """Provider author objects of the case's R2 pool (primary then fallback), de-duplicated, in the provider's order. Empty for an empty or failed pool."""
    capture_dir = Path(capture_dir)
    index = {e["seq"]: e for e in load_index(capture_dir)}
    summary = json.loads((capture_dir / "cases" / f"{case_id}.json").read_text(encoding="utf-8"))
    items, seen = [], set()
    for part in (summary["R2_primary"], summary.get("R2_fallback")):
        if not part:
            continue
        e = index[part["seq"]]
        body = (capture_dir / e["body_file"]).read_bytes() if e.get("body_file") else None
        for item in classify_author_response(e.get("status"), body, e.get("error"))[2]:
            cid = str(item.get("id", "")).rsplit("/", 1)[-1]
            if cid and cid not in seen:
                seen.add(cid)
                items.append(item)
    return items[:10]


def works_params(author_id: str, cap: int) -> dict[str, Any]:
    if not author_id or not author_id.startswith("A") or not author_id[1:].isdigit():
        raise DriverError(f"not an OpenAlex author id: {author_id!r}")
    if isinstance(cap, bool) or not isinstance(cap, int) or cap < 1:
        raise DriverError("works cap must be a positive integer")
    return {"filter": f"author.id:{author_id}", "per-page": cap, "sort": "publication_date:desc", "select": WORKS_SELECT}


def parse_works(body: bytes | None) -> list[dict[str, Any]] | None:
    try:
        parsed = json.loads(body or b"")
    except ValueError:
        return None
    results = parsed.get("results") if isinstance(parsed, dict) else None
    return [r for r in results if isinstance(r, dict)] if isinstance(results, list) else None


async def capture_works(candidate_ids: Sequence[str], capture_dir: Path, *, inner_transport: httpx.AsyncBaseTransport, budget: int, cap: int,
                        mailto: str | None = None, api_key: str | None = None) -> dict[str, Any]:
    """One works request per distinct candidate, saved and hashed before the next. Resumable: already captured requests are served from disk and cost nothing.
    ProviderStop (401, 403, 429), BudgetExhausted and GuardStop propagate after the offending response has been saved."""
    capture_dir = Path(capture_dir)
    capture_dir.mkdir(parents=True, exist_ok=True)
    recorder = RecordingTransport(inner_transport, capture_dir, budget)
    recorder.load_existing()
    base = {**({"mailto": mailto} if mailto else {}), **({"api_key": api_key} if api_key else {})}
    out: dict[str, Any] = {}
    async with httpx.AsyncClient(transport=recorder, timeout=30) as client:
        for cid in sorted(set(candidate_ids)):
            params = {**base, **works_params(cid, cap)}
            recorder.label = f"W_{cid}"
            status = body = error = None
            try:
                response = await client.get(WORKS_URL, params=params)
                status, body = response.status_code, response.content
            except httpx.HTTPError as exc:
                error = type(exc).__name__
            entry = recorder.cache[request_key(client.build_request("GET", WORKS_URL, params=params))]
            works = parse_works(body) if (status is not None and status < 400) else None
            out[cid] = {"seq": entry["seq"], "sha256": entry["sha256"], "body_file": entry["body_file"], "http_status": status, "error": error,
                        "status": "ok" if works is not None else "failed", "works": len(works) if works is not None else 0}
    write_text_exclusive(capture_dir / f"works_summary_{len(out)}.json", canonical_json(out) + "\n")
    return out


def load_works(capture_dir: Path, candidate_ids: Sequence[str], cap: int) -> dict[str, list[dict[str, Any]]]:
    """Works for each candidate from the saved capture (offline). A candidate whose request failed has no entry, so its packet shows an empty works list."""
    capture_dir = Path(capture_dir)
    cache = {e["key"]: e for e in load_index(capture_dir)}
    result: dict[str, list[dict[str, Any]]] = {}
    for cid in candidate_ids:
        req = httpx.Request("GET", WORKS_URL, params=works_params(cid, cap))
        e = cache.get(request_key(req))
        if e and e.get("body_file") and e.get("status") and e["status"] < 400:
            works = parse_works((capture_dir / e["body_file"]).read_bytes())
            if works is not None:
                result[cid] = works
    return result


def build_release(case_inputs: Mapping[str, Mapping[str, Any]], flags: Mapping[str, str], *, seed: int | str, k: int, works_cap: int, gold_values: Sequence[str],
                  reviewer_dir: Path, protected_dir: Path) -> dict[str, Any]:
    """Build, scan and write the packets. `case_inputs[case] = {query_name, papers, designated_doi, pool_items, works_by_candidate}`. Any leak aborts the release."""
    if set(case_inputs) != set(flags):
        raise DriverError("case inputs and origin flags must cover exactly the same cases")
    released, crosswalks = [], {}
    for case in sorted(case_inputs):
        ci = case_inputs[case]
        released.append(dossier.release(dossier.build_stage_a_packet(case, ci["query_name"], ci["papers"], seed=seed, k=k, designated_doi=ci["designated_doi"]),
                                        gold_values=gold_values))
        if ci["pool_items"]:
            packet, crosswalk = dossier.build_stage_b_packet(case, ci["pool_items"], seed=seed, works_cap=works_cap, works_by_candidate=ci.get("works_by_candidate"))
            released.append(dossier.release(packet, gold_values=gold_values))
            crosswalks[case] = crosswalk
    hashes = dossier.write_release(reviewer_dir, protected_dir, released, crosswalks, dict(flags))
    queue = dossier.build_queue([p for p, _ in released], seed=seed)
    with open(Path(reviewer_dir) / "queue.json", "x", encoding="utf-8") as f:
        f.write(json.dumps(queue, indent=1) + "\n")
    return {"packets": len(released), "cases": len(case_inputs), "cases_with_stage_b": len(crosswalks), "packet_hashes": hashes, "queue_length": len(queue)}
