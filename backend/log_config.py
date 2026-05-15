import logging
import json
import sys
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """Emits each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        }
        # Merge any extra dict attached by callers
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload.update(record.extra)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def configure_root(level: str = "INFO") -> None:
    """Call once at app startup."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


# ── Convenience helpers ──────────────────────────────────────────

def log_source_fetch(logger: logging.Logger, source: str, records: int,
                     time_ms: float, author: str) -> None:
    logger.info("source_fetch_complete", extra={"extra": {
        "event":    "source_fetch_complete",
        "source":   source,
        "records":  records,
        "time_ms":  round(time_ms),
        "author":   author,
    }})


def log_source_error(logger: logging.Logger, source: str,
                     reason: str, author: str) -> None:
    logger.warning("source_fetch_failed", extra={"extra": {
        "event":  "source_fetch_failed",
        "source": source,
        "reason": reason,
        "author": author,
    }})
