import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI

from judo_chat import main
from judo_chat.config import Settings
from judo_chat.corpus.models import Corpus
from judo_chat.guardrail import GuardrailResult
from judo_chat.normalizer import Recognizer
from judo_chat.providers import Providers
from judo_chat.question_rate_limit import QuestionRateLimiter


class FakeGuardrail:
    async def classify(self, query: str, *_: object) -> GuardrailResult:
        return GuardrailResult(category="tecnica", reason="teste")


class FakeAnswerer:
    last_cache_touch: float | None = None

    def __init__(self) -> None:
        self.keep_alive_calls = 0

    async def keep_alive(self) -> tuple[int, int]:
        self.keep_alive_calls += 1
        return 0, 0


def _patch(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> Providers:
    providers = Providers(guardrail=FakeGuardrail(), answerer=FakeAnswerer())  # type: ignore[arg-type]

    @asynccontextmanager
    async def create_providers(*_: object) -> AsyncIterator[Providers]:
        yield providers

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "create_providers", create_providers)
    return providers


async def test_lifespan_fills_the_app_state(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
    providers = _patch(monkeypatch, Settings(_env_file=None, provider="openai", guardrail_api="decisions"))
    app = FastAPI()
    async with main.lifespan(app):
        assert isinstance(app.state.corpus, Corpus)
        assert isinstance(app.state.recognizer, Recognizer)
        assert app.state.guardrail is providers.guardrail
        assert app.state.answerer is providers.answerer
        assert isinstance(app.state.question_rate_limiter, QuestionRateLimiter)
    assert "configuração: provider=openai guardrail=decisions/gpt-6-luna resposta=gpt-6-luna" in caplog.messages


async def test_lifespan_logs_the_messages_guardrail_for_anthropic(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("INFO")
    _patch(monkeypatch, Settings(_env_file=None, provider="anthropic", keepalive_enabled=False))
    async with main.lifespan(FastAPI()):
        pass
    assert any(m.startswith("configuração: provider=anthropic guardrail=messages/") for m in caplog.messages)


async def test_lifespan_cancels_the_keepalive_on_shutdown(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch, Settings(_env_file=None, provider="anthropic", keepalive_enabled=True))
    tasks_before = set(asyncio.all_tasks())
    async with main.lifespan(FastAPI()):
        [keepalive] = set(asyncio.all_tasks()) - tasks_before
        assert not keepalive.done()
    assert keepalive.cancelled()
