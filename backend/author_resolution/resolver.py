"""Architectural Role: Decision Engine of the Author Entity Resolution Subsystem.

This module orchestrates deterministic author identity resolution and decision persistence.
It bridges harvested OpenAlex candidates, multi-signal evidence extraction, weighted candidate scoring,
and safety-first non-linear decision gates.

Key Architectural Invariants:
1. Decision Gates Overrule Argmax Ranking:
   - Having the highest similarity score (rank 1) does NOT imply automatic resolution.
   - Automatic selection (auto_selected) requires clearing four simultaneous gates (policy.py):
     a) Absolute Score Gate: S1 >= 0.75
     b) Margin Separation Gate: Delta S = (S1 - S2) >= 0.15 (not applicable to a single-candidate pool)
     c) Dominance Ratio Gate: R_dom = (S1 / S2) >= 1.35 (not applicable to a single-candidate pool)
     d) Evidence Signal Sufficiency: at least 2 *available* (non-null) signals for the top candidate.
   - and, in addition, the evidence-sufficiency safeguards in policy.py (unscored competitor, corroboration,
     zero-support conflict, incomparable evidence sets, incomplete evidence), which only withhold automation.
2. Safety Through Abstention (Precision-First Posture):
   - When evidence is ambiguous, the system deliberately abstains and assigns
     'manual_selection_required' (routing candidates to the human-in-the-loop review UI)
     or 'unresolved'. Abstention prevents catastrophic author graph corruption.
3. Transactional Provenance in SQLite:
   - All resolution decisions, candidate scores, and fine-grained evidence signals are
     transactionally committed to SQLite (the system of record).
"""
from __future__ import annotations


from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config import (
    AUTHOR_AUTO_DOMINANCE_THRESHOLD, AUTHOR_AUTO_MARGIN_THRESHOLD, AUTHOR_AUTO_SCORE_THRESHOLD,
    AUTHOR_MANUAL_SCORE_THRESHOLD, AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO,
    AUTHOR_RESOLVER_VERSION, AUTHOR_SCORING_VERSION, AUTHOR_THRESHOLD_VERSION,
)
from database import Author, AuthorExternalId, AuthorCandidate, AuthorResolution, AuthorResolutionEvidence
from author_resolution.candidates import (
    AuthorCandidateInput,
    CandidateGenerationResult,
    OpenAlexCandidate,
    OpenAlexCandidateService,
    normalize_name,
)
from author_resolution.context import QueryContext
from author_resolution.enrichment import CandidateEnrichmentService, EnrichmentReport
from author_resolution.evidence import Evidence, extract_evidence
from author_resolution.policy import (
    AUTO_RESOLVED, MANUAL_REVIEW, UNRESOLVED, DecisionOutcome, evaluate_decision,
)
from author_resolution.scoring import CandidateScore, score_evidence

MANUAL_SELECTED = "manual_selected"


class CandidateSourceUnavailable(RuntimeError):
    """Candidate retrieval failed; this is not an unresolved identity decision.

    A successful response with zero candidates is *not* this error: it is a legitimate
    retrieval outcome (status "empty") that resolves to ``unresolved`` with no candidate rows.
    """

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.error_code = error_code


@dataclass(frozen=True)
class PoolResult:
    """Structured outcome of candidate retrieval + enrichment + persistence."""
    rows: list[AuthorCandidate]
    ranked: list["RankedCandidate"]
    status: str                      # "ok" | "empty" | provider error code
    failed: bool = False
    error_code: str | None = None
    enrichment: EnrichmentReport | None = None
    query_context: QueryContext = field(default_factory=QueryContext)


@dataclass(frozen=True)
class ResolutionOutcome:
    resolution: AuthorResolution
    retrieval_status: str            # "ok" | "empty" | "stored_pool"
    decision: DecisionOutcome
    enrichment: dict[str, Any] | None = None
    unparsable_candidate_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RankedCandidate:
    candidate: OpenAlexCandidate
    evidence: list[Evidence]
    score: CandidateScore


def rank_candidates(candidates: list[OpenAlexCandidate], context: Any = None) -> list[RankedCandidate]:
    ctx = QueryContext.from_any(context)
    ranked: list[RankedCandidate] = []
    for candidate in candidates:
        evidence = extract_evidence(candidate, ctx)
        ranked.append(RankedCandidate(candidate, evidence, score_evidence(evidence)))
    # deterministic display ordering only; it is not an identity assertion.
    return sorted(ranked, key=lambda item: (item.score.score is not None, item.score.score or -1.0, item.candidate.source_author_id), reverse=True)


def decide(ranked: list[RankedCandidate]) -> tuple[str, float | None, float | None, float | None, float | None, str]:
    """Compatibility wrapper returning (status, top, second, margin, dominance, reason)."""
    return evaluate_decision(ranked).as_tuple()


