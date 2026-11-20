"""Two-stage review records, validation, agreement statistics and conversion of adjudicated labels into C7 case fields (Decision B5, B6, B7; Decision A label states).

Offline and pure. Records are plain dictionaries (CSV-friendly). Reviewer rows are never overwritten by an adjudicated label. The module recruits nobody and assumes no
reviewer count or hours: the reviewer-time helper takes the available hours as an explicit argument.

Record kinds
  Stage A  one row per reviewer per case: status, group purity, confidence 1-5, rationale, evidence references, searches, ORCID-encountered flag, minutes
  Stage B  one row per reviewer per case per candidate: same / different / cannot_tell, confidence, evidence references, ORCID-encountered flag, minutes
  Final    one row per case: adjudicator, final status and purity, final candidate judgments, rationale. Required only where the two reviewers disagree
           (otherwise the agreed values are the final label and the source is recorded as "agreement").
"""
from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

STATUSES = ("resolved", "unresolved", "uncertain", "unverifiable")
PURITY = ("pure", "impure", "unresolved")
JUDGMENTS = ("same", "different", "cannot_tell")
STAGE_A_FIELDS = ["case_id", "reviewer_id", "status", "group_purity", "confidence", "rationale", "evidence_refs", "searches", "orcid_encountered", "minutes"]
STAGE_B_FIELDS = ["case_id", "reviewer_id", "candidate", "judgment", "confidence", "evidence_refs", "orcid_encountered", "minutes"]
FINAL_FIELDS = ["case_id", "adjudicator_id", "final_status", "final_group_purity", "candidate_judgments", "rationale"]


class ReviewError(ValueError):
    """Invalid review record or an invalid review set."""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if str(value).strip().lower() in ("true", "1", "yes"):
        return True
    if str(value).strip().lower() in ("false", "0", "no"):
        return False
    raise ReviewError(f"not a boolean: {value!r}")


def _num(name: str, value: Any, lo: float, hi: float | None = None) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise ReviewError(f"{name} is not a number: {value!r}") from None
    if not math.isfinite(x) or x < lo or (hi is not None and x > hi):
        raise ReviewError(f"{name} out of range: {value!r}")
    return x


def validate_stage_a(row: Mapping[str, Any]) -> dict[str, Any]:
    if row.get("status") not in STATUSES:
        raise ReviewError(f"Stage A status must be one of {STATUSES}, got {row.get('status')!r}")
    if row.get("group_purity") not in PURITY:
        raise ReviewError(f"group purity must be one of {PURITY}, got {row.get('group_purity')!r}")
    if not row.get("case_id") or not row.get("reviewer_id"):
        raise ReviewError("case_id and reviewer_id are required")
    return {**row, "confidence": int(_num("confidence", row.get("confidence"), 1, 5)), "orcid_encountered": _bool(row.get("orcid_encountered")),
            "minutes": _num("minutes", row.get("minutes"), 0)}


def validate_stage_b(row: Mapping[str, Any]) -> dict[str, Any]:
    if row.get("judgment") not in JUDGMENTS:
        raise ReviewError(f"Stage B judgment must be one of {JUDGMENTS}, got {row.get('judgment')!r}")
    if not row.get("case_id") or not row.get("reviewer_id") or not row.get("candidate"):
        raise ReviewError("case_id, reviewer_id and candidate are required")
    return {**row, "confidence": int(_num("confidence", row.get("confidence"), 1, 5)), "orcid_encountered": _bool(row.get("orcid_encountered")),
            "minutes": _num("minutes", row.get("minutes"), 0)}


def parse_judgments(text: str) -> dict[str, str]:
    """'K-1:same;K-2:different' to a mapping."""
    out = {}
    for part in filter(None, (p.strip() for p in str(text).split(";"))):
        cand, _, j = part.partition(":")
        if j not in JUDGMENTS or not cand:
            raise ReviewError(f"bad candidate judgment {part!r}")
        out[cand] = j
    return out


