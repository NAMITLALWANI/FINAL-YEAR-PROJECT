"""Extra stop conditions for provider capture (T017): a transport wrapper placed *inside* the recording transport.

It stops the run before the next request when (a) the provider-reported cost (`meta.cost_usd`, summed) has reached a fraction of the cost ceiling, or (b) a given
number of consecutive requests ended in a server error (HTTP 5xx) or a transport error. The failing response itself has already been saved and hashed by the
recording transport; stopping happens before anything further is requested. Cached (already captured) requests never reach this wrapper.
"""
from __future__ import annotations

import json

import httpx


class GuardStop(RuntimeError):
    """A pre-declared stop condition fired. `reason` is one of cost_ceiling, consecutive_failures."""

    def __init__(self, reason: str, detail: str):
        super().__init__(f"capture stopped: {reason} ({detail})")
        self.reason = reason


class GuardedTransport(httpx.AsyncBaseTransport):
    def __init__(self, inner: httpx.AsyncBaseTransport, *, cost_ceiling_usd: float | None, stop_fraction: float = 0.8, max_consecutive_failures: int = 3):
        if cost_ceiling_usd is not None and cost_ceiling_usd <= 0:
            raise ValueError("cost ceiling must be positive")
        if not 0 < stop_fraction <= 1 or max_consecutive_failures < 1:
            raise ValueError("invalid guard settings")
        self.inner = inner
        self.limit = None if cost_ceiling_usd is None else cost_ceiling_usd * stop_fraction
        self.max_failures = max_consecutive_failures
        self.spent = 0.0
        self.consecutive_failures = 0
        self.requests = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if self.consecutive_failures >= self.max_failures:
            raise GuardStop("consecutive_failures", f"{self.consecutive_failures} in a row")
        if self.limit is not None and self.spent >= self.limit:
            raise GuardStop("cost_ceiling", f"spent {self.spent:.4f} of the {self.limit:.4f} stop level")
        self.requests += 1
        try:
            response = await self.inner.handle_async_request(request)
            body = await response.aread()
        except httpx.HTTPError:
            self.consecutive_failures += 1
            raise
        if response.status_code >= 500:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        try:
            cost = json.loads(body).get("meta", {}).get("cost_usd")
            if isinstance(cost, (int, float)) and not isinstance(cost, bool):
                self.spent += float(cost)
        except (ValueError, AttributeError):
            pass
        # `aread()` returns the decoded body, so the encoding and length headers of the wire response no longer describe it (T019: leaving them made every
        # real response fail with a DecodingError, which mock transports without compression could not show).
        headers = [(k, v) for k, v in response.headers.multi_items() if k.lower() not in ("content-encoding", "content-length", "transfer-encoding")]
        return httpx.Response(response.status_code, content=body, headers=headers, request=request)
