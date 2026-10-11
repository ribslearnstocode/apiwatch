import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import func, select

from app import security
from app.services import monitoring
from app.scheduler import scheduled_tick
from app.models import Incident, MonitorResult, utcnow


def test_crud(client, monitor):
    monitor_id = monitor["id"]
    assert client.get("/api/monitors").json()[0]["id"] == monitor_id
    assert client.get(f"/api/monitors/{monitor_id}").status_code == 200
    payload = {**monitor, "name": "Renamed API", "is_active": False}
    updated = client.put(f"/api/monitors/{monitor_id}", json=payload)
    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed API"
    assert client.post(f"/api/monitors/{monitor_id}/check").status_code == 409
    assert client.delete(f"/api/monitors/{monitor_id}").status_code == 204
    assert client.get(f"/api/monitors/{monitor_id}").status_code == 404


@pytest.mark.parametrize("url", ["file:///etc/passwd", "http://localhost", "http://127.0.0.1", "http://10.0.0.1",
                                  "https://httpbin.org@127.0.0.1", "http://[::1]/health",
                                  "https://httpbin.org/status/200#fragment", "http://169.254.169.254"])
def test_unsafe_url_rejected(client, url):
    assert client.post("/api/monitors", json={"name": "Unsafe", "url": url}).status_code == 422


def test_duplicate_and_validation(client, monitor):
    assert client.post("/api/monitors", json=monitor).status_code == 409
    assert client.post("/api/monitors", json={**monitor, "check_interval": 1}).status_code == 422
    assert client.post("/api/monitors", json={**monitor, "name": "  "}).status_code == 422
    assert client.get("/api/dashboard/summary?hours=0").status_code == 422


def test_empty_analytics(client):
    data = client.get("/api/dashboard/summary").json()
    assert data["total_monitors"] == 0
    assert data["average_response_time"] is None


def test_not_yet_checked(client, monitor):
    data = client.get(f'/api/monitors/{monitor["id"]}/analytics').json()
    assert data["status"] == "not_yet_checked"
    assert data["uptime_percentage"] is None


def test_incident_lifecycle_and_analytics(client, monitor, db, monkeypatch):
    probe = AsyncMock(side_effect=[(200, 100, None), (503, 300, "HTTP 503"), (503, 200, "HTTP 503"), (200, 200, None)])
    monkeypatch.setattr(monitoring, "probe", probe)
    path = f'/api/monitors/{monitor["id"]}'
    for _ in range(3):
        assert client.post(path + "/check").status_code == 200
    incidents = client.get(path + "/incidents").json()
    assert len(incidents) == 1 and incidents[0]["resolved_at"] is None
    assert client.get(path + "/analytics").json()["status"] == "unhealthy"
    assert client.post(path + "/check").json()["is_success"]
    assert client.get(path + "/incidents").json()[0]["resolved_at"] is not None
    stats = client.get(path + "/analytics").json()
    assert stats["uptime_percentage"] == 50
    assert stats["avg_response_time"] == 200
    assert stats["min_response_time"] == 100
    assert stats["max_response_time"] == 300
    assert stats["incident_count"] == 1
    assert stats["successful_checks"] == stats["failed_checks"] == 2
    assert len(client.get(path + "/results?limit=2&offset=1").json()) == 2
    assert client.delete(path).status_code == 204
    assert db.scalar(select(func.count(MonitorResult.id))) == 0
    assert db.scalar(select(func.count(Incident.id))) == 0


def test_first_failure_opens_incident(client, monitor, monkeypatch):
    monkeypatch.setattr(monitoring, "probe", AsyncMock(return_value=(None, 10000, "Request timed out")))
    path = f'/api/monitors/{monitor["id"]}'
    assert client.post(path + "/check").json()["error_message"] == "Request timed out"
    assert len(client.get(path + "/incidents").json()) == 1


def test_duplicate_check_and_edits_blocked(client, monitor):
    monitoring.running_checks.add(monitor["id"])
    path = f'/api/monitors/{monitor["id"]}'
    assert client.post(path + "/check").status_code == 409
    assert client.put(path, json=monitor).status_code == 409
    assert client.delete(path).status_code == 409


@pytest.mark.parametrize("status,error", [(204, None), (503, "HTTP 503"), (302, "HTTP 302; redirects are disabled")])
def test_http_probe(monkeypatch, status, error):
    requests = []

    def respond(request):
        requests.append(request)
        assert request.url.host == "93.184.216.34"
        assert request.headers["Host"] == "httpbin.org"
        assert request.extensions["sni_hostname"] == "httpbin.org"
        return httpx.Response(status, headers={"Location": "http://127.0.0.1"})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(monitoring, "pinned_target", AsyncMock(return_value=("httpbin.org", "93.184.216.34")))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs))
    result = asyncio.run(monitoring.probe("https://httpbin.org/status/200"))
    assert result[0] == status and result[2] == error
    assert len(requests) == 1


def test_timeout_probe(monkeypatch):
    def timeout(request):
        raise httpx.ReadTimeout("timeout")
    real_client = httpx.AsyncClient
    monkeypatch.setattr(monitoring, "pinned_target", AsyncMock(return_value=("httpbin.org", "93.184.216.34")))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(timeout), **kwargs))
    assert asyncio.run(monitoring.probe("https://httpbin.org/status/200"))[2] == "Request timed out"


def test_private_dns_rejected(monkeypatch):
    async def run():
        loop = asyncio.get_running_loop()
        monkeypatch.setattr(loop, "getaddrinfo", AsyncMock(return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]))
        with pytest.raises(ValueError, match="non-public"):
            await security.resolve_public_ip("httpbin.org")
    asyncio.run(run())


def test_scheduler_due_and_paused(client, monitor, monkeypatch):
    probe = AsyncMock(return_value=(200, 50, None))
    monkeypatch.setattr(monitoring, "probe", probe)
    asyncio.run(scheduled_tick())
    asyncio.run(scheduled_tick())
    assert probe.await_count == 1
    client.put(f'/api/monitors/{monitor["id"]}', json={**monitor, "is_active": False})
    asyncio.run(scheduled_tick())
    assert probe.await_count == 1


def test_time_window_and_current_status(client, monitor, db):
    db.add(MonitorResult(monitor_id=monitor["id"], status_code=200, response_time_ms=100,
                         is_success=True, checked_at=utcnow() - timedelta(hours=48)))
    db.commit()
    stats = client.get(f'/api/monitors/{monitor["id"]}/analytics?hours=24').json()
    assert stats["total_checks"] == 0 and stats["status"] == "healthy"
    assert client.get(f'/api/monitors/{monitor["id"]}/analytics?hours=168').json()["total_checks"] == 1
