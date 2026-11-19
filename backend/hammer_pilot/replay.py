"""Offline replay of frozen captures through the committed five-signal implementation.

No network, no application database, no Chroma. Candidate and enrichment objects are rebuilt in memory from
captured raw responses; enrichment is re-run through the production ``CandidateEnrichmentService`` against a
transport that serves only captured responses. A request that was never captured aborts the replay
(``PilotDataError``): evidence is never invented or silently repaired.

Scoring and decisions use the existing ``score_evidence``, ``rank_candidates`` and ``evaluate_decision``.
Ranking is unchanged; **candidates scored on different signal sets are not directly comparable** (the score is
renormalised over available signals). This limitation is recorded in the manifest and in every pool summary.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

import config
from author_resolution.candidates import AuthorCandidateInput, OpenAlexCandidate
from author_resolution.context import QueryContext
from author_resolution.enrichment import CandidateEnrichmentService
from author_resolution.policy import AUTO_RESOLVED, MANUAL_REVIEW, evaluate_decision
from author_resolution.resolver import rank_candidates
from hammer_pilot.capture import classify_author_response, request_key
from hammer_pilot.common import (
    CONDITIONS, POLICIES, PilotDataError, canonical_json, read_csv, sha256_bytes, strip_volatile,
    write_csv_exclusive, write_text_exclusive,
)
from hammer_pilot.context_rules import derive_contexts, register_by_case

PREDICTION_FIELDS = ["run_id", "case_id", "condition", "policy", "outcome", "pool_status", "pool_size", "fallback_status", "selected_author_id",
                     "top_author_id", "top_score", "second_score", "margin", "dominance", "threshold_gates_passed", "auto_blockers",
                     "top_signal_set", "candidate_signal_sets", "different_signal_sets_in_pool", "reason"]
RETRIEVAL_FIELDS = ["run_id", "case_id", "arm", "pool_status", "error_code", "fallback_status", "pool_size", "ordered_candidate_ids",
                    "response_seq", "response_body_file", "response_sha256", "shares_response_with_other_arm"]


class ReplayTransport(httpx.AsyncBaseTransport):
    """Serves only captured responses; verifies each body's SHA-256."""

    def __init__(self, capture_dir: Path, entries_by_key: dict[str, dict[str, Any]]):
        self.dir, self.entries = Path(capture_dir), entries_by_key

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        key = request_key(request)
        entry = self.entries.get(key)
        if entry is None:
            raise PilotDataError(f"replay needs a capture that does not exist: {key}")
        if entry.get("error"):
            if "Timeout" in entry["error"]:
                raise httpx.ReadTimeout("recorded timeout", request=request)
            raise httpx.ConnectError("recorded request failure", request=request)
        body = (self.dir / entry["body_file"]).read_bytes()
        if sha256_bytes(body) != entry["sha256"]:
            raise PilotDataError(f"capture hash mismatch for {entry['body_file']}")
        return httpx.Response(entry["status"], content=body, headers={"content-type": entry.get("content_type", "application/json")}, request=request)


def load_index(capture_dir: Path) -> list[dict[str, Any]]:
    path = Path(capture_dir) / "capture_index.jsonl"
    if not path.is_file():
        raise PilotDataError("captures/capture_index.jsonl is missing")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_capture_hashes(capture_dir: Path, entries: list[dict[str, Any]]) -> list[str]:
    problems = []
    for e in entries:
        if e.get("error"):
            continue
        f = Path(capture_dir) / (e.get("body_file") or "")
        if not e.get("sha256"):
            problems.append(f"seq {e['seq']}: no sha256 recorded")
        elif not f.is_file():
            problems.append(f"seq {e['seq']}: body file missing")
        elif sha256_bytes(f.read_bytes()) != e["sha256"]:
            problems.append(f"seq {e['seq']}: sha256 mismatch")
    return problems


