import asyncio
import socket
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from app import security
from app.services import monitors, monitoring


@pytest.mark.parametrize("url", [
    "https://api.example.com/health?version=2",
    "http://api.example.com:8080/v1/status",
    "https://[2606:4700:4700::1111]/health",
])
def test_register_custom_public_endpoint(client, url):
    response = client.post("/api/monitors", json={"name": "Custom API", "url": url})
    assert response.status_code == 201, response.text
    assert response.json()["url"] == url
    monitors.pinned_target.assert_awaited_once_with(url)


@pytest.mark.parametrize("url", [
    "ftp://example.com/health", "http://192.168.1.20/health", "http://172.16.1.1/",
    "http://0.0.0.0/", "http://2130706433/", "http://0x7f000001/",
    "http://[::ffff:127.0.0.1]/", "http://[fe80::1]/", "http://[ff02::1]/",
    "http://[64:ff9b::a00:1]/", "http://224.0.0.1/", "http://service.local/",
    "https://user:password@example.com/", "https://example.com:0/",
    "https://example.com:99999/", "https://example.com/with\nnewline",
])
def test_unsafe_custom_endpoint_rejected(client, url):
    assert client.post("/api/monitors", json={"name": "Invalid", "url": url}).status_code == 422
    assert client.get("/api/monitors").json() == []


@pytest.mark.parametrize("error", [ValueError("Endpoint DNS resolved to a non-public address."),
                                 socket.gaierror("not found"), TimeoutError()])
def test_registration_dns_failures(client, monkeypatch, error):
    monkeypatch.setattr(monitors, "pinned_target", AsyncMock(side_effect=error))
    response = client.post("/api/monitors", json={"name": "Custom", "url": "https://api.example.com/health"})
    assert response.status_code == 422
    assert client.get("/api/monitors").json() == []


def test_dns_rebinding_never_connects(client, monkeypatch):
    monkeypatch.setattr(monitors, "pinned_target", security.pinned_target)
    resolver = AsyncMock(side_effect=["93.184.216.34", ValueError("Endpoint DNS resolved to a non-public address.")])
    monkeypatch.setattr(security, "resolve_public_ip", resolver)
    http_client = Mock()
    monkeypatch.setattr(monitoring.httpx, "AsyncClient", http_client)
    created = client.post("/api/monitors", json={"name": "Rebinding", "url": "https://api.example.com/health"})
    assert created.status_code == 201
    checked = client.post(f'/api/monitors/{created.json()["id"]}/check').json()
    assert checked["is_success"] is False
    assert "non-public" in checked["error_message"]
    assert resolver.await_count == 2
    http_client.assert_not_called()


def test_mixed_public_private_dns_rejected(monkeypatch):
    async def run():
        loop = asyncio.get_running_loop()
        monkeypatch.setattr(loop, "getaddrinfo", AsyncMock(return_value=[
            (2, 1, 6, "", ("93.184.216.34", 443)), (2, 1, 6, "", ("10.0.0.1", 443))]))
        with pytest.raises(ValueError, match="non-public"):
            await security.resolve_public_ip("api.example.com")
    asyncio.run(run())


def test_custom_port_and_query_preserved(monkeypatch):
    def respond(request):
        assert request.url == httpx.URL("http://93.184.216.34:8080/health?version=2")
        assert request.headers["Host"] == "api.example.com:8080"
        assert request.extensions["sni_hostname"] == "api.example.com"
        return httpx.Response(200)

    monkeypatch.setattr(security, "resolve_public_ip", AsyncMock(return_value="93.184.216.34"))
    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs))
    result = asyncio.run(monitoring.probe("http://api.example.com:8080/health?version=2"))
    assert result[0] == 200 and result[2] is None
    security.resolve_public_ip.assert_awaited_once_with("api.example.com", 8080)
