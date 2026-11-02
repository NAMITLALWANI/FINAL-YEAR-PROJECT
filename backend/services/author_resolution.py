"""Deterministic V1 author-resolution orchestration and audit persistence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import (
    AUTHOR_AUTO_DOMINANCE_THRESHOLD, AUTHOR_AUTO_MARGIN_THRESHOLD, AUTHOR_AUTO_SCORE_THRESHOLD,
    AUTHOR_MANUAL_SCORE_THRESHOLD, AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO,
    AUTHOR_RESOLVER_VERSION, AUTHOR_SCORING_VERSION, AUTHOR_THRESHOLD_VERSION,
)
from database import Author, AuthorExternalId, AuthorCandidate, AuthorResolution, AuthorResolutionEvidence
from services.author_candidates import AuthorCandidateInput, OpenAlexCandidate, OpenAlexCandidateService
from services.author_evidence import Evidence, extract_evidence
from services.author_scoring import CandidateScore, score_evidence


AUTO_RESOLVED = "auto_selected"
MANUAL_REVIEW = "manual_selection_required"
UNRESOLVED = "unresolved"
MANUAL_SELECTED = "manual_selected"


class CandidateSourceUnavailable(RuntimeError):
    """Candidate retrieval failed; this is not an unresolved identity decision."""


@dataclass(frozen=True)
class RankedCandidate:
    candidate: OpenAlexCandidate
    evidence: list[Evidence]
    score: CandidateScore


def rank_candidates(candidates: list[OpenAlexCandidate], context: dict[str, Any] | None = None) -> list[RankedCandidate]:
    ranked = [RankedCandidate(candidate, extract_evidence(candidate, context), score_evidence(extract_evidence(candidate, context))) for candidate in candidates]
    # deterministic display ordering only; it is not an identity assertion.
    return sorted(ranked, key=lambda item: (item.score.score is not None, item.score.score or -1.0, item.candidate.source_author_id), reverse=True)


def decide(ranked: list[RankedCandidate]) -> tuple[str, float | None, float | None, float | None, float | None, str]:
    if not ranked or ranked[0].score.score is None:
        return UNRESOLVED, None, None, None, None, "Insufficient comparable evidence."
    top = ranked[0].score.score
    second = ranked[1].score.score if len(ranked) > 1 else None
    margin = top - second if second is not None else top
    dominance = (top / second) if second and second > 0 else None
    strong = (top >= AUTHOR_AUTO_SCORE_THRESHOLD and ranked[0].score.available_signals >= AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO and (second is None or (margin >= AUTHOR_AUTO_MARGIN_THRESHOLD and (dominance is None or dominance >= AUTHOR_AUTO_DOMINANCE_THRESHOLD))))
    if strong:
        return AUTO_RESOLVED, top, second, margin, dominance, "Conservative configurable engineering heuristics were met; review remains possible."
    if top >= AUTHOR_MANUAL_SCORE_THRESHOLD:
        return MANUAL_REVIEW, top, second, margin, dominance, "Candidate evidence is plausible but not sufficiently separated for automatic resolution."
    return UNRESOLVED, top, second, margin, dominance, "No candidate has sufficient available evidence."


class AuthorResolutionService:
    def __init__(self, candidate_service: OpenAlexCandidateService | None = None):
        self.candidate_service = candidate_service or OpenAlexCandidateService()

    async def generate_and_rank(self, author_name: str, institution_hint: str | None, context: dict[str, Any] | None, db: AsyncSession) -> tuple[list[AuthorCandidate], list[RankedCandidate], str]:
        request_context = dict(context or {})
        if institution_hint:
            request_context.setdefault("institution_hints", [institution_hint])
        result = await self.candidate_service.generate(
            AuthorCandidateInput(author_name, institution_hint, request_context)
        )
        if result.status == "failed":
            return [], [], result.error_code or "candidate_source_failed"
        rows = await self.candidate_service.persist_candidates(result, db)
        await db.commit()
        return rows, rank_candidates(result.candidates, request_context), result.status

    async def create_resolution(
        self,
        author_name: str,
        institution_hint: str | None,
        context: dict[str, Any] | None,
        db: AsyncSession,
        selected_candidate_id: str | None = None,
        mark_unresolved: bool = False,
        reason: str | None = None,
        candidate_ids: list[str] | None = None,
    ) -> AuthorResolution:
        request_context = dict(context or {})
        if institution_hint:
            request_context.setdefault("institution_hints", [institution_hint])

        if candidate_ids is not None:
            if candidate_ids:
                stmt = select(AuthorCandidate).where(AuthorCandidate.id.in_(candidate_ids))
                res = await db.execute(stmt)
                rows = list(res.scalars().all())
            else:
                rows = []
            row_by_source_id = {row.source_author_id: row for row in rows}
            candidates_list = []
            for row in rows:
                if row.raw_payload_json:
                    try:
                        payload_data = json.loads(row.raw_payload_json)
                        raw_cand = payload_data.get("payload", payload_data) if isinstance(payload_data, dict) else payload_data
                        cand = OpenAlexCandidate.from_openalex(
                            raw_cand,
                            AuthorCandidateInput(author_name),
                            row.retrieved_at,
                        )
                        if cand is not None:
                            candidates_list.append(cand)
                    except Exception:
                        pass
            ranked = rank_candidates(candidates_list, request_context) if candidates_list else []
            generation_status = "ok"
        else:
            rows, ranked, generation_status = await self.generate_and_rank(author_name, institution_hint, context, db)
            if generation_status != "ok":
                raise CandidateSourceUnavailable("Candidate source unavailable: no resolution decision was recorded")
            row_by_source_id = {row.source_author_id: row for row in rows}

        status, top, second, margin, dominance, decision_reason = decide(ranked)
        selected_row = None

        if mark_unresolved:
            status, decision_reason = UNRESOLVED, reason or "Reviewer marked this query unresolved."
            top, second, margin, dominance = None, None, None, None
        elif selected_candidate_id:
            selected_row = await db.get(AuthorCandidate, selected_candidate_id)
            if selected_row is None or selected_row.query_normalized != author_name.strip().casefold():
                raise ValueError("Selected candidate does not belong to this author query.")
            status, decision_reason = MANUAL_SELECTED, reason or "Reviewer manually selected this candidate."
        elif status == AUTO_RESOLVED and ranked:
            selected_row = row_by_source_id.get(ranked[0].candidate.source_author_id)

        resolution = AuthorResolution(
            query_original=author_name,
            query_normalized=author_name.strip().casefold(),
            institution_hint=institution_hint,
            status=status,
            selected_candidate=selected_row,
            top_score=top,
            second_score=second,
            score_margin=margin,
            dominance_ratio=dominance,
            confidence_level="engineering_heuristic" if status == AUTO_RESOLVED else None,
            decision_reason=decision_reason,
            resolver_version=AUTHOR_RESOLVER_VERSION,
            scoring_version=AUTHOR_SCORING_VERSION,
            threshold_version=AUTHOR_THRESHOLD_VERSION,
            resolved_at=datetime.now(timezone.utc).replace(tzinfo=None) if selected_row else None,
        )

        if selected_row:
            ext_stmt = select(AuthorExternalId).where(
                AuthorExternalId.source == selected_row.source,
                AuthorExternalId.external_id == selected_row.source_author_id,
            )
            existing_ext = (await db.execute(ext_stmt)).scalar_one_or_none()
            if existing_ext:
                author = await db.get(Author, existing_ext.author_id)
            else:
                author = Author(
                    display_name=selected_row.display_name,
                    normalized_name=selected_row.normalized_name,
                    resolution_state="resolved",
                )
                db.add(author)
                await db.flush()
                db.add(AuthorExternalId(
                    author_id=author.id,
                    source=selected_row.source,
                    external_id=selected_row.source_author_id,
                    provenance_json='{"identity_strength":"source_identified","note":"Source profile selected by resolution; not cross-source proof."}'
                ))
                await db.flush()
            resolution.author = author

        db.add(resolution)
        await db.flush()

        if ranked:
            for item in ranked:
                candidate_row = row_by_source_id.get(item.candidate.source_author_id)
                if not candidate_row:
                    continue
                for evidence in item.evidence:
                    values = evidence.as_db_values()
                    db.add(AuthorResolutionEvidence(
                        resolution=resolution,
                        candidate=candidate_row,
                        weight=None,
                        weighted_contribution=item.score.contributions.get(evidence.signal_name),
                        **values,
                    ))
        elif selected_row and selected_row.raw_payload_json:
            try:
                p_data = json.loads(selected_row.raw_payload_json)
                r_cand = p_data.get("payload", p_data) if isinstance(p_data, dict) else p_data
                cand = OpenAlexCandidate.from_openalex(
                    r_cand,
                    AuthorCandidateInput(author_name),
                    selected_row.retrieved_at,
                )
                ev_list = extract_evidence(cand, request_context)
                scored = score_evidence(ev_list)
                for evidence in ev_list:
                    values = evidence.as_db_values()
                    db.add(AuthorResolutionEvidence(
                        resolution=resolution,
                        candidate=selected_row,
                        weight=None,
                        weighted_contribution=scored.contributions.get(evidence.signal_name),
                        **values,
                    ))
            except Exception:
                pass

        await db.commit()
        await db.refresh(resolution)
        return resolution

    async def get_resolution(self, resolution_id: str, db: AsyncSession) -> AuthorResolution | None:
        return await db.scalar(select(AuthorResolution).where(AuthorResolution.id == resolution_id))
