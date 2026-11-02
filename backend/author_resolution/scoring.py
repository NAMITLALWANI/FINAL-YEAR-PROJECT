"""Architectural Role: Candidate Scoring Component of Author Entity Resolution.

This module computes transparent, normalized weighted evidence scores for candidate author profiles.
It strictly performs feature combination and mathematical weighting; it does NOT make identity decisions.

The Five Evidence Signals & Their Configured Weights:
1. Name Similarity (w1 = 0.35): Jaro-Winkler string similarity between query and candidate display name/aliases.
2. Institutional Compatibility (w2 = 0.25): Jaccard token overlap between candidate affiliations and query institution.
3. Publication Corpus Overlap (w3 = 0.20): Token and DOI overlap between candidate works and query context.
4. Coauthor Network Overlap (w4 = 0.10): Shared coauthor count between candidate graph and query context.
5. Temporal Compatibility (w5 = 0.10): Gaussian decay penalty over publication year divergence.

Missing signals are dynamically re-normalized over the available evidence dimensions.
"""
from __future__ import annotations

from dataclasses import dataclass
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
    return CandidateScore(round(sum(contributions.values()), 6), len(available), contributions)
