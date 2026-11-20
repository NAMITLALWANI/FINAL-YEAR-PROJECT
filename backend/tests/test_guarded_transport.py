"""T017: tests of the extra capture stop conditions (cost stop level, consecutive failures). Synthetic transports only; no network."""
import asyncio
import json

import httpx
import pytest

from hammer_pilot.capture import RecordingTransport
from hammer_pilot.guarded_transport import GuardStop, GuardedTransport


def mock(handler):
    return httpx.MockTransport(handler)


def run(coro):
    return asyncio.run(coro)


async def fetch(transport, n):
    async with httpx.AsyncClient(transport=transport) as c:
        return [(await c.get(f"https://api.openalex.org/authors?q={i}")).status_code for i in range(n)]


def test_cost_stop_fires_before_the_next_request():
    seen = []
    def h(req):
        seen.append(1)
        return httpx.Response(200, json={"results": [], "meta": {"cost_usd": 0.3}})
    g = GuardedTransport(mock(h), cost_ceiling_usd=1.0, stop_fraction=0.5)
    with pytest.raises(GuardStop) as e:
        run(fetch(g, 5))
    assert e.value.reason == "cost_ceiling" and len(seen) == 2 and abs(g.spent - 0.6) < 1e-9     # 0.3 < 0.5 so a second request is made; 0.6 >= 0.5 then stops


def test_no_ceiling_means_no_cost_stop():
    g = GuardedTransport(mock(lambda r: httpx.Response(200, json={"meta": {"cost_usd": 5}})), cost_ceiling_usd=None)
    assert run(fetch(g, 4)) == [200] * 4


def test_three_consecutive_5xx_stop_and_success_resets():
    codes = iter([500, 502, 200, 503, 500, 504, 200])
    g = GuardedTransport(mock(lambda r: httpx.Response(next(codes), json={})), cost_ceiling_usd=None, max_consecutive_failures=3)
    with pytest.raises(GuardStop) as e:
        run(fetch(g, 7))
    assert e.value.reason == "consecutive_failures" and g.requests == 6     # 500,502,200(reset),503,500,504 -> stop before the 7th


def test_transport_errors_count_as_failures():
    def h(req):
        raise httpx.ConnectError("down", request=req)
    g = GuardedTransport(mock(h), cost_ceiling_usd=None, max_consecutive_failures=2)
    async def go():
        async with httpx.AsyncClient(transport=g) as c:
            for i in range(5):
                try:
                    await c.get(f"https://api.openalex.org/x?i={i}")
                except httpx.ConnectError:
                    pass
    with pytest.raises(GuardStop):
        run(go())
    assert g.requests == 2


def test_4xx_is_not_a_server_failure():
    g = GuardedTransport(mock(lambda r: httpx.Response(404, json={})), cost_ceiling_usd=None, max_consecutive_failures=1)
    assert run(fetch(g, 3)) == [404] * 3


def test_failing_response_is_saved_before_the_stop(tmp_path):
    inner = GuardedTransport(mock(lambda r: httpx.Response(500, json={"error": "x"})), cost_ceiling_usd=None, max_consecutive_failures=2)
    rec = RecordingTransport(inner, tmp_path, budget=50)
    (tmp_path / "bodies").mkdir()
    async def go():
        async with httpx.AsyncClient(transport=rec) as c:
            for i in range(5):
                await c.get(f"https://api.openalex.org/authors?i={i}")
    with pytest.raises(GuardStop):
        run(go())
    lines = [json.loads(l) for l in (tmp_path / "capture_index.jsonl").read_text().splitlines()]
    assert len(lines) == 2 and all(l["status"] == 500 and l["sha256"] for l in lines)


def test_bad_settings_refused():
    with pytest.raises(ValueError):
        GuardedTransport(mock(lambda r: None), cost_ceiling_usd=0)
    with pytest.raises(ValueError):
        GuardedTransport(mock(lambda r: None), cost_ceiling_usd=1, stop_fraction=1.5)
    with pytest.raises(ValueError):
        GuardedTransport(mock(lambda r: None), cost_ceiling_usd=1, max_consecutive_failures=0)


def test_compressed_responses_survive_the_guard(tmp_path):
    """T019 regression: a gzip-encoded wire response must come out decoded exactly once (the real provider compresses; plain mocks did not)."""
    import gzip
    payload = json.dumps({"results": [{"id": "A1"}], "meta": {"cost_usd": 0.001}}).encode()
    def h(req):
        return httpx.Response(200, content=gzip.compress(payload), headers={"content-encoding": "gzip", "content-type": "application/json"})
    g = GuardedTransport(mock(h), cost_ceiling_usd=1.0)
    rec = RecordingTransport(g, tmp_path, budget=5)
    (tmp_path / "bodies").mkdir()
    async def go():
        async with httpx.AsyncClient(transport=rec) as c:
            r = await c.get("https://api.openalex.org/authors?x=1")
            return r.json()
    assert run(go())["results"][0]["id"] == "A1"
    assert abs(g.spent - 0.001) < 1e-9
    entry = json.loads((tmp_path / "capture_index.jsonl").read_text().splitlines()[0])
    assert entry["status"] == 200 and entry["json_valid"] is True
