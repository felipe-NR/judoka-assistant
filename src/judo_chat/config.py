from datetime import time
from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JUDO_CHAT_", env_file=".env", extra="ignore", frozen=True)

    data_dir: Path = _ROOT / "data"
    provider: Literal["anthropic", "openai"] = "anthropic"
    guardrail_model: str = "claude-haiku-5-5"
    # O pensamento do Haiku 5.5 vem ligado e conta no max_tokens: com 300 a classificação
    # podia acabar antes do JSON.
    guardrail_effort: Literal["low", "medium", "high"] = "low"
    guardrail_max_tokens: int = 1024
    # Só na OpenAI: "decisions" classifica pela Decisions API (paga só a entrada, devolve
    # probabilidades). Bloqueia se P(fora), P(pedido de agressão) ou P(pedido para mudar as
    # instruções) passar do limite.
    guardrail_api: Literal["responses", "decisions"] = "responses"
    guardrail_fora_threshold: float = 0.5
    guardrail_harm_threshold: float = 0.5
    guardrail_instructions_threshold: float = 0.5
    # Haiku 5.5: o modelo mais barato disponível (US$ 0,10/M de entrada e US$ 0,50/M de saída
    # com prompt de até 100 mil tokens). Para mais qualidade, use claude-sonnet-5-5 com
    # JUDO_CHAT_ANSWER_EFFORT=low e JUDO_CHAT_USE_REFUSAL_FALLBACKS=true.
    answer_model: str = "claude-haiku-5-5"
    # O effort faz parte do prefixo cacheado; None não envia o parâmetro (o Haiku 4.5 o rejeita).
    # Sem ele o Haiku 5.5 usa medium.
    answer_effort: Literal["low", "medium", "high"] | None = "low"
    # Cabe o pensamento além da resposta.
    answer_max_tokens: int = 8000
    guardrail_timeout_s: float = 15.0
    answer_timeout_s: float = 90.0
    # 1h combinado com o re-aquecimento: grava 1 vez por dia (2x o preço de entrada) e lê a
    # cada ~55 min parado (0,1x). Com 5 min seriam ~13 re-aquecimentos por hora.
    cache_ttl: Literal["5m", "1h"] = "1h"
    # Só na OpenAI (gpt-5.6 em diante): tempo mínimo do prefixo no cache. O padrão da API é
    # 30m, e cada expiração regrava o corpus (1,25x o preço de entrada). 12h grava a 2,5x,
    # uma vez para o dia inteiro. O SDK 3.37 ainda tipa só "30m"; a documentação aceita "12h".
    openai_cache_ttl: Literal["30m", "12h"] = "12h"
    keepalive_enabled: bool = True
    # Abaixo dos 60 min do TTL, com folga para a checagem que roda a cada minuto.
    keepalive_interval_s: float = 55 * 60
    keepalive_window_start: time = time(7, 0)
    keepalive_window_end: time = time(23, 0)
    keepalive_timezone: str = "America/Sao_Paulo"
    # Retry server-side num modelo alternativo quando o modelo recusa por política. Só vale
    # para o Sonnet 5.5 e o Opus 5.5; o Haiku não tem fallback no servidor.
    use_refusal_fallbacks: bool = False
    # Origens que podem chamar a API pelo navegador (a página no GitHub Pages).
    cors_origins: tuple[str, ...] = ("https://felipe-nr.github.io",)
    # Em produção a página fica só no GitHub Pages. Servida pela API, ela pergunta à própria
    # origem e não passa pelo CORS; em 2026-10-23 robôs a abriram 19 vezes em 10 minutos.
    serve_chat_page: bool = True
    # Limites de perguntas (src/judo_chat/question_rate_limit.py), em janelas móveis. Uma
    # pessoa lê cada resposta por mais de 10 s, e IPs de rede móvel (CGNAT) e de academia são
    # compartilhados. O global corta abuso espalhado por muitos IPs.
    question_limit_per_ip_per_minute: int = 8
    question_limit_per_ip_per_day: int = 80
    question_limit_global_per_day: int = 1000
    # Cada IP guarda no máximo question_limit_per_ip_per_day instantes; a micro tem 1 GB.
    question_limit_max_tracked_ips: int = 5000
    # Países (ISO 3166-1) que recebem 403 em qualquer rota: quase todo acesso de lá é bot de
    # datacenter (PR #15, 2026-10-23). Vazio desliga o bloqueio. A base sai de
    # scripts/update_geoip.py.
    blocked_countries: tuple[str, ...] = ("SG", "PK", "CN", "IN")
    geoip_db: Path = _ROOT / ".geoip" / "dbip-country-lite.mmdb"

    @model_validator(mode="after")
    def _fallbacks_need_a_supported_model(self) -> Self:
        if self.provider == "openai":
            if self.guardrail_model == "claude-haiku-5-5":
                object.__setattr__(self, "guardrail_model", "gpt-6-luna")
            if self.answer_model == "claude-haiku-5-5":
                object.__setattr__(self, "answer_model", "gpt-6-luna")
        if self.provider != "openai" and self.guardrail_api == "decisions":
            raise ValueError("JUDO_CHAT_GUARDRAIL_API=decisions só vale para a OpenAI")
        if self.provider == "openai" and self.use_refusal_fallbacks:
            raise ValueError("JUDO_CHAT_USE_REFUSAL_FALLBACKS só vale para a Anthropic")
        if self.use_refusal_fallbacks and self.answer_model.startswith("claude-haiku"):
            raise ValueError("JUDO_CHAT_USE_REFUSAL_FALLBACKS não vale para o Haiku, que não tem fallback no servidor")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
