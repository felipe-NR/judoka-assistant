"""Bloqueio por país do IP de origem, contra o tráfego de bots que gasta tokens no /api/perguntar.

O IP vem de request.client: atrás de um proxy, o uvicorn o tira do X-Forwarded-For quando o
proxy conecta de um IP em --forwarded-allow-ips (só 127.0.0.1 por padrão). IPs fora da base,
como os locais, passam.
"""

import logging
from collections.abc import Awaitable, Callable, Iterable
from pathlib import Path

import maxminddb
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

BLOCKED_MESSAGE = "O assistente não está disponível na sua região."

CountryLookup = Callable[[str], str | None]


class CountryDatabase:
    """Lê o código ISO do país numa base MMDB (DB-IP Lite ou GeoLite2-Country)."""

    def __init__(self, path: Path) -> None:
        self._reader = maxminddb.open_database(path)

    def __call__(self, ip: str) -> str | None:
        try:
            record = self._reader.get(ip)
        except ValueError:
            return None
        if not isinstance(record, dict):
            return None
        country = record.get("country")
        if not isinstance(country, dict):
            return None
        code = country.get("iso_code")
        return code if isinstance(code, str) else None


def open_country_database(path: Path) -> CountryDatabase | None:
    if not path.is_file():
        logger.warning("base de países ausente em %s: bloqueio por país desligado (scripts/update_geoip.py)", path)
        return None
    return CountryDatabase(path)


class GeoBlockMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, lookup: CountryLookup, blocked: Iterable[str]) -> None:
        super().__init__(app)
        self._lookup = lookup
        self._blocked = frozenset(code.upper() for code in blocked)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.client is not None:
            country = self._lookup(request.client.host)
            if country in self._blocked:
                logger.info("bloqueado por país: %s %s %s", country, request.client.host, request.url.path)
                return JSONResponse(status_code=403, content={"detail": BLOCKED_MESSAGE})
        return await call_next(request)
