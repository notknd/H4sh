"""Strict input parsing; no user value is ever evaluated by a shell."""
from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

HOSTNAME = re.compile(r"(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def target_host(value: str) -> str:
    candidate = value.strip().rstrip(".")
    if not candidate or len(candidate) > 253:
        raise ValueError("Informe um IP ou hostname válido.")
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        if not HOSTNAME.fullmatch(candidate):
            raise ValueError("Hostname inválido. Não use URLs, portas ou comandos aqui.")
        return candidate.lower()


def web_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Informe uma URL HTTP(S) válida, sem credenciais.")
    target_host(parsed.hostname)
    if parsed.port and not 1 <= parsed.port <= 65535:
        raise ValueError("Porta inválida.")
    return parsed.geturl()
