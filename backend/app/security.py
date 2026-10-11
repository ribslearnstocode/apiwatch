"""Validate public HTTP URLs and pin DNS results to prevent private-network access."""
import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

from pydantic import HttpUrl, TypeAdapter, ValidationError

EXAMPLE_ENDPOINTS = {
    "https://jsonplaceholder.typicode.com/posts/1": "JSONPlaceholder",
    "https://api.github.com/zen": "GitHub Zen",
    "https://httpbin.org/status/200": "HTTPBin healthy",
    "https://httpbin.org/status/503": "HTTPBin unavailable",
    "https://dummyjson.com/products/1": "DummyJSON",
}

http_url = TypeAdapter(HttpUrl)


def is_public_address(value: str) -> bool:
    address = ipaddress.ip_address(value)
    if not address.is_global or address.is_multicast or address.is_reserved:
        return False
    if isinstance(address, ipaddress.IPv6Address):
        # Translation/tunnelling addresses can embed destinations that are not public.
        if address.ipv4_mapped or address.sixtofour or address.teredo:
            return False
        if any(address in ipaddress.ip_network(prefix) for prefix in ("64:ff9b::/96", "64:ff9b:1::/48")):
            return False
    return True


def validate_url(value: str) -> str:
    value = value.strip()
    if any(ord(character) < 33 or ord(character) == 127 for character in value) or "\\" in value:
        raise ValueError("URL cannot contain whitespace, control characters, or backslashes.")
    try:
        normalized = str(http_url.validate_python(value))
    except ValidationError:
        raise ValueError("Enter a valid HTTP or HTTPS URL, such as https://api.example.com/health.") from None
    parsed = urlsplit(normalized)
    if len(normalized) > 2048:
        raise ValueError("URL must be at most 2048 characters.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URLs containing a username or password are not supported.")
    if parsed.fragment:
        raise ValueError("Remove the URL fragment (#...) before adding the endpoint.")
    host = parsed.hostname.rstrip(".").lower()
    if "%" in host:
        raise ValueError("Scoped or escaped host addresses are not supported.")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Local and private network endpoints cannot be monitored.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if "." not in host:
            raise ValueError("Use a public hostname, not a local machine name.")
    else:
        if not is_public_address(host):
            raise ValueError("Local, private, and reserved IP addresses cannot be monitored.")
    if parsed.port == 0:
        raise ValueError("The endpoint port must be between 1 and 65535.")
    return normalized


async def resolve_public_ip(host: str, port: int = 443) -> str:
    loop = asyncio.get_running_loop()
    addresses = await asyncio.wait_for(
        loop.getaddrinfo(host, port, type=socket.SOCK_STREAM), timeout=5
    )
    ips = [item[4][0] for item in addresses]
    if not ips or any(not is_public_address(ip) for ip in ips):
        raise ValueError("Endpoint DNS resolved to a non-public address.")
    # Pin the validated address for this request, avoiding a second DNS lookup.
    return next((ip for ip in ips if ":" not in ip), ips[0])


async def pinned_target(url: str):
    parsed = urlsplit(validate_url(url))
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return parsed.hostname, await resolve_public_ip(parsed.hostname, port)
