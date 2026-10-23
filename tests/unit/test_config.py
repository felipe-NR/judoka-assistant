import pytest
from pydantic import ValidationError

from judo_chat.config import Settings


# _env_file=None: o .env local (por exemplo com JUDO_CHAT_GUARDRAIL_API=decisions) não entra no teste.
def test_refusal_fallbacks_are_rejected_on_haiku() -> None:
    with pytest.raises(ValidationError, match="Haiku"):
        Settings(_env_file=None, provider="anthropic", answer_model="claude-haiku-5-5", use_refusal_fallbacks=True)


def test_refusal_fallbacks_are_accepted_on_sonnet() -> None:
    assert Settings(
        _env_file=None, provider="anthropic", answer_model="claude-sonnet-5-5", use_refusal_fallbacks=True
    ).use_refusal_fallbacks


def test_openai_cache_lasts_the_whole_day_by_default() -> None:
    assert Settings(_env_file=None, provider="openai").openai_cache_ttl == "12h"
