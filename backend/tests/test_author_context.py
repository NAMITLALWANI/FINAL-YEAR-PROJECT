import pytest

from author_resolution.context import (
    ContextValidationError, QueryContext, normalize_doi, normalize_openalex_id, normalize_ror,
)


def test_doi_and_id_normalisation():
    assert normalize_doi("https://doi.org/10.1000/ABC.1") == "10.1000/abc.1"
    assert normalize_doi("doi:10.1000/x") == "10.1000/x"
    assert normalize_doi("10.1/x") is None            # registrant too short
    assert normalize_doi("not a doi") is None
    assert normalize_doi(None) is None
    assert normalize_openalex_id("https://openalex.org/w123456", "work") == "W123456"
    assert normalize_openalex_id("A1234", "author") == "A1234"
    assert normalize_openalex_id("W123456", "author") is None
    assert normalize_ror("https://ror.org/03yrm5c26") == "03yrm5c26"


def test_absent_is_distinct_from_empty_and_nothing_is_invented():
    ctx = QueryContext.from_any(None)
    assert not any(ctx.provided_categories().values())
    assert ctx.active_year_start is None and ctx.publication_fingerprint() is None
    ctx2 = QueryContext.from_any({"publications": [], "coauthors": []})
    assert not ctx2.has_publications and not ctx2.has_coauthors


def test_legacy_dict_shape_is_accepted():
    ctx = QueryContext.from_any({
        "institution_hints": ["Example Institute"], "coauthors": ["Bob Jones"],
        "publications": [{"doi": "10.1000/abc"}, {"title": "Only a title"}, "W123456"],
        "active_year_start": 2015, "active_year_end": 2020,
    })
    assert [i.name for i in ctx.institutions] == ["Example Institute"]
    assert ctx.publication_dois == ("10.1000/abc",) and ctx.publication_work_ids == ("W123456",)
    assert ctx.ignored_title_only == 1                  # titles are never compared
    assert (ctx.active_year_start, ctx.active_year_end) == (2015, 2020)


def test_institution_hint_is_merged_not_duplicated():
    ctx = QueryContext.from_any({"institution_hints": ["Example Institute"]}, "Example Institute")
    assert len(ctx.institutions) == 1


def test_lenient_mode_records_rejections_strict_mode_raises():
    bad = {"publications": ["nonsense"], "active_year_start": 2030, "active_year_end": 2020}
    lenient = QueryContext.from_any(bad)
    assert lenient.rejected_inputs and not lenient.has_publications and not lenient.has_years
    with pytest.raises(ContextValidationError):
        QueryContext.from_any(bad, strict=True)
    with pytest.raises(ContextValidationError):
        QueryContext.from_any({"coauthors": [{"openalex_id": "nope"}]}, strict=True)
    with pytest.raises(ContextValidationError):
        QueryContext.from_any({"publications": [f"10.1000/x{i}" for i in range(51)]}, strict=True)


def test_fingerprint_is_order_independent_and_changes_with_identifiers():
    a = QueryContext.from_any({"publications": ["10.1000/a", "10.1000/b"]})
    b = QueryContext.from_any({"publications": ["10.1000/b", "10.1000/a"]})
    c = QueryContext.from_any({"publications": ["10.1000/a"]})
    assert a.publication_fingerprint() == b.publication_fingerprint() != c.publication_fingerprint()
