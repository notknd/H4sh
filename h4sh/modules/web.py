from __future__ import annotations

import asyncio
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

import aiohttp

from h4sh.core.validation import web_url

SECURITY_HEADERS = ("strict-transport-security", "content-security-policy", "x-frame-options", "x-content-type-options", "referrer-policy")


async def audit(raw_url: str) -> dict:
    url = web_url(raw_url)
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, allow_redirects=True, headers={"User-Agent": "H4sh/0.1 security posture check"}) as response:
            headers = {key.lower(): value for key, value in response.headers.items()}
            result = {"requested_url": url, "final_url": str(response.url), "status": response.status, "server": headers.get("server", "not disclosed"), "technologies": {key: headers[key] for key in ("server", "x-powered-by", "via") if key in headers}, "security_headers": {key: headers.get(key, "missing") for key in SECURITY_HEADERS}}
    parsed = urlparse(url)
    if parsed.scheme == "https":
        result["tls"] = await asyncio.to_thread(_certificate, parsed.hostname, parsed.port or 443)
    return result


def _certificate(host: str, port: int) -> dict:
    context = ssl.create_default_context()
    with context.wrap_socket(__import__("socket").create_connection((host, port), timeout=10), server_hostname=host) as sock:
        cert = sock.getpeercert()
        expiry = cert.get("notAfter", "")
        return {"protocol": sock.version(), "cipher": sock.cipher()[0], "issuer": dict(x[0] for x in cert.get("issuer", ())), "expires": expiry, "checked_at": datetime.now(timezone.utc).isoformat()}
