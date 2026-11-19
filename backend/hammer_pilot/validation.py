"""Pilot dataset validator (15-case schemas). Reports problems; never repairs or edits input."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from author_resolution.context import QueryContext, normalize_doi
from hammer_pilot.capture import verify_seed_freeze
from hammer_pilot.common import (
    CONDITIONS, DOI_PURPOSES, OUTCOMES, POLICIES, PilotDataError, parse_ts, read_csv,
)
from hammer_pilot.context_rules import derive_contexts, register_by_case
from hammer_pilot.replay import load_index, verify_capture_hashes

PLANNED = {"resolved": 10, "unresolved": 5}
STATUSES = {"resolved", "unresolved", "uncertain"}
JUDGMENTS = {"same", "not_same", "cannot_tell"}
FORBIDDEN_REVIEW_COLUMNS = {"rank", "score", "decision", "outcome", "top_score", "predicted_status", "candidate_rank", "selected_candidate", "policy"}
FORBIDDEN_REVIEW_TEXT = re.compile(r"(hammer|auto_selected|manual_selection_required|candidate rank|\brank\s*#?\d|\bscore\s*[:=]\s*\d)", re.IGNORECASE)
FORBIDDEN_STAGE_B_COLUMNS = {"rank", "score", "decision", "outcome", "top_score", "predicted_status"}
OPENALEX_ID = re.compile(r"^(?:https?://openalex\.org/)?[AWI]\d+$", re.IGNORECASE)


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.ok, "errors": self.errors, "warnings": self.warnings, "info": self.info}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold())


def validate_pilot(pilot_dir: Path, predictions_csv: Path | None = None) -> ValidationReport:
    pilot_dir = Path(pilot_dir)
    rep = ValidationReport()
    err, warn = rep.errors.append, rep.warnings.append
    try:
        seeds = read_csv(pilot_dir / "seeds.csv", {"case_id", "query_text", "identity_group_id", "planned_status", "context_c1_json",
                                                   "context_c1x_json", "context_modified_after_candidates_seen"})
        reg_rows = read_csv(pilot_dir / "doi_register.csv", {"case_id", "doi", "purpose", "justification_if_both"})
    except PilotDataError as exc:
        err(str(exc))
        return rep
    ids = [s["case_id"].strip() for s in seeds]
    if len(ids) != len(set(ids)):
        err("seeds: duplicate case_id")
    if len(seeds) != 15:
        err(f"seeds: expected 15 planned cases, found {len(seeds)}")
    planned = {k: sum(1 for s in seeds if s["planned_status"].strip() == k) for k in PLANNED}
    if planned != PLANNED:
        err(f"seeds: planned composition must be {PLANNED}, found {planned}")
    groups = [s["identity_group_id"].strip() for s in seeds]
    if len(groups) != len(set(groups)) or any(not g for g in groups):
        err("seeds: identity_group_id must be present and unique (one case per underlying person)")
    queries = [_norm(s["query_text"]) for s in seeds]
    if len(queries) != len(set(queries)):
        err("seeds: duplicate query text")
    if any(s["context_modified_after_candidates_seen"].strip().lower() not in ("false", "0", "") for s in seeds):
        err("seeds: context was modified after candidates were seen")
    # --- seed freeze
    freeze: dict[str, Any] = {}
    try:
        freeze = verify_seed_freeze(pilot_dir)
    except (PilotDataError, OSError, ValueError) as exc:
        err(f"seed freeze: {exc}")
    # --- DOI register and leakage
    try:
        register = register_by_case(reg_rows)
    except PilotDataError as exc:
        err(str(exc))
        register = {}
    for row in reg_rows:
        if row["purpose"].strip() == "both" and not row["justification_if_both"].strip():
            err(f"DOI register: purpose 'both' needs a justification ({row['case_id']})")
    doi_cases: dict[str, set[str]] = {}
    for r in reg_rows:
        d = normalize_doi(r["doi"])
        if d:
            doi_cases.setdefault(d, set()).add(r["case_id"].strip())
    for d, cs in sorted(doi_cases.items()):
        if len(cs) > 1:
            err(f"DOI register: DOI {d} is used by several cases {sorted(cs)} (gold evidence or query context); one case per underlying person requires disjoint DOIs")
    leaks: dict[str, list[str]] = {}
    for s in seeds:
        case = s["case_id"].strip()
        try:
            ctx = derive_contexts(s, register.get(case, []))
        except PilotDataError as exc:
            err(str(exc))
            continue
        registered = {r["doi"] for r in register.get(case, [])}
        for doi in QueryContext.from_any(json.loads(s["context_c1_json"] or "{}")).publication_dois:
            if doi not in registered:
                err(f"{case}: DOI {doi} in the C1 seed is not in the DOI register")
        if set(ctx["both_dois"]) & set(QueryContext.from_any(ctx["C1"]).publication_dois):
            err(f"{case}: a 'both' DOI is present in the primary C1 context; it belongs in C1x only")
        if ctx["removed_from_c1"]:
            leaks[case] = ctx["removed_from_c1"]
            warn(f"{case}: C1 seed DOI(s) {ctx['removed_from_c1']} overlap gold evidence; derived primary C1 excludes them (seed and register preserved); publication overlap for them is exploratory (C1x)")
    rep.info["doi_overlap_cases"] = leaks
    # --- Stage A: two separate reviewer records plus an adjudicated final label
    labels: dict[str, dict[str, str]] = {}
    review_text: dict[str, str] = {}
    first_review_ts = None
    last_review_ts = None
    try:
        reviews: dict[str, dict[str, dict[str, str]]] = {}
        reviewer_ids: dict[str, str] = {}
        for tag in ("a", "b"):
            path = pilot_dir / f"review_{tag}.csv"
            if not path.is_file():
                raise PilotDataError(f"Missing file: {path.name} (a separate review record per reviewer is required)")
            with open(path, encoding="utf-8") as stream:
                header = set(stream.readline().strip().split(","))
            if header & FORBIDDEN_REVIEW_COLUMNS:
                err(f"review_{tag}: reviewer submissions must not contain candidate ranks, scores or decisions; forbidden columns {sorted(header & FORBIDDEN_REVIEW_COLUMNS)}")
            rows = read_csv(path, {"case_id", "reviewer_id", "status", "confidence", "rationale", "evidence_refs_json", "gold_dois_json", "submitted_at"})
            ids_in_file = {r["reviewer_id"].strip() for r in rows}
            if len(ids_in_file) != 1 or "" in ids_in_file:
                err(f"review_{tag}: exactly one non-empty reviewer_id is required per review file")
            reviewer_ids[tag] = next(iter(ids_in_file)) if len(ids_in_file) == 1 else ""
            by_case = {r["case_id"].strip(): r for r in rows}
            if len(by_case) != len(rows):
                err(f"review_{tag}: a case is reviewed more than once")
            for case in ids:
                if case not in by_case:
                    err(f"review_{tag}: missing review for {case}")
            for case, r in by_case.items():
                if r["status"].strip() not in STATUSES:
                    err(f"review_{tag} {case}: invalid status")
                try:
                    refs = json.loads(r["evidence_refs_json"] or "[]")
                except json.JSONDecodeError:
                    refs = []
                    err(f"review_{tag} {case}: evidence_refs_json is not valid JSON")
                if not refs:
                    err(f"review_{tag} {case}: evidence references are required")
                text = r["rationale"] + " " + r["evidence_refs_json"]
                review_text[f"{tag}:{case}"] = text
                if re.search(r"openalex\.org/(?:authors/)?A\d+", text, re.IGNORECASE):
                    err(f"review_{tag} {case}: evidence refers to an OpenAlex author profile; Stage A must not use candidate results")
                if FORBIDDEN_REVIEW_TEXT.search(text):
                    err(f"review_{tag} {case}: submission mentions HAMMER output (rank, score or decision)")
                ts = parse_ts(r["submitted_at"], f"review_{tag} {case} submitted_at")
                first_review_ts = ts if first_review_ts is None or ts < first_review_ts else first_review_ts
                last_review_ts = ts if last_review_ts is None or ts > last_review_ts else last_review_ts
                reg_gold = {x["doi"] for x in register.get(case, []) if x["purpose"] in ("gold_evidence", "both")}
                for d in json.loads(r["gold_dois_json"] or "[]"):
                    if normalize_doi(d) not in reg_gold:
                        err(f"review_{tag} {case}: gold DOI {d} is not registered as gold_evidence or both")
            reviews[tag] = by_case
        if reviewer_ids["a"] and reviewer_ids["a"] == reviewer_ids["b"]:
            err("Stage A: Reviewer A and Reviewer B must have two distinct reviewer IDs")
        rows = read_csv(pilot_dir / "stage_a.csv", {"case_id", "final_status", "gold_person_id", "adjudication_status", "adjudicator_id", "rationale"})
        labels = {r["case_id"].strip(): r for r in rows}
        if len(labels) != len(rows):
            err("Stage A: duplicate case rows")
        pids: dict[str, list[str]] = {}
        for case in ids:
            if case not in labels:
                err(f"Stage A: missing final label for {case}")
        for case, r in labels.items():
            final = r["final_status"].strip()
            if final not in STATUSES:
                err(f"Stage A {case}: invalid final_status")
            gp = r["gold_person_id"].strip()
            if final == "resolved":
                if not gp:
                    err(f"Stage A {case}: resolved needs an opaque gold_person_id")
                pids.setdefault(gp, []).append(case)
            elif gp:
                err(f"Stage A {case}: only resolved cases carry a gold_person_id")
            if gp and (OPENALEX_ID.match(gp) or "openalex" in gp.casefold()):
                err(f"Stage A {case}: gold_person_id must be an opaque person ID, not an OpenAlex identifier")
            sa = reviews.get("a", {}).get(case, {}).get("status", "").strip()
            sb = reviews.get("b", {}).get(case, {}).get("status", "").strip()
            adj = r["adjudication_status"].strip()
            if sa and sb and sa == sb:
                if final != sa or adj != "agreed":
                    err(f"Stage A {case}: reviewers agree on '{sa}' but the final record says '{final}' / '{adj}'")
            elif sa and sb:
                if adj not in ("adjudicated", "uncertain"):
                    err(f"Stage A {case}: reviewers disagree; adjudication_status must be 'adjudicated' or 'uncertain'")
                adjudicator = r["adjudicator_id"].strip()
                if not adjudicator or adjudicator in (reviewer_ids.get("a"), reviewer_ids.get("b")):
                    err(f"Stage A {case}: an adjudicator distinct from both reviewers is required for a disagreement")
                if adj == "uncertain" and final != "uncertain":
                    err(f"Stage A {case}: adjudication_status 'uncertain' requires final_status 'uncertain'")
        for gp, cases in pids.items():
            if len(cases) > 1:
                err(f"Stage A: gold_person_id {gp} is assigned to several cases {cases}; one underlying person per case")
        counts = {k: sum(1 for r in labels.values() if r["final_status"].strip() == k) for k in STATUSES}
        rep.info["final_composition"] = counts
        if counts["resolved"] != 10 or counts["unresolved"] != 5:
            rep.info["composition_note"] = "final labels differ from the planned 10/5; uncertain cases are retained and reported"
    except PilotDataError as exc:
        err(str(exc))
    # --- captures and Stage B
    cap = pilot_dir / "captures"
    pools: dict[str, list[str]] = {}
    capture_times = None
    if cap.is_dir() and (cap / "capture_index.jsonl").is_file():
        try:
            entries = load_index(cap)
            for p in verify_capture_hashes(cap, entries):
                err(f"capture: {p}")
            if freeze.get("frozen_at"):
                frozen = parse_ts(freeze["frozen_at"])
                for e in entries:
                    if parse_ts(e["captured_at"]) < frozen:
                        err(f"capture seq {e['seq']} predates the seed freeze")
            times = sorted(parse_ts(e["captured_at"]) for e in entries)
            if times and first_review_ts is not None and last_review_ts > times[0]:
                err("timestamps: a Stage A review was submitted after candidate capture began; identity truth must precede candidate generation")
            capture_times = (times[0], times[-1]) if times else None
            for case in ids:
                path = cap / "cases" / f"{case}.json"
                if not path.is_file():
                    err(f"capture: no case summary for {case}")
                    continue
                summary = json.loads(path.read_text(encoding="utf-8"))
                pools[case] = sorted(set(summary["R0"]["candidate_ids"]) | set(summary["r2_pool_candidate_ids"]))
        except (PilotDataError, OSError, KeyError, ValueError) as exc:
            err(f"capture: {exc}")
        for key, text in review_text.items():
            case = key.split(":", 1)[1]
            for cid in pools.get(case, []):
                if re.search(rf"\b{re.escape(cid)}\b", text):
                    err(f"review {key}: reviewer text contains a captured candidate ID ({cid}); Stage A must be blind to candidates")
        stage_b_path = pilot_dir / "stage_b.csv"
        if not stage_b_path.is_file():
            warn("Stage B file not present yet")
        else:
            try:
                with open(stage_b_path, encoding="utf-8") as stream:
                    header = set(stream.readline().strip().split(","))
                if header & FORBIDDEN_STAGE_B_COLUMNS:
                    err(f"Stage B must be blind to rank/score/decision; forbidden columns present: {sorted(header & FORBIDDEN_STAGE_B_COLUMNS)}")
                rows = read_csv(stage_b_path, {"case_id", "candidate_author_id", "reviewer_a_judgment", "reviewer_b_judgment", "final_judgment", "adjudication_status", "submitted_at"})
                judged: dict[str, dict[str, str]] = {}
                for r in rows:
                    case, cid = r["case_id"].strip(), r["candidate_author_id"].strip()
                    if r["final_judgment"].strip() not in JUDGMENTS or r["reviewer_a_judgment"].strip() not in JUDGMENTS or r["reviewer_b_judgment"].strip() not in JUDGMENTS:
                        err(f"Stage B {case}/{cid}: invalid judgment")
                    if cid not in pools.get(case, []):
                        err(f"Stage B {case}/{cid}: candidate is not in the captured pools")
                    judged.setdefault(case, {})[cid] = r["final_judgment"].strip()
                    if capture_times and parse_ts(r["submitted_at"], f"Stage B {case}/{cid} submitted_at") < capture_times[1]:
                        err(f"timestamps: Stage B {case}/{cid} was submitted before the last candidate capture")
                    status = labels.get(case, {}).get("final_status", "").strip()
                    if r["final_judgment"].strip() == "same" and status != "resolved":
                        err(f"Stage B {case}/{cid}: 'same' on a case that is not resolved")
                for case, pool in pools.items():
                    if labels.get(case, {}).get("final_status", "").strip() == "resolved":
                        missing = [c for c in pool if c not in judged.get(case, {})]
                        if missing:
                            err(f"Stage B incomplete for {case}: {len(missing)} captured candidate(s) not judged")
            except PilotDataError as exc:
                err(str(exc))
    else:
        rep.info["captures"] = "not present yet"
    # --- development leakage
    excl_path = pilot_dir / "development_exclusions.csv"
    if excl_path.is_file():
        try:
            excl = read_csv(excl_path, {"kind", "value"})
            by_kind: dict[str, set[str]] = {}
            for r in excl:
                by_kind.setdefault(r["kind"].strip(), set()).add(_norm(r["value"]))
            for s in seeds:
                if _norm(s["query_text"]) in by_kind.get("name", set()) or _norm(s["identity_group_id"]) in by_kind.get("identity_group", set()):
                    err(f"development leakage: {s['case_id']} matches a development-set identity")
            for r in reg_rows:
                if _norm(r["doi"]) in by_kind.get("doi", set()):
                    err(f"development leakage: DOI {r['doi']} ({r['case_id']}) is in the development exclusions")
        except PilotDataError as exc:
            err(str(exc))
    else:
        err("development_exclusions.csv is mandatory for a pilot-ready dataset (list development-set names, identity groups and DOIs; an empty list needs a header row)")
    # --- prediction labels
    if predictions_csv:
        try:
            for r in read_csv(Path(predictions_csv), {"case_id", "condition", "policy", "outcome"}):
                if r["condition"] not in CONDITIONS or r["policy"] not in POLICIES or r["outcome"] not in OUTCOMES:
                    err(f"predictions: inconsistent label in {r['case_id']} ({r['condition']}/{r['policy']}/{r['outcome']})")
        except PilotDataError as exc:
            err(str(exc))
    return rep
