"""Public registration data for domains and IP networks."""
from __future__ import annotations

import ipaddress

import aiohttp

from h4sh.core.validation import target_host


async def lookup(target: str) -> dict:
    host = target_host(target)
    try:
        ipaddress.ip_address(host)
        endpoint = f"https://rdap.org/ip/{host}"
        kind = "ip"
    except ValueError:
        endpoint = f"https://rdap.org/domain/{host}"
        kind = "domain"
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=12)) as session:
        async with session.get(endpoint, headers={"Accept": "application/rdap+json", "User-Agent": "H4sh/0.2 authorized diagnostics"}) as response:
            if response.status == 404:
                raise ValueError("Nenhum registro RDAP público encontrado.")
            if response.status != 200:
                raise RuntimeError(f"RDAP indisponível (HTTP {response.status}).")
            raw = await response.json()
    return {"target": host, "kind": kind, "handle": raw.get("handle"), "name": raw.get("name"), "status": raw.get("status", []), "country": raw.get("country"), "events": raw.get("events", []), "nameservers": [entry.get("ldhName") for entry in raw.get("nameservers", [])], "source": "rdap.org public registration data"}
