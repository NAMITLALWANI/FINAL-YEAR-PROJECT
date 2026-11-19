"""Architectural Role: Candidate Scoring Component of Author Entity Resolution.

This module computes transparent, normalized weighted evidence scores for candidate author profiles.
It strictly performs feature combination and mathematical weighting; it does NOT make identity decisions.
The score is a heuristic, not a calibrated probability.

The Five Evidence Signals & Their Configured Weights (see author_resolution.evidence for the exact computations):
1. Name Similarity (w1 = 0.35): RapidFuzz token_sort_ratio between query name(s) and candidate display name/aliases.
2. Institutional Compatibility (w2 = 0.25): OpenAlex institution ID / ROR equality, else RapidFuzz token_sort_ratio of names.
3. Publication Overlap (w3 = 0.20): share of the query's supplied works (DOI / OpenAlex work ID) that list the candidate as an author.
4. Coauthor Overlap (w4 = 0.10): matched coauthors derived from the candidate's actual works' authorships.
5. Temporal Compatibility (w5 = 0.10): overlap of the supplied active-year range with the candidate's observed year range.

Missing signals are omitted and the remaining weights are re-normalized, so candidates can be scored on
different signal sets. ``signal_set`` records exactly which signals each score used; the decision policy
(resolver.py) uses it to refuse automatic assignment between incomparable candidates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from config import AUTHOR_SCORE_WEIGHTS, AUTHOR_SCORING_VERSION
from author_resolution.evidence import Evidence


@dataclass(frozen=True)
class CandidateScore:
    """Encapsulates the aggregate weighted score and individual feature contributions.
    
    Attributes:
        score: Normalized aggregate similarity in [0.0, 1.0], or None if no signals available.
        available_signals: Count of independent non-null evidence dimensions evaluated.
        contributions: Granular mapping of signal_name -> weighted contribution to final score.
        scoring_version: Version identifier tracking scoring configuration provenance.
    """
    score: float | None
    available_signals: int
    contributions: dict[str, float]
    scoring_version: str = AUTHOR_SCORING_VERSION
    signal_set: tuple[str, ...] = ()
    effective_weights: dict[str, float] = field(default_factory=dict)


def score_evidence(evidence: Iterable[Evidence], weights: dict[str, float] | None = None) -> CandidateScore:
    """Compute normalized weighted aggregate score over all available non-null evidence signals.
    
    Dynamically rescales weights so available signals sum to 1.0, ensuring fair comparison
    when candidate metadata is partially sparse.
    """
    configured = weights or AUTHOR_SCORE_WEIGHTS
    # Filter only evidence items that produced valid numerical scores
    available = [item for item in evidence if item.normalized_score is not None and item.signal_name in configured]
    total_weight = sum(configured[item.signal_name] for item in available)
    if not available or total_weight <= 0:
        return CandidateScore(None, 0, {})
    
    # Calculate fractional contribution of each signal rescaled by total available weight
    contributions = {
        item.signal_name: (configured[item.signal_name] * item.normalized_score) / total_weight 
        for item in available
    }
    effective = {item.signal_name: configured[item.signal_name] / total_weight for item in available}
    signal_set = tuple(name for name in configured if name in effective)
    return CandidateScore(round(sum(contributions.values()), 6), len(available), contributions,
                          signal_set=signal_set, effective_weights=effective)
