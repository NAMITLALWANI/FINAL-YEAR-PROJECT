import asyncio
import time
from abc import ABC, abstractmethod
from log_config import get_logger, log_source_fetch, log_source_error
from config import SOURCE_TIMEOUT

logger = get_logger(__name__)


class BaseConnector(ABC):
    """
    All connectors inherit from this.
    Provides: timeout wrapping, structured logging, uniform return shape.
    """
    source_name: str = "base"
    timeout: int = SOURCE_TIMEOUT

    async def fetch(self, author_name: str, **kwargs) -> tuple[list[dict], dict]:
        """
        Returns (records: list[dict], status: dict).
        Never raises — failures are captured in status.
        """
        start = time.monotonic()
        try:
            records = await asyncio.wait_for(
                self._fetch_impl(author_name, **kwargs),
                timeout=self.timeout,
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            log_source_fetch(logger, self.source_name, len(records), elapsed_ms, author_name)
            return records, {
                "status":   "ok",
                "records":  len(records),
                "time_ms":  round(elapsed_ms),
            }
        except asyncio.TimeoutError:
            log_source_error(logger, self.source_name, "timeout", author_name)
            return [], {"status": "failed", "reason": "timeout"}
        except Exception as exc:
            log_source_error(logger, self.source_name, str(exc), author_name)
            return [], {"status": "failed", "reason": str(exc)}

    @abstractmethod
    async def _fetch_impl(self, author_name: str, **kwargs) -> list[dict]:
        """Subclasses implement the actual fetch logic here."""
        ...
