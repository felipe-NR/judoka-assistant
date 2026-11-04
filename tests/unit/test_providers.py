import pytest

from judo_chat.answer import Answerer
from judo_chat.config import Settings
from judo_chat.corpus.models import Corpus
from judo_chat.guardrail import Guardrail
from judo_chat.normalizer import Recognizer
from judo_chat.openai_provider import OpenAIAnswerer, OpenAIDecisionsGuardrail, OpenAIGuardrail
from judo_chat.providers import create_providers


@pytest.fixture(autouse=True)
def _api_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    # Os clientes só leem a chave ao serem criados; nenhum teste aqui chama a API.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "teste")
    monkeypatch.setenv("OPENAI_API_KEY", "teste")


async def test_anthropic_providers(corpus: Corpus, recognizer: Recognizer) -> None:
    settings = Settings(_env_file=None, provider="anthropic")
    async with create_providers(settings, corpus, recognizer) as providers:
        assert isinstance(providers.guardrail, Guardrail)
        assert isinstance(providers.answerer, Answerer)


async def test_openai_providers_use_the_responses_guardrail(corpus: Corpus, recognizer: Recognizer) -> None:
    settings = Settings(_env_file=None, provider="openai", guardrail_api="responses")
    async with create_providers(settings, corpus, recognizer) as providers:
        assert isinstance(providers.guardrail, OpenAIGuardrail)
        assert isinstance(providers.answerer, OpenAIAnswerer)


async def test_openai_providers_use_the_decisions_guardrail(corpus: Corpus, recognizer: Recognizer) -> None:
    settings = Settings(_env_file=None, provider="openai", guardrail_api="decisions")
    async with create_providers(settings, corpus, recognizer) as providers:
        assert isinstance(providers.guardrail, OpenAIDecisionsGuardrail)
        assert isinstance(providers.answerer, OpenAIAnswerer)
