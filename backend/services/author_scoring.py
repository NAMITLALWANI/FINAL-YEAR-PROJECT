"""Transparent weighted scoring; this module makes no identity decision."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from config import AUTHOR_SCORE_WEIGHTS, AUTHOR_SCORING_VERSION
from services.author_evidence import Evidence


@dataclass(frozen=True)
class CandidateScore:
    score: float | None
    available_signals: int
    contributions: dict[str, float]
    scoring_version: str = AUTHOR_SCORING_VERSION


def score_evidence(evidence: Iterable[Evidence], weights: dict[str, float] | None = None) -> CandidateScore:
    configured = weights or AUTHOR_SCORE_WEIGHTS
    available = [item for item in evidence if item.normalized_score is not None and item.signal_name in configured]
    total_weight = sum(configured[item.signal_name] for item in available)
    if not available or total_weight <= 0:
        return CandidateScore(None, 0, {})
    contributions = {item.signal_name: (configured[item.signal_name] * item.normalized_score) / total_weight for item in available}
    return CandidateScore(round(sum(contributions.values()), 6), len(available), contributions)