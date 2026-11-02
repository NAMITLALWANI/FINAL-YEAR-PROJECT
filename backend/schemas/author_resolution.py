import json
from typing import Any
from pydantic import BaseModel, Field, model_validator


class CandidateRequest(BaseModel):
    author_name: str = Field(min_length=2, max_length=200)
    institution_hint: str | None = Field(default=None, max_length=300)
    context: dict[str, Any] | None = None

    @model_validator(mode="after")
    def bounded_context(self):
        if self.context is not None and len(json.dumps(self.context, ensure_ascii=False)) > 5000:
            raise ValueError("context must be at most 5000 characters when serialized")
        return self


class ResolutionRequest(CandidateRequest):
    selected_candidate_id: str | None = None
    mark_unresolved: bool = False
    reason: str | None = Field(default=None, max_length=500)


class EvidenceSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    doi: str | None = Field(default=None, max_length=256)
    year: int | None = Field(default=None, ge=1800, le=2200)
    source: str | None = Field(default=None, max_length=40)
    candidate_names: list[str] = Field(default_factory=list, max_length=20)


def evidence_response(evidence):
    return {"signal": evidence.signal_name, "availability": evidence.availability, "score": evidence.normalized_score, "explanation": evidence.explanation, "raw_value": evidence.raw_value, "provenance": evidence.provenance}


def ranked_candidate_response(candidate_row, ranked):
    return {
        "candidate_id": candidate_row.id,
        "source": candidate_row.source,
        "source_author_id": candidate_row.source_author_id,
        "display_name": candidate_row.display_name,
        "institution_summary": candidate_row.institution_summary,
        "works_count": candidate_row.works_count,
        "citation_count": candidate_row.citation_count,
        "years_active_start": candidate_row.years_active_start,
        "years_active_end": candidate_row.years_active_end,
        "score": ranked.score.score,
        "available_signals": ranked.score.available_signals,
        "evidence": [evidence_response(item) for item in ranked.evidence],
        "identity_note": "OpenAlex profile candidate only; not a confirmed cross-source identity.",
    }