def _items(capture_dir: Path, by_seq: dict[int, dict[str, Any]], part: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not part:
        return []
    e = by_seq[part["seq"]]
    body = (Path(capture_dir) / e["body_file"]).read_bytes() if e.get("body_file") else None
    return classify_author_response(e.get("status"), body, e.get("error"))[2]


def _outcome_for_v2(out) -> str:
    if out.top_score is None:
        return "no_score"
    return {AUTO_RESOLVED: "auto", MANUAL_REVIEW: "manual"}.get(out.status, "unresolved")


def _row(base: dict[str, Any], policy: str, outcome: str, ranked, out, selected: str, reason: str, blockers: list[str], gates: bool) -> dict[str, Any]:
    sets = {r.candidate.source_author_id: list(r.score.signal_set) for r in ranked}
    return {**base, "policy": policy, "outcome": outcome, "selected_author_id": selected,
            "top_author_id": ranked[0].candidate.source_author_id if ranked else "",
            "top_score": out.top_score if out else None, "second_score": out.second_score if out else None,
            "margin": out.margin if out else None, "dominance": out.dominance if out else None,
            "threshold_gates_passed": gates, "auto_blockers": canonical_json(blockers),
            "top_signal_set": canonical_json(sets.get(ranked[0].candidate.source_author_id, [])) if ranked else "[]",
            "candidate_signal_sets": canonical_json(sets),
            "different_signal_sets_in_pool": len({tuple(v) for v in sets.values()}) > 1, "reason": reason}


def evaluate_policies(base: dict[str, Any], pool_status: str, ranked) -> list[dict[str, Any]]:
    """Return one row per policy. Provider failure, empty pool, no-score, manual and unresolved stay distinct."""
    if pool_status in ("provider_failed", "empty"):
        outcome = "provider_failed" if pool_status == "provider_failed" else "empty_pool"
        return [_row(base, p, outcome, [], None, "", pool_status, [], False) for p in POLICIES]
    out = evaluate_decision(ranked)
    top = ranked[0]
    top_id = top.candidate.source_author_id
    rows = []
    for policy in POLICIES:
        if policy == "forced_top1":
            ok = top.score.score is not None
            rows.append(_row(base, policy, "auto" if ok else "no_score", ranked, out, top_id if ok else "", "rank 1 selected" if ok else "rank 1 has no score", [], False))
        elif policy == "selective_policy_v2":
            outcome = _outcome_for_v2(out)
            rows.append(_row(base, policy, outcome, ranked, out, top_id if outcome == "auto" else "", out.reason, list(out.auto_blockers), out.threshold_gates_passed))
        else:   # legacy_gates_plus_p3: P0, P1, P2, P3, P9, P10; P4-P8 (blockers) not applied
            if out.top_score is None:
                outcome = "no_score"
            elif out.threshold_gates_passed:
                outcome = "auto"
            elif out.top_score >= config.AUTHOR_MANUAL_SCORE_THRESHOLD:
                outcome = "manual"
            else:
                outcome = "unresolved"
            rows.append(_row(base, policy, outcome, ranked, out, top_id if outcome == "auto" else "", "legacy gates + P3 (P4-P8 not applied)", [], out.threshold_gates_passed))
    return rows


def _evidence_snapshot(case: str, condition: str, ranked) -> dict[str, Any]:
    return strip_volatile({"case_id": case, "condition": condition, "candidates": [
        {"rank": i, "author_id": r.candidate.source_author_id, "score": r.score.score, "signal_set": list(r.score.signal_set),
         "effective_weights": r.score.effective_weights,
         "evidence": [{"signal": e.signal_name, "status": e.status, "availability": e.availability, "score": e.normalized_score,
                       "explanation": e.explanation, "provenance": e.provenance} for e in r.evidence]}
        for i, r in enumerate(ranked, 1)]})


async def replay(pilot_dir: Path, out_dir: Path, run_id: str = "run") -> dict[str, Any]:
    pilot_dir, out_dir = Path(pilot_dir), Path(out_dir)
    capture_dir = pilot_dir / "captures"
    entries = load_index(capture_dir)
    problems = verify_capture_hashes(capture_dir, entries)
    if problems:
        raise PilotDataError("capture integrity problems: " + "; ".join(problems))
    by_seq = {e["seq"]: e for e in entries}
    transport = ReplayTransport(capture_dir, {e["key"]: e for e in entries})
    seeds = sorted(read_csv(pilot_dir / "seeds.csv", {"case_id", "query_text", "context_c1_json", "context_c1x_json"}), key=lambda r: r["case_id"])
    reg_path = pilot_dir / "doi_register.csv"
    register = register_by_case(read_csv(reg_path, {"case_id", "doi", "purpose"}) if reg_path.stat().st_size else [])
    predictions, retrieval, snapshots = [], [], []
    for seed in seeds:
        case = seed["case_id"].strip()
        summary_path = capture_dir / "cases" / f"{case}.json"
        if not summary_path.is_file():
            raise PilotDataError(f"no capture summary for {case}")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        contexts = derive_contexts(seed, register.get(case, []))
        for arm, part in (("R0", summary["R0"]), ("R2", summary["R2_primary"])):
            fallback = summary["R2_fallback"] if arm == "R2" else None
            pool = summary["r2_pool_candidate_ids"] if arm == "R2" else part["candidate_ids"]
            if arm == "R0":
                status = "provider_failed" if part["status"] in ("provider_failed", "malformed") else part["status"]
            else:
                status = summary["r2_pool_status"]
            shared = summary["R0"]["seq"] == summary["R2_primary"]["seq"]
            retrieval.append({"run_id": run_id, "case_id": case, "arm": arm, "response_seq": part["seq"], "response_body_file": part.get("body_file") or "",
                              "response_sha256": part["sha256"] or "", "shares_response_with_other_arm": shared, "pool_status": status, "error_code": part["error_code"] or (fallback or {}).get("error_code") or "",
                              "fallback_status": (fallback or {}).get("status", "") if arm == "R2" else "", "pool_size": len(pool),
                              "ordered_candidate_ids": canonical_json(pool)})
        pool_status = summary["r2_pool_status"]
        items = _items(capture_dir, by_seq, summary["R2_primary"]) + _items(capture_dir, by_seq, summary["R2_fallback"])
        for condition in CONDITIONS:
            base = {"run_id": run_id, "case_id": case, "condition": condition, "pool_status": pool_status, "pool_size": len(summary["r2_pool_candidate_ids"]),
                    "fallback_status": (summary["R2_fallback"] or {}).get("status", "")}
            ranked = []
            if pool_status == "ok":
                qctx = QueryContext.from_any(contexts[condition])
                candidates, seen = [], set()
                for item in items:
                    c = OpenAlexCandidate.from_openalex(item, AuthorCandidateInput(summary["query_text"]), datetime(2000, 1, 1))
                    if c and c.source_author_id not in seen:
                        seen.add(c.source_author_id)
                        candidates.append(c)
                report = await CandidateEnrichmentService(transport=transport).enrich(candidates, qctx)
                ranked = rank_candidates(report.candidates, qctx)
                snapshots.append(_evidence_snapshot(case, condition, ranked))
            predictions += evaluate_policies(base, pool_status, ranked)
    write_csv_exclusive(out_dir / "predictions.csv", PREDICTION_FIELDS, predictions)
    write_csv_exclusive(out_dir / "retrieval.csv", RETRIEVAL_FIELDS, retrieval)
    write_text_exclusive(out_dir / "evidence_snapshot.jsonl", "".join(canonical_json(s) + "\n" for s in snapshots))
    return {"predictions": len(predictions), "retrieval_rows": len(retrieval), "snapshots": len(snapshots)}
