"""Make one explicit, low-volume LLM smoke request with synthetic evidence."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import config first so its existing APP_ENV/.env loading convention applies.
import config  # noqa: F401
from services.scholarly_retrieval import RetrievalHit, generate_explanation


def validate_configuration() -> tuple[str, str]:
    api_key = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", "").strip()
    base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").strip()
    key_lower = api_key.casefold()
    if not api_key or any(marker in key_lower for marker in ("your-api-key", "replace-with", "changeme")):
        raise ValueError("Missing GEMINI_API_KEY")
    if not model or model.casefold().startswith(("replace-with", "your-model")) or len(model) > 128 or not re.fullmatch(r"[A-Za-z0-9._:/-]+", model):
        raise ValueError("GEMINI_MODEL must be a configured model identifier")
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("GEMINI_BASE_URL must be an http(s) API root without embedded credentials, query, or fragment")
    return model, parsed.hostname


async def run_smoke(timeout_seconds: float = 12.0) -> tuple[dict[str, object], int]:
    try:
        model, provider_host = validate_configuration()
    except ValueError as exc:
        return {"provider_format": "Gemini generateContent", "status": "configuration_error", "error": str(exc), "live_request_made": False}, 2

    synthetic_hit = RetrievalHit(
        document_id="smoke-doc-1", canonical_id="synthetic:smoke-1",
        title="Synthetic Example: Scholarly Metadata Records", abstract="Synthetic evidence for checking structured explanation output.",
        doi=None, year=2025, venue="Synthetic Test Venue", authors=["Example Researcher"],
        affiliation_mentions=[], sources=["synthetic"], source_record_ids=[], source_external_ids={},
        url=None, score=1.0, rank=1, content_hash="synthetic-smoke-record-v1",
    )
    try:
        result = await generate_explanation(
            "What topic is represented in this synthetic example record?",
            [synthetic_hit], timeout_seconds=timeout_seconds, max_attempts=1,
        )
    except Exception:
        # Keep unexpected exception details (which might include request data) out of output.
        return {"provider_format": "Gemini generateContent", "provider_host": provider_host, "model": model, "status": "client_error", "live_request_made": True}, 1

    claims = result.get("claims") if isinstance(result.get("claims"), list) else []
    allowed_ids = {synthetic_hit.document_id}
    citations_validated = result.get("status") == "generated" and bool(claims) and all(
        isinstance(claim, dict)
        and isinstance(claim.get("document_ids"), list)
        and bool(claim["document_ids"])
        and all(doc_id in allowed_ids for doc_id in claim["document_ids"])
        for claim in claims
    )
    usable = result.get("status") == "generated" and bool(str(result.get("summary", "")).strip())
    report = {
        "provider_format": "Gemini generateContent",
        "provider_host": provider_host,
        "model": model,
        "status": result.get("status"),
        "http_status": result.get("http_status"),
        "latency_ms": result.get("latency_ms"),
        "usable_explanation": usable,
        "citations_passed_validation": citations_validated,
        "live_request_made": True,
    }
    return report, 0 if usable and citations_validated else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=12.0, help="Request timeout in seconds (default: 12; max: 60)")
    args = parser.parse_args()
    if not 1.0 <= args.timeout <= 60.0:
        parser.error("--timeout must be between 1 and 60 seconds")
    report, status = asyncio.run(run_smoke(args.timeout))
    print(json.dumps(report, indent=2, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())