from __future__ import annotations

from h4sh.core.executor import run
from h4sh.core.validation import target_host

PROFILES = {
    "Fast scan": ["-T3", "--top-ports", "100", "-sV"],
    "Service detection": ["-T3", "-sV", "--version-light"],
    "Full TCP ports": ["-T3", "-p-", "--open"],
}


async def scan(target: str, profile: str) -> dict:
    host = target_host(target)
    if profile not in PROFILES:
        raise ValueError("Perfil de varredura desconhecido.")
    # `--` protects the target position; validated profile flags remain options.
    result = await run(["nmap", *PROFILES[profile], "--", host], timeout=300)
    return {"profile": profile, "returncode": result.returncode, "output": result.stdout, "warnings": result.stderr}
