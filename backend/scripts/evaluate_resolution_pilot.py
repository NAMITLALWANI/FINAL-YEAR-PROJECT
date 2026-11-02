"""Replay V1 against persisted manual choices as a small exploratory pilot.

This is not a held-out benchmark: the labels are reviewer selections from the
same application history and require independent confirmation for research use.
Run from backend/: ../.venv/bin/python scripts/evaluate_resolution_pilot.py
"""
import asyncio
import json
import sys
import platform
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select

from database import AsyncSessionLocal, AuthorCandidate, AuthorResolution, engine
from config import (
    AUTHOR_AUTO_DOMINANCE_THRESHOLD, AUTHOR_AUTO_MARGIN_THRESHOLD,
    AUTHOR_AUTO_SCORE_THRESHOLD, AUTHOR_MANUAL_SCORE_THRESHOLD,
    AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO, AUTHOR_RESOLVER_VERSION,
    AUTHOR_SCORING_VERSION, AUTHOR_SCORE_WEIGHTS, AUTHOR_THRESHOLD_VERSION,
)
from services.author_candidates import OpenAlexCandidate
from services.author_resolution import decide, rank_candidates


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


async def main() -> None:
    predictions = []
    async with AsyncSessionLocal() as db:
        labeled = (await db.execute(
            select(AuthorResolution).where(
                AuthorResolution.status == "manual_selected",
                AuthorResolution.selected_candidate_id.is_not(None),
            ).order_by(AuthorResolution.created_at, AuthorResolution.id)
        )).scalars().all()
        for resolution in labeled:
            rows = (await db.execute(
                select(AuthorCandidate).where(AuthorCandidate.query_normalized == resolution.query_normalized)
            )).scalars().all()
            candidates = [OpenAlexCandidate.from_persisted(row) for row in rows]
            ranked = rank_candidates(candidates, {"institution_hints": [resolution.institution_hint]} if resolution.institution_hint else None)
            status, top, second, margin, dominance, reason = decide(ranked)
            predicted_id = ranked[0].candidate.source_author_id if ranked else None
            label_row = await db.get(AuthorCandidate, resolution.selected_candidate_id)
            label_id = label_row.source_author_id if label_row else None
            predictions.append({
                "resolution_id": resolution.id,
                "query": resolution.query_original,
                "label_source": "persisted_manual_selection_not_independently_revalidated",
                "gold_selected_source_id": label_id,
                "top_ranked_source_id": predicted_id,
                "rank_correct": predicted_id == label_id,
                "replayed_status": status,
                "replayed_automatic_correct": predicted_id == label_id if status == "auto_selected" else None,
                "top_score": top,
                "second_score": second,
                "score_margin": margin,
                "decision_reason": reason,
                "candidate_count": len(ranked),
            })
    n = len(predictions)
    auto = [p for p in predictions if p["replayed_status"] == "auto_selected"]
    correct_auto = sum(bool(p["replayed_automatic_correct"]) for p in auto)
    metrics = {
        "dataset_version": "persisted-manual-choice-pilot-v1",
        "n_manual_selected_resolution_episodes": n,
        "candidate_top1_accuracy": _ratio(sum(p["rank_correct"] for p in predictions), n),
        "automatic_coverage_on_pilot": _ratio(len(auto), n),
        "automatic_accuracy_on_pilot": _ratio(correct_auto, len(auto)),
        "false_merge_rate_on_pilot": _ratio(len(auto) - correct_auto, len(auto)),
        "manual_review_rate_on_pilot": _ratio(sum(p["replayed_status"] == "manual_selection_required" for p in predictions), n),
        "unresolved_rate_on_pilot": _ratio(sum(p["replayed_status"] == "unresolved" for p in predictions), n),
        "interpretation": "Exploratory resubstitution-style replay only. Manual selections are not independently verified labels; repeated queries may occur. Do not use these values as held-out or publication-level performance claims.",
    }
    configuration = {
        "python_version": platform.python_version(),
        "resolver_version": AUTHOR_RESOLVER_VERSION,
        "scoring_version": AUTHOR_SCORING_VERSION,
        "threshold_version": AUTHOR_THRESHOLD_VERSION,
        "weights": AUTHOR_SCORE_WEIGHTS,
        "automatic_score_threshold": AUTHOR_AUTO_SCORE_THRESHOLD,
        "automatic_margin_threshold": AUTHOR_AUTO_MARGIN_THRESHOLD,
        "automatic_dominance_threshold": AUTHOR_AUTO_DOMINANCE_THRESHOLD,
        "manual_review_threshold": AUTHOR_MANUAL_SCORE_THRESHOLD,
        "minimum_available_signals_for_auto": AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO,
    }
    artifact = {"metrics": metrics, "configuration": configuration, "predictions": predictions}
    output = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "pilot_predictions.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(metrics, indent=2))
    print(f"Saved {n} row-level predictions to {output}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())