"""Backward-compatible facade forwarding to rag.retrieval and explanation.synthesis."""
from rag.retrieval import *
from rag.retrieval import _chroma_collection, _search, _upsert_documents
from explanation.synthesis import generate_explanation
