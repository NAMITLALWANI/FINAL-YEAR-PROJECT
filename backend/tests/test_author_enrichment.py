import asyncio

import httpx

from author_resolution.context import QueryContext
from author_resolution.enrichment import CandidateEnrichmentService
from author_test_helpers import cand, json_response, work


def run(coro):
    return asyncio.run(coro)


def service(handler, **kw):
    return CandidateEnrichmentService(transport=httpx.MockTransport(handler), **kw)


def recorder(responses):
    """Handler that returns queued responses (or raises queued exceptions) and records every request."""
    seen = []

    def handler(request):
        seen.append(request)
        item = responses[min(len(seen) - 1, len(responses) - 1)]
        if isinstance(item, Exception):
            raise item
        return item
    return handler, seen


PUB_CTX = QueryContext.from_any({"publications": ["10.1000/a", "10.1000/b"]})
CO_CTX = QueryContext.from_any({"coauthors": [{"openalex_id": "A7"}]})


def test_no_query_inputs_means_no_requests():
    handler, seen = recorder([json_response({"results": []})])
    report = run(service(handler).enrich([cand("A1")], QueryContext.from_any({"institution_hints": ["Example Institute"]})))
    assert seen == [] and report.query_works_status is None and report.candidates[0].publication_evidence is None


def test_publication_links_come_from_query_works_authorships():
    body = {"results": [work("W1", "10.1000/a", ["A1", "A9"]), work("W2", "10.1000/b", ["A9"])]}
    handler, seen = recorder([json_response(body)])
    report = run(service(handler).enrich([cand("A1"), cand("A2")], PUB_CTX))
    assert len(seen) == 1                                       # one query-level request, not one per candidate
    assert "https://doi.org/10.1000/a" in seen[0].url.params["filter"]
    a1, a2 = (c.publication_evidence for c in report.candidates)
    assert a1.status == "ok" and a1.matched_work_ids == ("W1",) and set(a1.comparable_work_ids) == {"W1", "W2"}
    assert a2.matched_work_ids == () and set(a2.comparable_work_ids) == {"W1", "W2"}
    assert a1.context_fingerprint == PUB_CTX.publication_fingerprint()
    assert report.candidates[0].sample_publications == [{"openalex_work_id": "W1", "doi": None}]


def test_unresolved_dois_and_truncated_author_lists_are_not_counted_as_conflicts():
    body = {"results": [work("W1", "10.1000/a", ["A9"], truncated=True)]}   # 10.1000/b not found at all
    handler, _ = recorder([json_response(body)])
    pub = run(service(handler).enrich([cand("A1")], PUB_CTX)).candidates[0].publication_evidence
    assert pub.unresolved_identifiers == ("10.1000/b",)
    assert pub.truncated_author_work_ids == ("W1",) and pub.comparable_work_ids == ()


def test_empty_works_response_is_empty_not_failed():
    handler, _ = recorder([json_response({"results": []})])
    report = run(service(handler).enrich([cand("A1")], PUB_CTX))
    assert report.query_works_status == "empty" and not report.any_failed
    assert report.candidates[0].publication_evidence.status == "empty"


def test_provider_failures_are_recorded_per_signal_without_raising():
    for response in (httpx.ReadTimeout("slow"), json_response({}, 500), json_response({}, 429), httpx.Response(200, text="not json")):
        handler, _ = recorder([response])
        report = run(service(handler).enrich([cand("A1")], PUB_CTX))
        pub = report.candidates[0].publication_evidence
        assert pub.status == "failed" and pub.error_code and report.any_failed


def test_missing_doi_in_response_is_tolerated():
    handler, _ = recorder([json_response({"results": [work("W5", None, ["A1"])]})])
    pub = run(service(handler).enrich([cand("A1")], QueryContext.from_any({"publications": ["W5"]}))).candidates[0].publication_evidence
    assert pub.matched_work_ids == ("W5",) and pub.matched_dois == ()


def test_coauthors_use_stable_ids_exclude_self_and_dedupe_across_pages():
    page1 = {"meta": {"count": 3}, "results": [work("W1", "10.1000/a", ["A1", "A7", "A8"]), work("W2", None, ["A1", "A7"])]}
    page2 = {"meta": {"count": 3}, "results": [work("W3", None, ["A1", "A7"])]}
    handler, seen = recorder([json_response(page1), json_response(page2)])
    report = run(service(handler, per_page=2, max_pages=3).enrich([cand("A1")], CO_CTX))
    ev = report.candidates[0].coauthor_evidence
    assert [r.url.params["page"] for r in seen] == ["1", "2"]          # stops once all 3 works were examined
    assert [c["openalex_id"] for c in ev.coauthors] == ["A7", "A8"]    # own ID excluded, A7 not duplicated
    assert ev.coauthors[0]["work_ids"] == ["W1", "W2", "W3"] and ev.complete and ev.works_examined == 3
    assert "author.id:A1" in seen[0].url.params["filter"]


