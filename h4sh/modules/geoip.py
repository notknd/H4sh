"""Approximate, public network geolocation; never device tracking."""
from __future__ import annotations

import socket
from urllib.parse import quote

import aiohttp

from h4sh.core.validation import target_host


async def lookup(target: str) -> dict:
    host = target_host(target)
    try:
        ip = socket.gethostbyname(host)
    except OSError as exc:
        raise ValueError(f"Não foi possível resolver o alvo: {exc}") from exc
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(f"https://ipapi.co/{quote(ip)}/json/", headers={"User-Agent": "H4sh/0.2 (authorized diagnostics)"}) as response:
            if response.status != 200:
                raise RuntimeError(f"Provedor Geo IP indisponível (HTTP {response.status}).")
            raw = await response.json()
    if raw.get("error"):
        raise RuntimeError(raw.get("reason", "Consulta Geo IP indisponível."))
    latitude, longitude = raw.get("latitude"), raw.get("longitude")
    map_url = None
    if latitude is not None and longitude is not None:
        map_url = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=10/{latitude}/{longitude}"
    return {
        "target": host,
        "ip": ip,
        "approximate": True,
        "country": raw.get("country_name"),
        "region": raw.get("region"),
        "city": raw.get("city"),
        "timezone": raw.get("timezone"),
        "asn": raw.get("asn"),
        "organization": raw.get("org"),
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "map_url": map_url,
        "source": "ipapi.co (approximate IP geolocation)",
    }