class AuthorResolutionService:
    def __init__(
        self,
        candidate_service: OpenAlexCandidateService | None = None,
        enrichment_service: CandidateEnrichmentService | None = None,
    ):
        self.candidate_service = candidate_service or OpenAlexCandidateService()
        self.enrichment_service = enrichment_service or CandidateEnrichmentService()

    async def generate_pool(
        self, author_name: str, institution_hint: str | None, context: dict[str, Any] | None, db: AsyncSession
    ) -> PoolResult:
        """Retrieve, enrich, persist and rank candidates, keeping retrieval status structured.

        ``status`` is "ok" (candidates), "empty" (successful response, zero candidates) or a provider
        error code (``failed=True``). Enrichment failures never fail the pool; they are recorded per
        signal and reported in ``enrichment``.
        """
        request_context = dict(context or {})
        if institution_hint:
            request_context.setdefault("institution_hints", [institution_hint])
        query_context = QueryContext.from_any(request_context)
        result = await self.candidate_service.generate(
            AuthorCandidateInput(author_name, institution_hint, request_context)
        )
        if result.status == "failed":
            code = result.error_code or "candidate_source_failed"
            return PoolResult([], [], code, True, code, None, query_context)
        report = await self.enrichment_service.enrich(result.candidates, query_context)
        enriched = replace(result, candidates=report.candidates)
        try:
            rows = await self.candidate_service.persist_candidates(enriched, db)
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise
        return PoolResult(rows, rank_candidates(report.candidates, query_context), result.status, False, None, report, query_context)

    async def generate_and_rank(self, author_name: str, institution_hint: str | None, context: dict[str, Any] | None, db: AsyncSession) -> tuple[list[AuthorCandidate], list[RankedCandidate], str]:
        pool = await self.generate_pool(author_name, institution_hint, context, db)
        return pool.rows, pool.ranked, pool.status

    async def create_resolution(self, *args: Any, **kwargs: Any) -> AuthorResolution:
        return (await self.create_resolution_detailed(*args, **kwargs)).resolution

    async def create_resolution_detailed(
        self,
        author_name: str,
        institution_hint: str | None,
        context: dict[str, Any] | None,
        db: AsyncSession,
        selected_candidate_id: str | None = None,
        mark_unresolved: bool = False,
        reason: str | None = None,
        candidate_ids: list[str] | None = None,
    ) -> ResolutionOutcome:
        request_context = dict(context or {})
        if institution_hint:
            request_context.setdefault("institution_hints", [institution_hint])
        query_context = QueryContext.from_any(request_context)
        normalized_query = normalize_name(author_name)

        if mark_unresolved and selected_candidate_id:
            raise ValueError("An unresolved decision cannot also select a candidate.")

        requested_ids: set[str] | None = None
        unparsable: list[str] = []
        enrichment_summary: dict[str, Any] | None = None
        if candidate_ids is not None:
            requested_ids = set(candidate_ids)
            if candidate_ids:
                stmt = select(AuthorCandidate).where(AuthorCandidate.id.in_(candidate_ids))
                res = await db.execute(stmt)
                rows = list(res.scalars().all())
            else:
                rows = []
            if (
                len(rows) != len(requested_ids)
                or any(row.query_normalized != normalized_query for row in rows)
            ):
                raise ValueError("One or more candidates do not belong to this author query.")
            row_by_source_id = {row.source_author_id: row for row in rows}
            candidates_list = []
            for row in rows:
                try:
                    candidates_list.append(replace(OpenAlexCandidate.from_persisted(row), query_original=author_name))
                except Exception:
                    # Not silent: the decision is marked incomplete and the id is returned to the caller.
                    unparsable.append(row.id)
            ranked = rank_candidates(candidates_list, query_context) if candidates_list else []
            retrieval_status = "stored_pool"
        else:
            pool = await self.generate_pool(author_name, institution_hint, context, db)
            if pool.failed:
                raise CandidateSourceUnavailable(
                    "Candidate source unavailable: no resolution decision was recorded", pool.error_code)
            rows, ranked, retrieval_status = pool.rows, pool.ranked, pool.status   # "ok" or "empty"
            row_by_source_id = {row.source_author_id: row for row in rows}
            enrichment_summary = pool.enrichment.summary() if pool.enrichment else None

        outcome = evaluate_decision(ranked, incomplete_pool=bool(unparsable))
        status, top, second, margin, dominance, decision_reason = outcome.as_tuple()
        if retrieval_status == "empty":
            decision_reason = "No candidates were returned by OpenAlex (successful empty response); no identity could be proposed."
        algorithmic = f"Algorithmic assessment: {status}. {decision_reason}"
        selected_row = None

        if mark_unresolved:
            status, decision_reason = UNRESOLVED, f"{reason or 'Reviewer marked this query unresolved.'} | {algorithmic}"
            top, second, margin, dominance = None, None, None, None
        elif selected_candidate_id:
            if requested_ids is not None and selected_candidate_id not in requested_ids:
                raise ValueError("The selected candidate must be included in the supplied candidate set.")
            selected_row = await db.get(AuthorCandidate, selected_candidate_id)
            if selected_row is None or selected_row.query_normalized != normalized_query:
                raise ValueError("Selected candidate does not belong to this author query.")
            status, decision_reason = MANUAL_SELECTED, f"{reason or 'Reviewer manually selected this candidate.'} | {algorithmic}"
        elif status == AUTO_RESOLVED and ranked:
            selected_row = row_by_source_id.get(ranked[0].candidate.source_author_id)

        try:
            resolution = AuthorResolution(
                query_original=author_name,
                query_normalized=normalized_query,
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
            db.add(resolution)

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

            await db.flush()

            for item in ranked:
                candidate_row = row_by_source_id.get(item.candidate.source_author_id)
                if not candidate_row:
                    continue
                for evidence in item.evidence:
                    values = evidence.as_db_values()
                    db.add(AuthorResolutionEvidence(
                        resolution=resolution,
                        candidate=candidate_row,
                        # Effective (renormalised) weight actually applied; None when the signal was unavailable.
                        weight=item.score.effective_weights.get(evidence.signal_name),
                        weighted_contribution=item.score.contributions.get(evidence.signal_name),
                        **values,
                    ))

            await db.commit()
            await db.refresh(resolution)
        except SQLAlchemyError:
            await db.rollback()
            raise
        return ResolutionOutcome(resolution, retrieval_status, outcome, enrichment_summary, tuple(unparsable))

    async def get_resolution(self, resolution_id: str, db: AsyncSession) -> AuthorResolution | None:
        return await db.scalar(select(AuthorResolution).where(AuthorResolution.id == resolution_id))
