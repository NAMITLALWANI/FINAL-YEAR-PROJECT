import asyncio
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import Publication, SourceRecord
from services.scholarly_retrieval import build_document, generate_explanation, index_status, retrieve


def test_document_is_stable_and_keeps_source_provenance():
    publication = Publication(
        id=7,
        canonical_id="doi:10.1000/example",
        title="Evidence based scholarly retrieval",
        authors=json.dumps(["Ada Author", "Lin Researcher"]),
        year=2024,
        abstract=None,
        venue="Example Journal",
        doi="10.1000/example",
        source_list=json.dumps(["crossref"]),
    )
    source = SourceRecord(id=11, source="openalex", source_id="W123", url="https://example.org/work", raw_json=json.dumps({"topics": [{"display_name": "Computer science"}], "affiliations": [{"name": "Example University"}]}))

    first = build_document(publication, [source])
    second = build_document(publication, [source])

    assert first is not None
    assert first.id == second.id
    assert first.content_hash == second.content_hash
    assert "Abstract:" not in first.text
    assert first.metadata["source_providers"] == '["crossref", "openalex"]'
    assert first.metadata["source_record_ids"] == '["11"]'
    assert first.metadata["url"] == "https://example.org/work"
    assert first.metadata["concepts"] == '["Computer science"]'
    assert first.metadata["affiliation_mentions"] == '["Example University"]'


def test_no_records_abstains_without_calling_provider(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://compatible.example/v1/")
    result = asyncio.run(generate_explanation("Ada Author", []))
    assert result["status"] == "abstained"
    assert result["claims"] == []


def test_empty_persistent_collection_returns_empty_without_model_call(tmp_path):
    result = asyncio.run(retrieve("Ada Author", path=tmp_path / "empty-index"))
    assert result == []
    assert index_status(tmp_path / "empty-index")["status"] == "empty"


def test_generated_claims_must_cite_retrieved_document(monkeypatch):
    import httpx
    from services.scholarly_retrieval import RetrievalHit

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_BASE_URL", "https://generativelanguage.example/v1beta")
    hit = RetrievalHit("doc-1", "doi:1", "A grounded title", None, "10.1/x", 2020, None, ["Ada Author"], [], ["crossref"], ["2"], {"crossref": ["R1"]}, "https://example.org", 0.7, 1, "hash")

    calls = []
    timeouts = []

    class Response:
        status_code = 200
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": json.dumps({
                "summary": "This unreferenced summary must not pass.",
                "claims": [
                    {"text": "This title is in the retrieved record.", "document_ids": ["doc-1"]},
                    {"text": "Unsupported claim.", "document_ids": ["fabricated"]},
                ],
            })}]}}], "usageMetadata": {"totalTokenCount": 17}}

    class Client:
        def __init__(self, **kwargs):
            timeouts.append(kwargs["timeout"])

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            calls.append((args, kwargs))
            return Response()

    monkeypatch.setattr(httpx, "AsyncClient", Client)
    result = asyncio.run(generate_explanation("Ada Author", [hit]))

    assert result["status"] == "generated"
    assert result["claims"] == [{"text": "This title is in the retrieved record.", "document_ids": ["doc-1"]}]
    assert "unreferenced summary" not in result["summary"]
    assert "Unsupported claim" not in result["summary"]
    assert result["http_status"] == 200
    assert result["provider"] == "gemini"
    assert result["token_usage"] == {"totalTokenCount": 17}
    url, = calls[0][0]
    assert url == "https://generativelanguage.example/v1beta/models/test-model:generateContent"
    assert calls[0][1]["headers"] == {"x-goog-api-key": "test-key"}
    assert calls[0][1]["json"]["generationConfig"] == {"temperature": 0, "responseMimeType": "application/json"}
    assert calls[0][1]["json"]["contents"][0]["role"] == "user"
    assert calls[0][1]["json"]["systemInstruction"]["parts"]
    assert timeouts == [12.0]