# --------------------------------------------------------------------------- one case
def resolve_case(case_id: str, stage_a: Sequence[Mapping[str, Any]], stage_b: Sequence[Mapping[str, Any]], final: Mapping[str, Any] | None, *,
                 candidates: Sequence[str], builder_id: str) -> dict[str, Any]:
    """Validate one case's review set and return its final label. Raises ReviewError listing every problem found.

    Requirements: two distinct reviewers; each has a Stage A row; if candidates exist, each reviewer judged every candidate (Stage B completeness); the adjudicator is
    neither a reviewer nor the packet builder; an adjudication row exists wherever the reviewers disagree."""
    problems: list[str] = []
    a = [validate_stage_a(r) for r in stage_a if r["case_id"] == case_id]
    b = [validate_stage_b(r) for r in stage_b if r["case_id"] == case_id]
    reviewers = sorted({r["reviewer_id"] for r in a})
    if len(reviewers) != 2 or len(a) != 2:
        problems.append(f"Stage A needs exactly two distinct reviewers, found {len(a)} rows from {len(reviewers)} reviewer(s)")
    if builder_id in reviewers:
        problems.append("the packet builder is a reviewer")
    cand_set = set(candidates)
    for r in reviewers:
        judged = [x["candidate"] for x in b if x["reviewer_id"] == r]
        if len(judged) != len(set(judged)):
            problems.append(f"reviewer {r} judged a candidate more than once")
        if set(judged) - cand_set:
            problems.append(f"reviewer {r} judged candidates that are not in the packet")
        if cand_set and set(judged) != cand_set:
            problems.append(f"reviewer {r} did not judge every candidate ({len(cand_set - set(judged))} missing)")
    if problems:
        raise ReviewError("; ".join(problems))
    ra, rb = a
    by = {(x["reviewer_id"], x["candidate"]): x["judgment"] for x in b}
    disagree = ra["status"] != rb["status"] or ra["group_purity"] != rb["group_purity"] or any(by.get((reviewers[0], c)) != by.get((reviewers[1], c)) for c in cand_set)
    if disagree:
        if final is None:
            raise ReviewError("the reviewers disagree and no adjudication row exists")
        if final["adjudicator_id"] in reviewers or final["adjudicator_id"] == builder_id or not final.get("adjudicator_id"):
            raise ReviewError("the adjudicator must be a third person who is neither a reviewer nor the packet builder")
        if final["final_status"] not in STATUSES or final["final_group_purity"] not in PURITY:
            raise ReviewError("final status or purity invalid")
        judgments = parse_judgments(final["candidate_judgments"]) if isinstance(final["candidate_judgments"], str) else dict(final["candidate_judgments"])
        if set(judgments) - cand_set or (cand_set and set(judgments) != cand_set and final["final_status"] == "resolved"):
            raise ReviewError("a resolved adjudication must judge every candidate in the packet, and only those")
        return {"case_id": case_id, "status": final["final_status"], "group_purity": final["final_group_purity"], "candidate_judgments": judgments, "source": "adjudication",
                "adjudicator_id": final["adjudicator_id"], "reviewers": reviewers}
    return {"case_id": case_id, "status": ra["status"], "group_purity": ra["group_purity"], "candidate_judgments": {c: by[(reviewers[0], c)] for c in cand_set}, "source": "agreement",
            "adjudicator_id": None, "reviewers": reviewers}


def to_c7_fields(final_label: Mapping[str, Any], crosswalk: Mapping[str, str], *, audit_subset: str, selected_candidate: str | None = None) -> dict[str, Any]:
    """Keyword arguments for `metrics_c7.Case`: label state, group purity, per-candidate judgments keyed by provider candidate id, and the audit subset.
    The crosswalk (opaque to provider id) is applied here and nowhere reviewers can see."""
    judgments = {crosswalk[c]: j for c, j in final_label["candidate_judgments"].items()}
    fields: dict[str, Any] = {"label_state": final_label["status"], "group_purity": final_label["group_purity"], "audit_subset": audit_subset,
                              "pool_judgments": judgments or None}
    if selected_candidate is not None and judgments and selected_candidate in judgments:
        fields["selected_judgment"] = judgments[selected_candidate]
    return fields


