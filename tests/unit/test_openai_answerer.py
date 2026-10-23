from dataclasses import dataclass, field

from judo_chat.answer import REFUSAL_MESSAGE
from judo_chat.config import Settings
from judo_chat.corpus.models import Corpus
from judo_chat.openai_provider import OpenAIAnswerer


@dataclass
class FakeDetails:
    cached_tokens: int = 0
    cache_write_tokens: int = 0


@dataclass
class FakeUsage:
    input_tokens: int = 10
    output_tokens: int = 5
    input_tokens_details: FakeDetails = field(default_factory=FakeDetails)


@dataclass
class FakeResponse:
    output_text: str
    status: str = "completed"
    model: str = "gpt-6-luna"
    usage: FakeUsage = field(default_factory=FakeUsage)


class FakeResponses:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs: object) -> FakeResponse:
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response: FakeResponse) -> None:
        self.responses = FakeResponses(response)

    def with_options(self, **_: object) -> "FakeClient":
        return self


def _answerer(corpus: Corpus, text: str) -> tuple[OpenAIAnswerer, FakeClient]:
    client = FakeClient(FakeResponse(text))
    settings = Settings(_env_file=None, provider="openai")
    return OpenAIAnswerer(client, settings, corpus), client  # type: ignore[arg-type]


async def test_requests_the_long_cache_lifetime(corpus: Corpus) -> None:
    answerer, client = _answerer(corpus, "resposta")
    await answerer.answer("como faço osoto-gari?", [])
    [call] = client.responses.calls
    assert call["prompt_cache_options"] == {"ttl": "12h"}


async def test_scope_refusal_from_the_model_is_flagged(corpus: Corpus) -> None:
    answerer, _ = _answerer(corpus, REFUSAL_MESSAGE)
    answer = await answerer.answer("qual a capital da França?", [])
    assert answer.refused and answer.text == REFUSAL_MESSAGE
