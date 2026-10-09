from __future__ import annotations

import asyncio
import socket

import aiohttp
import dns.asyncresolver

from h4sh.core.validation import target_host


async def lookup(target: str) -> dict:
    host = target_host(target)
    resolver = dns.asyncresolver.Resolver()
    async def query(record: str) -> list[str]:
        try:
            answer = await resolver.resolve(host, record, lifetime=5)
            return [str(item) for item in answer]
        except Exception:
            return []
    records = await asyncio.gather(*(query(r) for r in ("A", "AAAA", "MX", "TXT", "NS")))
    addresses = records[0] + records[1]
    ip_data: dict = {}
    if addresses:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
                async with session.get(f"https://ipapi.co/{addresses[0]}/json/", headers={"User-Agent": "H4sh/0.1"}) as response:
                    if response.status == 200:
                        data = await response.json()
                        ip_data = {key: data.get(key) for key in ("ip", "city", "region", "country_name", "org", "asn", "latitude", "longitude")}
        except aiohttp.ClientError:
            ip_data = {"notice": "Consulta de IP indisponível."}
    return {"target": host, "resolved_name": await asyncio.to_thread(socket.getfqdn, host), "dns": dict(zip(("A", "AAAA", "MX", "TXT", "NS"), records)), "ip_context": ip_data}
