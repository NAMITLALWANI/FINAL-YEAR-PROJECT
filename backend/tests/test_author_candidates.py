import asyncio

import httpx

from services.author_candidates import AuthorCandidateInput, OpenAlexCandidateService


def run(coroutine):
    return asyncio.run(coroutine)


def author_payload(
    author_id="A1",
    display_name="Rajesh Kumar",
    institutions=None,
    **extra,
):
    payload = {
        "id": f"https://openalex.org/{author_id}",
        "display_name": display_name,
        "last_known_institutions": institutions or [],
        "works_count": 12,
        "cited_by_count": 34,
        "counts_by_year": [{"year": 2020, "works_count": 2}, {"year": 2024, "works_count": 3}],
    }
    payload.update(extra)
    return payload


def service_for_response(response_factory):
    def handler(request):
        assert request.url.path == "/authors"
        assert request.url.params["filter"].startswith("display_name.search:")
        return response_factory(request)

    return OpenAlexCandidateService(transport=httpx.MockTransport(handler))


def test_common_name_returns_multiple_openalex_candidates_and_preserves_provenance():
    service = service_for_response(
        lambda request: httpx.Response(
            200,
            json={
                "results": [
                    author_payload("A11", "Rajesh Kumar"),
                    author_payload("A22", "Rajesh Kumar"),
                ]
            },
        )
    )

    result = run(service.generate(AuthorCandidateInput("Rajesh Kumar", "IIT Bombay")))

    assert result.status == "ok"
    assert [candidate.source_author_id for candidate in result.candidates] == ["A11", "A22"]
    assert all(candidate.source == "openalex" for candidate in result.candidates)
    assert all(candidate.raw_payload["id"].startswith("https://openalex.org/") for candidate in result.candidates)


def test_unique_name_preserves_openalex_id_and_metadata():
    institution = {"id": "https://openalex.org/I123", "display_name": "Example University", "country_code": "IN"}
    service = service_for_response(
        lambda request: httpx.Response(
            200,
            json={"results": [author_payload("A123", "Unique Researcher", [institution])]},
        )
    )

    result = run(service.generate(AuthorCandidateInput("Unique Researcher")))

    assert result.status == "ok"
    candidate = result.candidates[0]
    assert candidate.source_author_id == "A123"
    assert candidate.source_author_url == "https://openalex.org/A123"
    assert candidate.institution_summary == "Example University"
    assert candidate.affiliations[0]["source_institution_id"] == "I123"
    assert candidate.works_count == 12
    assert candidate.citation_count == 34
    assert (candidate.years_active_start, candidate.years_active_end) == (2020, 2024)


def test_no_candidates_is_an_empty_result_not_an_identity_decision():
    service = service_for_response(lambda request: httpx.Response(200, json={"results": []}))

    result = run(service.generate(AuthorCandidateInput("No Such Author")))

    assert result.status == "empty"
    assert result.candidates == []
    assert result.error_code is None


def test_missing_affiliation_is_preserved_as_missing_evidence():
    service = service_for_response(
        lambda request: httpx.Response(200, json={"results": [author_payload("A1", "No Affiliation")]})
    )

    result = run(service.generate(AuthorCandidateInput("No Affiliation")))

    candidate = result.candidates[0]
    assert candidate.institution_summary is None
    assert candidate.affiliations == []


def test_multiple_affiliations_are_normalized_and_deduplicated():
    first = {"id": "https://openalex.org/I1", "display_name": "First University", "country_code": "IN"}
    second = {"institution": {"id": "https://openalex.org/I2", "display_name": "Second University", "country_code": "US"}, "years": [2021, 2022]}
    service = service_for_response(
        lambda request: httpx.Response(
            200,
            json={
                "results": [
                    author_payload("A1", "Multi Affiliation", [first], affiliations=[first, second])
                ]
            },
        )
    )

    result = run(service.generate(AuthorCandidateInput("Multi Affiliation")))

    candidate = result.candidates[0]
    assert candidate.institution_summary == "First University"
    assert [item["name"] for item in candidate.affiliations] == ["First University", "Second University"]
    assert candidate.affiliations[1]["years"] == [2021, 2022]


def test_http_failure_returns_safe_failure_result():
    service = service_for_response(lambda request: httpx.Response(503, json={"error": "unavailable"}))

    result = run(service.generate(AuthorCandidateInput("Unavailable Author")))

    assert result.status == "failed"
    assert result.error_code == "http_error"
    assert result.candidates == []


def test_timeout_returns_safe_failure_result():
    def handler(request):
        raise httpx.ReadTimeout("slow source", request=request)

    service = OpenAlexCandidateService(transport=httpx.MockTransport(handler))
    result = run(service.generate(AuthorCandidateInput("Slow Author")))

    assert result.status == "failed"
    assert result.error_code == "timeout"


def test_malformed_response_returns_safe_failure_result():
    service = service_for_response(lambda request: httpx.Response(200, json={"results": "not-a-list"}))

    result = run(service.generate(AuthorCandidateInput("Malformed")))

    assert result.status == "failed"
    assert result.error_code == "malformed_response"


def test_duplicate_openalex_candidates_are_not_returned_twice():
    duplicate = author_payload("A-duplicate", "Repeated Researcher")
    service = service_for_response(
        lambda request: httpx.Response(200, json={"results": [duplicate, duplicate.copy()]})
    )

    result = run(service.generate(AuthorCandidateInput("Repeated Researcher")))

    assert result.status == "ok"
    assert len(result.candidates) == 1
    assert result.candidates[0].source_author_id == "A-duplicate"