import csv
import json

import pytest

from scripts.merge_identity_reviews import LABEL_FIELDS, merge_reviews
from scripts.merge_retrieval_reviews import FIELDS as RETRIEVAL_FIELDS, merge_reviews as merge_relevance
from scripts.prepare_identity_review import prepare_packets
from scripts.prepare_retrieval_review import prepare_packets as prepare_retrieval_packets


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_prepare_blinded_packets_include_evidence_and_no_prediction_fields(tmp_path):
    queries = tmp_path / "queries.csv"
    evidence = tmp_path / "evidence.csv"
    write_csv(queries, ["query_id", "query_text", "context_json"], [{"query_id": "q1", "query_text": "Ada Example", "context_json": '{"institution":"Example U"}'}])
    write_csv(evidence, ["query_id", "source", "reference", "captured_at", "evidence_type", "excerpt_or_locator"], [{"query_id": "q1", "source": "Institution", "reference": "https://example.org/profile", "captured_at": "2026-01-01T00:00:00Z", "evidence_type": "official_profile", "excerpt_or_locator": "faculty page"}])
    paths = prepare_packets(queries, evidence, tmp_path / "packets")
    assert len(paths) == 2
    for path in paths:
        packet = path.read_text()
        assert "Ada Example" in packet
        assert "https://example.org/profile" in packet
        assert "reviewer_id" in packet
        assert "candidate_ids" not in packet.lower()
        assert "top_score" not in packet.lower()


def test_merge_independent_reviews_and_adjudication_to_manifest_schema(tmp_path):
    queries = tmp_path / "queries.csv"
    r1, r2, adj = (tmp_path / name for name in ("r1.csv", "r2.csv", "adj.csv"))
    write_csv(queries, ["query_id", "query_text", "context_json"], [{"query_id": "q1", "query_text": "Ada Example", "context_json": "{}"}])
    evidence = lambda source: json.dumps([{"source": source, "reference": f"https://example.org/{source}", "captured_at": "2026-01-01T00:00:00Z", "evidence_type": "official_profile"}])
    review_fields = ["query_id", "reviewer_id", "status", "confidence", "rationale", "gold_source", "gold_author_id", "evidence_refs_json"]
    write_csv(r1, review_fields, [{"query_id": "q1", "reviewer_id": "reviewer-a", "status": "resolved", "confidence": "4", "rationale": "Profile confirms identity", "gold_source": "openalex", "gold_author_id": "A1", "evidence_refs_json": evidence("one")}])
    write_csv(r2, review_fields, [{"query_id": "q1", "reviewer_id": "reviewer-b", "status": "unresolved", "confidence": "3", "rationale": "Insufficient stable identifiers", "gold_source": "", "gold_author_id": "", "evidence_refs_json": evidence("two")}])
    write_csv(adj, ["query_id", "adjudicator_id", "status", "confidence", "rationale", "gold_source", "gold_author_id", "evidence_refs_json"], [{"query_id": "q1", "adjudicator_id": "adjudicator-c", "status": "uncertain", "confidence": "2", "rationale": "Conflicting evidence", "gold_source": "", "gold_author_id": "", "evidence_refs_json": evidence("three")}])
    output = tmp_path / "identity_labels.csv"
    assert merge_reviews(queries, r1, r2, adj, output) == 1
    with output.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    assert reader.fieldnames == LABEL_FIELDS
    assert rows[0]["gold_status"] == "uncertain"
    assert rows[0]["adjudication_status"] == "uncertain"
    assert rows[0]["reviewer_1"] != rows[0]["reviewer_2"]
    assert len(json.loads(rows[0]["evidence_refs_json"])) == 3


def test_merge_rejects_missing_review_and_duplicate_reviewer(tmp_path):
    queries = tmp_path / "queries.csv"
    r1, r2, adj = (tmp_path / name for name in ("r1.csv", "r2.csv", "adj.csv"))
    write_csv(queries, ["query_id", "query_text", "context_json"], [{"query_id": "q1", "query_text": "Ada Example", "context_json": "{}"}])
    fields = ["query_id", "reviewer_id", "status", "confidence", "rationale", "gold_source", "gold_author_id", "evidence_refs_json"]
    row = {"query_id": "q1", "reviewer_id": "same", "status": "unresolved", "confidence": "3", "rationale": "checked", "gold_source": "", "gold_author_id": "", "evidence_refs_json": "[]"}
    write_csv(r1, fields, [row])
    write_csv(r2, fields, [row])
    write_csv(adj, ["query_id", "adjudicator_id", "status", "confidence", "rationale", "gold_source", "gold_author_id", "evidence_refs_json"], [])
    with pytest.raises(ValueError, match="distinct reviewers"):
        merge_reviews(queries, r1, r2, adj, tmp_path / "output.csv")


def test_retrieval_packets_hide_system_attribution_and_merge_adjudicated_pairs(tmp_path):
    packet = tmp_path / "packet.csv"
    write_csv(packet, ["query_id", "query_text", "canonical_publication_id", "title", "abstract", "doi", "url", "pool_protocol_version"], [{"query_id": "rq1", "query_text": "Graph models", "canonical_publication_id": "pub1", "title": "Graph Paper", "abstract": "Study", "doi": "10.1/x", "url": "https://example.org/paper", "pool_protocol_version": "pool-v1"}])
    htmls = prepare_retrieval_packets(packet, tmp_path / "html")
    assert len(htmls) == 2
    assert all("Graph Paper" in path.read_text() and "run-v1" not in path.read_text() and "score" not in path.read_text().lower() for path in htmls)
    pool = tmp_path / "pool.csv"
    r1, r2, adj = (tmp_path / name for name in ("rr1.csv", "rr2.csv", "ra.csv"))
    write_csv(pool, ["query_id", "canonical_publication_id"], [{"query_id": "rq1", "canonical_publication_id": "pub1"}])
    review_fields = ["query_id", "canonical_publication_id", "reviewer_id", "relevance", "evidence_note"]
    write_csv(r1, review_fields, [{"query_id": "rq1", "canonical_publication_id": "pub1", "reviewer_id": "reviewer-a", "relevance": "1", "evidence_note": "Topic matches"}])
    write_csv(r2, review_fields, [{"query_id": "rq1", "canonical_publication_id": "pub1", "reviewer_id": "reviewer-b", "relevance": "2", "evidence_note": "Directly addresses need"}])
    write_csv(adj, ["query_id", "canonical_publication_id", "adjudicator_id", "relevance", "evidence_note"], [{"query_id": "rq1", "canonical_publication_id": "pub1", "adjudicator_id": "reviewer-c", "relevance": "2", "evidence_note": "Full text confirms"}])
    output = tmp_path / "relevance.csv"
    assert merge_relevance(pool, r1, r2, adj, output) == 1
    with output.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        row = next(reader)
    assert reader.fieldnames == RETRIEVAL_FIELDS
    assert row["adjudication_status"] == "adjudicated"
    assert row["relevance"] == "2"