def test_explanation_with_no_valid_citations_returns_fallback(monkeypatch):
    import httpx
    from services.scholarly_retrieval import RetrievalHit

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_BASE_URL", "https://generativelanguage.example/v1beta")
    hit = RetrievalHit("doc-1", "doi:1", "Grounded record", None, None, 2020, None, [], [], ["crossref"], [], {}, None, 0.7, 1, "hash")

    class Response:
        status_code = 200
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": json.dumps({
                "summary": "Unsupported summary.",
                "claims": [{"text": "Unsupported claim.", "document_ids": ["unknown"]}],
            })}]}}]}

    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, *args, **kwargs): return Response()

    monkeypatch.setattr(httpx, "AsyncClient", Client)
    result = asyncio.run(generate_explanation("query", [hit]))

    assert result["status"] == "citation_validation_failed_fallback"
    assert result["provider"] == "deterministic"
    assert result["claims"] == []
    assert "Unsupported summary" not in result["summary"]
    assert "Unsupported claim" not in result["summary"]


def test_unconfigured_provider_uses_local_deterministic_explanation(monkeypatch):
    from services.scholarly_retrieval import RetrievalHit

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    hit = RetrievalHit("doc-1", "doi:1", "Local record", None, None, 2020, None, [], [], ["crossref"], [], {}, None, 0.7, 1, "hash")
    result = asyncio.run(generate_explanation("query", [hit]))

    assert result["status"] == "provider_not_configured"
    assert result["provider"] == "deterministic"
    assert result["claims"][0]["document_ids"] == ["doc-1"]
    assert "do not establish" in result["summary"]


def test_provider_failure_returns_local_fallback(monkeypatch):
    import httpx
    from services.scholarly_retrieval import RetrievalHit

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_BASE_URL", "https://generativelanguage.example/v1beta")
    hit = RetrievalHit("doc-1", "doi:1", "Local record", None, None, 2020, None, [], [], ["crossref"], [], {}, None, 0.7, 1, "hash")

    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, *args, **kwargs): raise RuntimeError("mock provider failure")

    monkeypatch.setattr(httpx, "AsyncClient", Client)
    result = asyncio.run(generate_explanation("query", [hit]))

    assert result["status"] == "provider_error_fallback"
    assert result["provider"] == "deterministic"
    assert result["claims"][0]["document_ids"] == ["doc-1"]
    assert "mock provider failure" not in result["summary"]


def test_malformed_or_empty_provider_responses_return_safe_fallback(monkeypatch):
    import httpx
    from services.scholarly_retrieval import RetrievalHit

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_BASE_URL", "https://generativelanguage.example/v1beta")
    hit = RetrievalHit("doc-1", "doi:1", "Local record", None, None, 2020, None, [], [], ["crossref"], [], {}, None, 0.7, 1, "hash")

    class Response:
        status_code = 200
        def __init__(self, content): self.content = content
        def raise_for_status(self): return None
        def json(self): return {"candidates": [{"content": {"parts": [{"text": self.content}]}}]}

    class Client:
        def __init__(self, content, **kwargs): self.content = content
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, *args, **kwargs): return Response(self.content)

    import httpx as httpx_module
    for content in ("not json", json.dumps({"summary": "empty claims", "claims": []})):
        monkeypatch.setattr(httpx_module, "AsyncClient", lambda **kwargs: Client(content, **kwargs))
        result = asyncio.run(generate_explanation("query", [hit], max_attempts=1))
        assert result["status"] in {"provider_error_fallback", "citation_validation_failed_fallback"}
        assert result["http_status"] == 200
        assert "test-key" not in json.dumps(result)


def test_http_auth_and_rate_limit_errors_do_not_expose_provider_payload(monkeypatch, caplog):
    import httpx
    from services.scholarly_retrieval import RetrievalHit

    monkeypatch.setenv("GEMINI_API_KEY", "secret-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_BASE_URL", "https://generativelanguage.example/v1beta")
    hit = RetrievalHit("doc-1", "doi:1", "Local record", None, None, 2020, None, [], [], ["crossref"], [], {}, None, 0.7, 1, "hash")

    class Client:
        def __init__(self, status, **kwargs): self.status = status
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs):
            request = httpx.Request("POST", url)
            response = httpx.Response(self.status, request=request, text="secret-test-key provider detail")
            raise httpx.HTTPStatusError("secret-test-key provider detail", request=request, response=response)

    for status in (401, 403, 429, 500):
        monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: Client(status, **kwargs))
        result = asyncio.run(generate_explanation("query", [hit], max_attempts=1))
        assert result["status"] == "provider_error_fallback"
        assert result["http_status"] == status
        assert "secret-test-key" not in json.dumps(result)
        assert "secret-test-key" not in caplog.text


