import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment profile
_ENV = os.getenv("APP_ENV", "dev")
_base = Path(__file__).parent
_env_file = _base / f".env.{_ENV}"
if _env_file.exists():
    load_dotenv(_env_file)
elif (_base / ".env").exists():
    load_dotenv(_base / ".env")

# Try to load demo env if present (overrides defaults if loaded)
if Path(".env.demo").exists():
    load_dotenv(".env.demo")

# ── Feature Flags ────────────────────────────────────────────────
ENABLE_OPENALEX = os.getenv("ENABLE_OPENALEX", "true").lower() == "true"
ENABLE_DBLP     = os.getenv("ENABLE_DBLP",     "true").lower() == "true"
ENABLE_CROSSREF = os.getenv("ENABLE_CROSSREF", "true").lower() == "true"
ENABLE_ARXIV    = os.getenv("ENABLE_ARXIV",    "true").lower() == "true"
ENABLE_SCHOLAR  = os.getenv("ENABLE_SCHOLAR",  "false").lower() == "true"
ENABLE_FACULTY  = os.getenv("ENABLE_FACULTY",  "false").lower() == "true"
DEMO_MODE       = os.getenv("DEMO_MODE",       "false").lower() == "true"

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
USE_CACHE     = os.getenv("USE_CACHE",     "true").lower()  == "true"

# ── Source Priority (lower = more trusted) ───────────────────────
SOURCE_PRIORITY: dict[str, int] = {
    "crossref":     1,
    "openalex":     2,
    "dblp":         3,
    "arxiv":        4,
    "scholar":      5,
    "faculty_page": 6,
}

# ── Deduplication Thresholds ─────────────────────────────────────
DEDUP_DEFAULT_THRESHOLD = float(os.getenv("DEDUP_DEFAULT_THRESHOLD", "0.85"))
DEDUP_LENIENT_THRESHOLD = float(os.getenv("DEDUP_LENIENT_THRESHOLD", "0.80"))  # openalex+crossref
DEDUP_STRICT_THRESHOLD  = float(os.getenv("DEDUP_STRICT_THRESHOLD",  "0.92"))  # any + scholar
DEDUP_LOG_THRESHOLD     = float(os.getenv("DEDUP_LOG_THRESHOLD",     "0.70"))  # only log above this

# ── Author Resolution Thresholds ─────────────────────────────────
AUTHOR_AUTO_SCORE_THRESHOLD = float(os.getenv("AUTHOR_AUTO_SCORE_THRESHOLD", "0.75"))
AUTHOR_AUTO_MARGIN_THRESHOLD = float(os.getenv("AUTHOR_AUTO_MARGIN_THRESHOLD", "0.15"))
AUTHOR_AUTO_DOMINANCE_THRESHOLD = float(os.getenv("AUTHOR_AUTO_DOMINANCE_THRESHOLD", "1.35"))
AUTHOR_MANUAL_SCORE_THRESHOLD = float(os.getenv("AUTHOR_MANUAL_SCORE_THRESHOLD", "0.45"))
AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO = int(os.getenv("AUTHOR_MIN_AVAILABLE_SIGNALS_FOR_AUTO", "2"))
RETRIEVAL_TIMEOUT_SECONDS = float(os.getenv("RETRIEVAL_TIMEOUT_SECONDS", "15"))
AUTHOR_RESOLVER_VERSION = os.getenv("AUTHOR_RESOLVER_VERSION", "v1")
AUTHOR_SCORING_VERSION = os.getenv("AUTHOR_SCORING_VERSION", "v1")
AUTHOR_THRESHOLD_VERSION = os.getenv("AUTHOR_THRESHOLD_VERSION", "v1")
AUTHOR_SCORE_WEIGHTS = {
    "name_similarity": 0.35,
    "institution_similarity": 0.25,
    "publication_overlap": 0.20,
    "coauthor_overlap": 0.10,
    "temporal_compatibility": 0.10,
}



# ── Timeouts ─────────────────────────────────────────────────────
SOURCE_TIMEOUT          = int(os.getenv("SOURCE_TIMEOUT",          "10"))
CACHE_TTL_HOURS         = int(os.getenv("CACHE_TTL_HOURS",         "24"))
SCHOLAR_CACHE_TTL_HOURS = int(os.getenv("SCHOLAR_CACHE_TTL_HOURS", "6"))

# ── Database ─────────────────────────────────────────────────────
_base = Path(__file__).resolve().parent
_authoritative_db = (_base / "academic_search.db").resolve()
_raw_db_url = os.getenv("DATABASE_URL")
if _raw_db_url:
    if _raw_db_url.startswith("sqlite+aiosqlite:///./") or _raw_db_url.startswith("sqlite:///./"):
        _scheme, _rel_path = _raw_db_url.split(":///./", 1)
        DATABASE_URL = f"{_scheme}:///{(_base / _rel_path).resolve()}"
    elif _raw_db_url in ("sqlite+aiosqlite:///academic_search.db", "sqlite:///academic_search.db"):
        DATABASE_URL = f"sqlite+aiosqlite:///{_authoritative_db}"
    else:
        DATABASE_URL = _raw_db_url
else:
    DATABASE_URL = f"sqlite+aiosqlite:///{_authoritative_db}"

# ── API Mailto (polite pool) ──────────────────────────────────────
OPENALEX_MAILTO = os.getenv("OPENALEX_MAILTO", "academic-search@demo.com")
OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY", "")
CROSSREF_MAILTO = os.getenv("CROSSREF_MAILTO", "academic-search@demo.com")

# ── Scraping ─────────────────────────────────────────────────────
ARXIV_DELAY_SECONDS = float(os.getenv("ARXIV_DELAY_SECONDS", "3.0"))
SCHOLAR_DELAY_MIN   = float(os.getenv("SCHOLAR_DELAY_MIN",   "2.0"))
SCHOLAR_DELAY_MAX   = float(os.getenv("SCHOLAR_DELAY_MAX",   "4.0"))

# ── Circuit Breaker ──────────────────────────────────────────────
CIRCUIT_BREAKER_THRESHOLD       = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD",       "5"))
CIRCUIT_BREAKER_TIMEOUT_MINUTES = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT_MINUTES", "15"))

# ── Logging ──────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
