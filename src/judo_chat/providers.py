"""Criação dos provedores de modelo suportados pela aplicação."""

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Protocol

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from judo_chat.answer import Answer, Answerer, Turn
from judo_chat.config import Settings
from judo_chat.corpus.models import Corpus
from judo_chat.guardrail import Guardrail, GuardrailResult
from judo_chat.normalizer import Match, Recognizer
from judo_chat.openai_provider import OpenAIAnswerer, OpenAIDecisionsGuardrail, OpenAIGuardrail
from judo_chat.relations import Relations


class GuardrailProvider(Protocol):
    async def classify(
        self, query: str, history: Sequence[str] = (), techniques: Sequence[str] = (), terms: Sequence[str] = ()
    ) -> GuardrailResult: ...


class AnswerProvider(Protocol):
    last_cache_touch: float | None

    async def answer(self, query: str, matches: list[Match], history: Sequence[Turn] = ()) -> Answer: ...

    async def keep_alive(self) -> tuple[int, int]: ...


@dataclass(frozen=True)
class Providers:
    guardrail: GuardrailProvider
    answerer: AnswerProvider


@asynccontextmanager
async def create_providers(settings: Settings, corpus: Corpus, recognizer: Recognizer) -> AsyncIterator[Providers]:
    relations = Relations(corpus, recognizer)
    if settings.provider == "anthropic":
        async with AsyncAnthropic() as client:
            yield Providers(
                guardrail=Guardrail(
                    client,
                    settings.guardrail_model,
                    settings.guardrail_timeout_s,
                    effort=settings.guardrail_effort,
                    max_tokens=settings.guardrail_max_tokens,
                ),
                answerer=Answerer(client, settings, corpus, relations),
            )
        return
    async with AsyncOpenAI() as client:
        guardrail: GuardrailProvider
        if settings.guardrail_api == "decisions":
            guardrail = OpenAIDecisionsGuardrail(
                client,
                settings.guardrail_model,
                settings.guardrail_timeout_s,
                fora_threshold=settings.guardrail_fora_threshold,
                harm_threshold=settings.guardrail_harm_threshold,
            )
        else:
            guardrail = OpenAIGuardrail(
                client,
                settings.guardrail_model,
                settings.guardrail_timeout_s,
                effort=settings.guardrail_effort,
                max_tokens=settings.guardrail_max_tokens,
            )
        yield Providers(guardrail=guardrail, answerer=OpenAIAnswerer(client, settings, corpus, relations))