def test_coauthor_sample_is_bounded_and_flagged_incomplete():
    page = {"meta": {"count": 500}, "results": [work(f"W{i}", None, ["A1", f"A{i + 10}"]) for i in range(2)]}
    handler, seen = recorder([json_response(page)])
    ev = run(service(handler, per_page=2, max_pages=2).enrich([cand("A1")], CO_CTX)).candidates[0].coauthor_evidence
    assert len(seen) == 2 and not ev.complete and ev.works_total == 500


def test_partial_enrichment_page_two_failure_keeps_page_one():
    page1 = {"meta": {"count": 300}, "results": [work("W1", None, ["A1", "A7"]), work("W2", None, ["A1", "A8"])]}
    handler, _ = recorder([json_response(page1), json_response({}, 500)])
    ev = run(service(handler, per_page=2, max_pages=2).enrich([cand("A1")], CO_CTX)).candidates[0].coauthor_evidence
    assert ev.status == "ok" and not ev.complete and ev.provenance["partial"] is True


def test_empty_coauthor_works_and_first_page_failure():
    handler, _ = recorder([json_response({"meta": {"count": 0}, "results": []})])
    assert run(service(handler).enrich([cand("A1")], CO_CTX)).candidates[0].coauthor_evidence.status == "empty"
    handler, _ = recorder([httpx.ConnectError("down")])
    report = run(service(handler).enrich([cand("A1")], CO_CTX))
    assert report.candidates[0].coauthor_evidence.status == "failed" and report.any_failed


def test_rate_limit_stops_further_requests_and_marks_remaining_candidates_failed():
    handler, seen = recorder([json_response({}, 429)])
    report = run(service(handler).enrich([cand("A1"), cand("A2"), cand("A3")], CO_CTX))
    assert len(seen) == 1
    assert [c.coauthor_evidence.status for c in report.candidates] == ["failed"] * 3
    assert report.candidates[2].coauthor_evidence.error_code == "skipped_after_rate_limit"


def test_disabled_service_makes_no_requests():
    handler, seen = recorder([json_response({"results": []})])
    run(service(handler, enabled=False).enrich([cand("A1")], PUB_CTX))
    assert seen == []


def test_request_parameters_carry_no_query_text():
    handler, seen = recorder([json_response({"meta": {"count": 0}, "results": []})])
    run(service(handler).enrich([cand("A1", query="Alice Smith")], QueryContext.from_any({"coauthors": [{"name": "Bob Jones", "openalex_id": "A7"}]})))
    assert "Bob" not in str(seen[0].url) and "Alice" not in str(seen[0].url)


def test_works_sample_uses_an_explicit_documented_sort_and_records_provenance():
    page = {"meta": {"count": 500}, "results": [work(f"W{i}", None, ["A1", f"A{i + 10}"]) for i in range(2)]}
    handler, seen = recorder([json_response(page)])
    ev = run(service(handler, per_page=2, max_pages=2).enrich([cand("A1")], CO_CTX)).candidates[0].coauthor_evidence
    assert all(r.url.params["sort"] == "publication_date:desc,cited_by_count:desc" for r in seen)
    p = ev.provenance
    assert p["sort"] == "publication_date:desc,cited_by_count:desc" and p["per_page"] == 2 and p["pages_requested"] == 2
    assert p["pages_succeeded"] == 2 and p["works_examined"] == 4 and p["works_total"] == 500
    assert p["truncated"] is True and p["partial"] is False


def test_partial_failure_is_marked_truncated_and_partial():
    page1 = {"meta": {"count": 300}, "results": [work("W1", None, ["A1", "A7"]), work("W2", None, ["A1", "A8"])]}
    handler, _ = recorder([json_response(page1), json_response({}, 500)])
    p = run(service(handler, per_page=2, max_pages=2).enrich([cand("A1")], CO_CTX)).candidates[0].coauthor_evidence.provenance
    assert p["partial"] is True and p["truncated"] is True and p["pages_requested"] == 2 and p["pages_succeeded"] == 1


def test_name_only_coauthors_trigger_no_retrieval():
    handler, seen = recorder([json_response({"meta": {"count": 0}, "results": []})])
    report = run(service(handler).enrich([cand("A1")], QueryContext.from_any({"coauthors": ["Bob Jones"]})))
    assert seen == [] and report.candidates[0].coauthor_evidence is None


def test_malformed_candidate_id_never_issues_a_request():
    handler, seen = recorder([json_response({"meta": {"count": 0}, "results": []})])
    bad = cand("A1")
    from dataclasses import replace
    bad = replace(bad, source_author_id="None")
    ev = run(service(handler).enrich([bad], CO_CTX)).candidates[0].coauthor_evidence
    assert seen == [] and ev.status == "failed" and ev.error_code == "invalid_candidate_id"