def test_timeout_falls_back_and_smoke_preflight_never_sends_without_configuration(monkeypatch):
    import httpx
    from services.scholarly_retrieval import RetrievalHit
    from scripts.smoke_llm_provider import run_smoke

    monkeypatch.setenv("GEMINI_API_KEY", "secret-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_BASE_URL", "https://generativelanguage.example/v1beta")
    hit = RetrievalHit("doc-1", "doi:1", "Local record", None, None, 2020, None, [], [], ["crossref"], [], {}, None, 0.7, 1, "hash")

    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, *args, **kwargs): raise httpx.ReadTimeout("secret-test-key network error")

    monkeypatch.setattr(httpx, "AsyncClient", Client)
    result = asyncio.run(generate_explanation("query", [hit], max_attempts=1))
    assert result["status"] == "provider_error_fallback"
    assert result["http_status"] is None
    assert "secret-test-key" not in json.dumps(result)

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    report, status = asyncio.run(run_smoke())
    assert status == 2
    assert report["status"] == "configuration_error"
    assert report["live_request_made"] is False


def test_smoke_command_reports_synthetic_validated_result_without_network(monkeypatch):
    from scripts import smoke_llm_provider
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    observed = {}

    async def fake_explain(query, hits, *, timeout_seconds, max_attempts):
        observed.update(query=query, hit_count=len(hits), timeout=timeout_seconds, attempts=max_attempts)
        return {"status": "generated", "summary": "Synthetic metadata topic.", "claims": [{"text": "Synthetic metadata topic.", "document_ids": ["smoke-doc-1"]}], "latency_ms": 5, "http_status": 200}

    monkeypatch.setattr(smoke_llm_provider, "generate_explanation", fake_explain)
    report, status = asyncio.run(smoke_llm_provider.run_smoke(timeout_seconds=7))
    assert status == 0
    assert report["usable_explanation"] is True
    assert report["citations_passed_validation"] is True
    assert report["live_request_made"] is True
    assert observed == {"query": "What topic is represented in this synthetic example record?", "hit_count": 1, "timeout": 7, "attempts": 1}


def test_smoke_does_not_call_fallback_claims_provider_validated(monkeypatch):
    from scripts import smoke_llm_provider
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")

    async def fallback(*args, **kwargs):
        return {"status": "provider_error_fallback", "summary": "Local fallback", "claims": [{"text": "Retrieved publication", "document_ids": ["smoke-doc-1"]}], "latency_ms": 2, "http_status": None}

    monkeypatch.setattr(smoke_llm_provider, "generate_explanation", fallback)
    report, status = asyncio.run(smoke_llm_provider.run_smoke())
    assert status == 1
    assert report["usable_explanation"] is False
    assert report["citations_passed_validation"] is False

def test_retrieval_similarity_floor_and_title_dedup(tmp_path):
    from services.scholarly_retrieval import _chroma_collection, _search, ScholarlyDocument, _upsert_documents
    
    idx_path = tmp_path / 'test_dedup_idx'
    doc1 = ScholarlyDocument(
        id='pub_1',
        text='Deep Learning and Artificial Intelligence Foundations Hinton Bengio LeCun',
        metadata={
            'canonical_id': 'doi_123',
            'title': 'Deep Learning Foundations',
            'doi': '10.1000/1',
            'year': 2020,
            'authors': json.dumps(['Geoffrey Hinton']),
            'content_hash': 'h1'
        },
        content_hash='h1'
    )
    # Duplicate with different canonical_id (e.g. raw_1)
    doc2 = ScholarlyDocument(
        id='pub_2',
        text='Deep Learning and Artificial Intelligence Foundations Hinton Bengio LeCun',
        metadata={
            'canonical_id': 'raw_1',
            'title': 'Deep Learning Foundations.',
            'doi': '10.1000/1',
            'year': 2020,
            'authors': json.dumps(['Geoffrey Hinton']),
            'content_hash': 'h2'
        },
        content_hash='h2'
    )
    _upsert_documents([doc1, doc2], path=idx_path)
    
    # Search with deduplication: only 1 hit should be returned even though both match
    hits = _search('Deep Learning and Artificial Intelligence', top_k=5, filters=None, path=idx_path, min_score=0.35)
    assert len(hits) == 1
    assert hits[0].title == 'Deep Learning Foundations'
    
    # High threshold / irrelevant query: should be rejected
    hits_irrelevant = _search('quantum computing superconductivity qubit', top_k=5, filters=None, path=idx_path, min_score=0.85)
    assert len(hits_irrelevant) == 0
