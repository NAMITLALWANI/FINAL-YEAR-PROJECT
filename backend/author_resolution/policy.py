"""Decision policy for author resolution (pure; no I/O).

The approved numeric gates are unchanged and read from config: automatic score 0.75,
margin 0.15, dominance 1.35, manual score 0.45, minimum available signals 2. Candidate
ranking (by heuristic score) is not changed here either.

On top of those gates this module adds *evidence-sufficiency safeguards* that only ever
withhold automatic assignment (route it to manual review). None introduces a number:

  S1 unscored competitor      a multi-candidate pool containing a candidate with no score
  S2 no corroboration         no observed, non-zero institution / publication / coauthor signal
  S3 hard conflict            an observed signal with score exactly 0.0 on the top candidate
  S4 incomparable evidence    a competitor was scored on a different signal set than the top candidate
  S5 incomplete evidence      an enrichment retrieval failed, or a candidate payload could not be parsed

Each is a separately reviewable policy decision (see FIVE_SIGNAL_DATA_SOURCE_FEASIBILITY.md section 14).
A high heuristic score is not a probability and never overrides these safeguards.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from config import (
    AUTHOR_AUTO_DOMINANCE_THRESHOLD, AUTHOR_AUTO_MARGIN_THRESHOLD, AUTHOR_AUTO_SCORE_THRESHOLD,
    AUTHOR_MANUAL_SCORE_THRESHOLD, AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO,
)
from author_resolution.evidence import IDENTITY_BEARING, RETRIEVAL_FAILED

AUTO_RESOLVED = "auto_selected"
MANUAL_REVIEW = "manual_selection_required"
UNRESOLVED = "unresolved"

S1_UNSCORED_COMPETITOR = "unscored_competitor"
S2_NO_CORROBORATION = "no_identity_corroboration"
S3_HARD_CONFLICT = "observed_zero_signal"
S4_INCOMPARABLE = "incomparable_evidence_sets"
S5_INCOMPLETE = "incomplete_evidence"

_BLOCKER_TEXT = {
    S1_UNSCORED_COMPETITOR: "a competing candidate has no usable evidence score",
    S2_NO_CORROBORATION: "no observed non-zero institution, publication or coauthor evidence supports the top candidate",
    S3_HARD_CONFLICT: "the top candidate has an observed signal with zero support",
    S4_INCOMPARABLE: "candidates were scored on different evidence sets",
    S5_INCOMPLETE: "some evidence retrieval failed or a candidate could not be read",
}


@dataclass(frozen=True)
class DecisionOutcome:
    status: str
    top_score: float | None
    second_score: float | None
    margin: float | None
    dominance: float | None
    reason: str
    threshold_gates_passed: bool = False
    auto_blockers: tuple[str, ...] = ()
    signal_sets: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def as_tuple(self) -> tuple[str, float | None, float | None, float | None, float | None, str]:
        return self.status, self.top_score, self.second_score, self.margin, self.dominance, self.reason

    def assessment(self) -> dict[str, Any]:
        return {
            "status": self.status, "reason": self.reason, "threshold_gates_passed": self.threshold_gates_passed,
            "auto_blockers": list(self.auto_blockers),
            "signal_sets": {cid: list(signals) for cid, signals in self.signal_sets},
        }


def describe_evidence(item: Any) -> str:
    used = list(item.score.signal_set)
    missing = [f"{e.signal_name} ({e.status})" for e in item.evidence if e.normalized_score is None]
    text = "Evidence used: " + (", ".join(used) if used else "none")
    return text + ("; not available: " + ", ".join(missing) if missing else "") + "."


def evaluate_decision(ranked: Sequence[Any], *, incomplete_pool: bool = False) -> DecisionOutcome:
    """Apply the approved gates, then the evidence-sufficiency safeguards. ``ranked`` is score-ordered."""
    if not ranked or ranked[0].score.score is None:
        return DecisionOutcome(UNRESOLVED, None, None, None, None, "Insufficient comparable evidence.")
    top_item = ranked[0]
    top = top_item.score.score
    competitors = list(ranked[1:])
    scored = [c for c in competitors if c.score.score is not None]
    second = scored[0].score.score if scored else None
    margin = top - second if second is not None else top
    dominance = (top / second) if second and second > 0 else None
    single = len(ranked) == 1
    sets = tuple((r.candidate.source_author_id, tuple(r.score.signal_set)) for r in ranked)

    if single:
        competition_ok = True
    else:
        # With competitors, margin/dominance must be computable: an unscored competitor fails closed.
        competition_ok = second is not None and margin >= AUTHOR_AUTO_MARGIN_THRESHOLD and (
            dominance is None or dominance >= AUTHOR_AUTO_DOMINANCE_THRESHOLD)
    gates = (top >= AUTHOR_AUTO_SCORE_THRESHOLD
             and top_item.score.available_signals >= AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO
             and competition_ok)

    blockers: list[str] = []
    if len(competitors) != len(scored):
        blockers.append(S1_UNSCORED_COMPETITOR)
    observed = {e.signal_name: e.normalized_score for e in top_item.evidence if e.normalized_score is not None}
    if not any(observed.get(name, 0.0) > 0.0 for name in IDENTITY_BEARING):
        blockers.append(S2_NO_CORROBORATION)
    if any(score == 0.0 for score in observed.values()):
        blockers.append(S3_HARD_CONFLICT)
    if any(tuple(c.score.signal_set) != tuple(top_item.score.signal_set) for c in scored):
        blockers.append(S4_INCOMPARABLE)
    if incomplete_pool or any(e.status == RETRIEVAL_FAILED for r in ranked for e in r.evidence):
        blockers.append(S5_INCOMPLETE)

    evidence_text = describe_evidence(top_item)
    if gates and not blockers:
        return DecisionOutcome(
            AUTO_RESOLVED, top, second, margin, dominance,
            "Conservative configurable engineering heuristics were met; review remains possible. " + evidence_text,
            True, (), sets)
    if top >= AUTHOR_MANUAL_SCORE_THRESHOLD:
        if gates and blockers:
            why = "Automatic assignment withheld: " + "; ".join(_BLOCKER_TEXT[b] for b in blockers) + "."
        else:
            why = "Candidate evidence is plausible but not sufficiently separated for automatic resolution."
        return DecisionOutcome(MANUAL_REVIEW, top, second, margin, dominance, why + " " + evidence_text, gates, tuple(blockers), sets)
    return DecisionOutcome(UNRESOLVED, top, second, margin, dominance,
                           "No candidate has sufficient available evidence. " + evidence_text, gates, tuple(blockers), sets)