# --------------------------------------------------------------------------- agreement and effort
def cohens_kappa(pairs: Sequence[tuple[str, str]]) -> dict[str, Any]:
    """Raw agreement and Cohen's kappa for two raters. Counts are always reported. kappa is None when chance agreement is 1."""
    n = len(pairs)
    if n == 0:
        return {"n": 0, "raw_agreement": None, "kappa": None, "note": "no pairs"}
    cats = sorted({x for p in pairs for x in p})
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    kappa = None if math.isclose(pe, 1.0) else (po - pe) / (1 - pe)
    return {"n": n, "agreements": sum(1 for a, b in pairs if a == b), "raw_agreement": po, "chance_agreement": pe, "kappa": kappa,
            "categories": {c: {"rater1": ca[c], "rater2": cb[c]} for c in cats},
            "note": "kappa is unstable at small n and when one category dominates; read it with the counts" + ("; undefined here (chance agreement is 1)" if kappa is None else "")}


def agreement_report(stage_a: Sequence[Mapping[str, Any]], stage_b: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Agreement between the two reviewers over all cases: Stage A status, Stage A purity and Stage B judgments."""
    def pairs(rows: Sequence[Mapping[str, Any]], unit: tuple[str, ...], field: str) -> list[tuple[str, str]]:
        grouped: dict[tuple, dict[str, str]] = {}
        for r in rows:
            grouped.setdefault(tuple(r[u] for u in unit), {})[r["reviewer_id"]] = r[field]
        return [tuple(v[k] for k in sorted(v)) for v in grouped.values() if len(v) == 2]
    return {"stage_a_status": cohens_kappa(pairs(stage_a, ("case_id",), "status")), "stage_a_purity": cohens_kappa(pairs(stage_a, ("case_id",), "group_purity")),
            "stage_b_judgment": cohens_kappa(pairs(stage_b, ("case_id", "candidate"), "judgment"))}


def orcid_encounter_summary(stage_a: Sequence[Mapping[str, Any]], stage_b: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    cases = {r["case_id"] for r in list(stage_a) + list(stage_b) if _bool(r["orcid_encountered"])}
    total = {r["case_id"] for r in list(stage_a) + list(stage_b)}
    return {"cases_with_an_orcid_encounter": len(cases), "cases": len(total), "case_ids": sorted(cases),
            "note": "results are reported separately for these cases; reviewers were told not to use an ORCID as evidence"}


def reviewer_time_summary(stage_a: Sequence[Mapping[str, Any]], stage_b: Sequence[Mapping[str, Any]], *, hours_available: float) -> dict[str, Any]:
    """B7: measured minutes per Stage A case (t_A) and per candidate (t_B), mean candidates per case, and the affordable number of cases per reviewer
    N = floor(60 H / (t_A + k t_B)) for an explicitly supplied number of hours H. Adjudication time and the automatic-verification load are not subtracted."""
    h = _num("hours_available", hours_available, 0)
    ta = [float(r["minutes"]) for r in stage_a]
    tb = [float(r["minutes"]) for r in stage_b]
    cases = {r["case_id"] for r in stage_a}
    if not ta:
        raise ReviewError("no Stage A rows")
    per_case_cands = Counter((r["case_id"], r["reviewer_id"]) for r in stage_b)
    k = (sum(per_case_cands.values()) / len(per_case_cands)) if per_case_cands else 0.0
    t_a = sum(ta) / len(ta)
    t_b = (sum(tb) / len(tb)) if tb else 0.0
    return {"cases": len(cases), "t_A_minutes_mean": t_a, "t_B_minutes_mean": t_b, "mean_candidates_per_case": k, "hours_available": h,
            "affordable_cases_per_reviewer": math.floor(60 * h / (t_a + k * t_b)) if (t_a + k * t_b) > 0 else None,
            "note": "per reviewer; less adjudication time and the verification of automatic assignments"}


# --------------------------------------------------------------------------- CSV
def write_templates(directory: Path) -> list[str]:
    """Empty CSV templates with the exact headers (no data rows, no dossier content). New files only."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    names = {"stage_a_reviews.csv": STAGE_A_FIELDS, "stage_b_reviews.csv": STAGE_B_FIELDS, "final_labels.csv": FINAL_FIELDS}
    for name, fields in names.items():
        with open(directory / name, "x", newline="", encoding="utf-8") as f:
            csv.writer(f, lineterminator="\n").writerow(fields)
    return sorted(names)


def read_csv(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != list(fields):
            raise ReviewError(f"{Path(path).name}: header must be exactly {list(fields)}, got {reader.fieldnames}")
        return list(reader)


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    with open(path, "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
