"""Limita quantas perguntas a API aceita, por IP e no total, em janelas móveis.

A API é pública (Tailscale Funnel) e cada pergunta paga o guardrail e a resposta no provedor.
O CORS só barra navegadores; um script chama a API à vontade. As contagens ficam em memória
(um processo só) e zeram quando o serviço reinicia: isto segura rajadas, e o teto de gasto
fica nas contas dos provedores.
"""

import logging
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

MINUTE_S = 60.0
DAY_S = 24 * 60 * 60.0

QuestionLimitName = Literal["ip_por_minuto", "ip_por_dia", "global_por_dia"]


@dataclass(frozen=True)
class QuestionRateLimitDecision:
    allowed: bool
    limit: QuestionLimitName | None = None
    retry_after_s: int = 0


def seconds_until_free_slot(accepted_at: deque[float], now: float, window_s: float, limit: int) -> float | None:
    """None se a janela ainda tem vaga; senão, quanto falta para a vaga mais antiga sair dela.

    `accepted_at` está em ordem crescente e pode guardar mais instantes que esta janela cobre.
    """
    if limit <= 0:
        return window_s
    in_window = 0
    for instant in reversed(accepted_at):
        if now - instant >= window_s:
            break
        in_window += 1
    if in_window < limit:
        return None
    oldest_counted = accepted_at[len(accepted_at) - limit]
    return window_s - (now - oldest_counted)


def drop_older_than(accepted_at: deque[float], now: float, window_s: float) -> None:
    while accepted_at and now - accepted_at[0] >= window_s:
        accepted_at.popleft()


class QuestionRateLimiter:
    def __init__(
        self,
        *,
        per_ip_per_minute: int,
        per_ip_per_day: int,
        global_per_day: int,
        max_tracked_ips: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._per_ip_per_minute = per_ip_per_minute
        self._per_ip_per_day = per_ip_per_day
        self._global_per_day = global_per_day
        self._max_tracked_ips = max_tracked_ips
        self._clock = clock
        # LRU: o IP usado há mais tempo sai primeiro quando o teto de IPs enche. Esquecer um
        # IP zera a conta dele, mas o teto global continua valendo.
        self._accepted_by_ip: OrderedDict[str, deque[float]] = OrderedDict()
        self._accepted_global: deque[float] = deque()

    def check_and_record(self, client_ip: str) -> QuestionRateLimitDecision:
        now = self._clock()
        drop_older_than(self._accepted_global, now, DAY_S)
        ip_accepted = self._accepted_by_ip.get(client_ip, deque())
        drop_older_than(ip_accepted, now, DAY_S)

        checks: list[tuple[QuestionLimitName, deque[float], float, int]] = [
            ("ip_por_minuto", ip_accepted, MINUTE_S, self._per_ip_per_minute),
            ("ip_por_dia", ip_accepted, DAY_S, self._per_ip_per_day),
            ("global_por_dia", self._accepted_global, DAY_S, self._global_per_day),
        ]
        for name, accepted_at, window_s, limit in checks:
            wait_s = seconds_until_free_slot(accepted_at, now, window_s, limit)
            if wait_s is not None:
                logger.warning("limite de perguntas: %s ip=%s limite=%d espera=%.0fs", name, client_ip, limit, wait_s)
                return QuestionRateLimitDecision(False, name, max(1, round(wait_s)))

        ip_accepted.append(now)
        self._accepted_global.append(now)
        self._remember(client_ip, ip_accepted)
        return QuestionRateLimitDecision(True)

    def _remember(self, client_ip: str, ip_accepted: deque[float]) -> None:
        self._accepted_by_ip[client_ip] = ip_accepted
        self._accepted_by_ip.move_to_end(client_ip)
        while len(self._accepted_by_ip) > self._max_tracked_ips:
            self._accepted_by_ip.popitem(last=False)


def wait_text(seconds: int) -> str:
    """Tempo de espera em pt-BR para a mensagem de 429."""
    if seconds < 60:
        return _plural(seconds, "segundo")
    if seconds < 60 * 60:
        return _plural(-(-seconds // 60), "minuto")
    return _plural(-(-seconds // 3600), "hora")


def _plural(count: int, unit: str) -> str:
    return f"{count} {unit}" if count == 1 else f"{count} {unit}s"
