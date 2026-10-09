"""Public-entity discovery via Wikidata, not private-person identification."""
from __future__ import annotations

import aiohttp


async def search(name: str) -> dict:
    query = " ".join(name.split())
    if len(query) < 2 or len(query) > 100:
        raise ValueError("Informe entre 2 e 100 caracteres para a entidade pública.")
    params = {"action": "wbsearchentities", "search": query, "language": "pt", "format": "json", "limit": "10", "origin": "*"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=12)) as session:
        async with session.get("https://www.wikidata.org/w/api.php", params=params, headers={"User-Agent": "H4sh/0.2 public-entity lookup"}) as response:
            if response.status != 200:
                raise RuntimeError(f"Wikidata indisponível (HTTP {response.status}).")
            raw = await response.json()
    results = [{"id": item.get("id"), "label": item.get("label"), "description": item.get("description"), "url": item.get("concepturi")} for item in raw.get("search", [])]
    return {"query": query, "results": results, "source": "Wikidata public entities", "notice": "Resultados são candidatos públicos e não confirmam a identidade de uma pessoa privada."}
