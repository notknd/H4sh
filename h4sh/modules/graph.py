"""Build a compact, passive relationship graph from public network sources."""
from __future__ import annotations

import asyncio

from h4sh.modules.geoip import lookup as geo_lookup
from h4sh.modules.osint import lookup as dns_lookup
from h4sh.modules.rdap import lookup as rdap_lookup


async def build(target: str) -> dict:
    dns, geo, rdap = await asyncio.gather(dns_lookup(target), geo_lookup(target), rdap_lookup(target), return_exceptions=True)
    nodes: list[dict] = [{"type": "target", "value": target}]
    edges: list[dict] = []
    if isinstance(dns, dict):
        for address in dns.get("dns", {}).get("A", []):
            nodes.append({"type": "ip", "value": address})
            edges.append({"from": target, "relation": "resolves_to", "to": address})
    if isinstance(geo, dict) and geo.get("asn"):
        nodes.append({"type": "asn", "value": geo["asn"]})
        edges.append({"from": geo["ip"], "relation": "announced_by", "to": geo["asn"]})
    if isinstance(rdap, dict) and rdap.get("name"):
        nodes.append({"type": "rdap", "value": rdap["name"]})
        edges.append({"from": target, "relation": "registered_as", "to": rdap["name"]})
    errors = [str(value) for value in (dns, geo, rdap) if isinstance(value, Exception)]
    return {"target": target, "nodes": nodes, "edges": edges, "source_errors": errors, "notice": "Relações passivas derivadas de fontes públicas; confirme antes de tomar decisões."}
