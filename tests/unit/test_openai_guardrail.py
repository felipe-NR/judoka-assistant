from dataclasses import dataclass, field

import httpx
import openai
import pytest

from judo_chat.guardrail import GUARDRAIL_SYSTEM
from judo_chat.openai_provider import OpenAIGuardrail


@dataclass
class FakeDetails:
    cached_tokens: int = 0


@dataclass
class FakeUsage:
    input_tokens: int = 900
    output_tokens: int = 20
    input_tokens_details: FakeDetails = field(default_factory=FakeDetails)


@dataclass
class FakeResponse:
    output_text: str
    status: str = "completed"
    model: str = "gpt-6-luna"
    usage: FakeUsage | None = field(default_factory=FakeUsage)


class FakeResponses:
    def __init__(self, result: FakeResponse | Exception) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs: object) -> FakeResponse:
        self.calls.append(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeClient:
    def __init__(self, result: FakeResponse | Exception) -> None:
        self.responses = FakeResponses(result)
        self.options: list[dict[str, object]] = []

    def with_options(self, **options: object) -> "FakeClient":
        self.options.append(options)
        return self


def _guardrail(result: FakeResponse | Exception) -> tuple[OpenAIGuardrail, FakeClient]:
    client = FakeClient(result)
    guardrail = OpenAIGuardrail(client, "gpt-6-luna", 5.0, effort="low", max_tokens=200)  # type: ignore[arg-type]
    return guardrail, client


async def test_allows_in_scope_category() -> None:
    guardrail, client = _guardrail(FakeResponse('{"category": "tecnica", "reason": "projeção"}'))
    result = await guardrail.classify("como faço osoto-gari?", techniques=["Osoto-gari"])
    assert result.allowed and result.category == "tecnica" and result.reason == "projeção" and not result.failed
    assert client.options == [{"timeout": 5.0, "max_retries": 1}]
    [call] = client.responses.calls
    assert call["model"] == "gpt-6-luna"
    assert call["instructions"] == GUARDRAIL_SYSTEM
    assert (
        call["input"]
        == "<pergunta>\ncomo faço osoto-gari?\n</pergunta>\n<tecnicas_reconhecidas>Osoto-gari</tecnicas_reconhecidas>"
    )
    assert call["max_output_tokens"] == 200
    assert call["reasoning"] == {"effort": "low"}
    assert call["text"]["format"]["strict"] is True  # type: ignore[index]
    assert call["store"] is False


async def test_blocks_out_of_scope_category() -> None:
    guardrail, _ = _guardrail(FakeResponse('{"category": "fora", "reason": "futebol"}'))
    result = await guardrail.classify("quem ganhou o jogo ontem?")
    assert not result.allowed and result.category == "fora" and not result.failed


async def test_logs_token_usage(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
    usage = FakeUsage(input_tokens=900, output_tokens=20, input_tokens_details=FakeDetails(cached_tokens=800))
    guardrail, _ = _guardrail(FakeResponse('{"category": "regras", "reason": "punição"}', usage=usage))
    await guardrail.classify("o que é shido?")
    assert "guardrail: model=gpt-6-luna cache_read=800 input=900 output=20" in caplog.messages


async def test_works_without_usage() -> None:
    guardrail, _ = _guardrail(FakeResponse('{"category": "historia", "reason": "Kano"}', usage=None))
    result = await guardrail.classify("quem fundou o judô?")
    assert result.allowed and result.category == "historia"


_REQUEST = httpx.Request("POST", "https://api.openai.com")


@pytest.mark.parametrize(
    ("result", "reason"),
    [
        (FakeResponse('{"category": "tecnica"', status="incomplete"), "guardrail_error:status:incomplete"),
        (openai.APIConnectionError(request=_REQUEST), "guardrail_error:APIConnectionError"),
        (openai.APITimeoutError(request=_REQUEST), "guardrail_error:APITimeoutError"),
        (FakeResponse('{"category": "tecnica"'), "guardrail_error:validation"),
        (FakeResponse('{"category": "culinaria", "reason": "receita"}'), "guardrail_error:validation"),
        (RuntimeError("bug"), "guardrail_error:unexpected"),
    ],
)
async def test_fails_closed(result: FakeResponse | Exception, reason: str) -> None:
    guardrail, _ = _guardrail(result)
    classified = await guardrail.classify("como faço osoto-gari?")
    assert not classified.allowed and classified.failed
    assert classified.category == "fora" and classified.reason == reason
