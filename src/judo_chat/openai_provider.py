"""Integração da OpenAI pela Responses API."""

import hashlib
import json
import logging
import time
from collections.abc import Sequence

import openai
import pydantic
from openai import AsyncOpenAI

from judo_chat.answer import Answer, Turn, UNAVAILABLE_MESSAGE, build_system_text, build_user_message
from judo_chat.config import Settings
from judo_chat.corpus.models import Corpus
from judo_chat.guardrail import GUARDRAIL_SYSTEM, GuardrailOutput, GuardrailResult, _closed
from judo_chat.normalizer import Match
from judo_chat.relations import Relations

logger = logging.getLogger(__name__)

_GUARDRAIL_CACHE_KEY = "judo-chat:guardrail:v1"

_GUARDRAIL_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["tecnica", "historia", "regras", "fora"]},
        "reason": {"type": "string"},
    },
    "required": ["category", "reason"],
    "additionalProperties": False,
}


class OpenAIGuardrail:
    def __init__(self, client: AsyncOpenAI, model: str, timeout_s: float, *, effort: str, max_tokens: int) -> None:
        self._client = client
        self._model = model
        self._timeout_s = timeout_s
        self._effort = effort
        self._max_tokens = max_tokens

    async def classify(
        self, query: str, history: Sequence[str] = (), techniques: Sequence[str] = ()
    ) -> GuardrailResult:
        content = f"<pergunta>\n{query}\n</pergunta>"
        if history:
            content = "<historico>\n" + "\n".join(history) + "\n</historico>\n" + content
        if techniques:
            content += "\n<tecnicas_reconhecidas>" + ", ".join(techniques) + "</tecnicas_reconhecidas>"
        try:
            response = await self._client.with_options(timeout=self._timeout_s, max_retries=1).responses.create(
                model=self._model,
                instructions=GUARDRAIL_SYSTEM,
                input=content,
                max_output_tokens=self._max_tokens,
                reasoning={"effort": self._effort},
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "guardrail",
                        "schema": _GUARDRAIL_SCHEMA,
                        "strict": True,
                    }
                },
                prompt_cache_key=_GUARDRAIL_CACHE_KEY,
                store=False,
            )
            if response.status != "completed":
                return _closed(f"status:{response.status}")
            parsed = GuardrailOutput.model_validate_json(response.output_text)
        except openai.APIError as error:
            logger.warning("guardrail: erro da API: %s", type(error).__name__)
            return _closed(type(error).__name__)
        except (pydantic.ValidationError, json.JSONDecodeError):
            logger.warning("guardrail: saída fora do schema")
            return _closed("validation")
        except Exception:
            logger.exception("guardrail: erro inesperado")
            return _closed("unexpected")
        return GuardrailResult(category=parsed.category, reason=parsed.reason)


class OpenAIAnswerer:
    def __init__(
        self, client: AsyncOpenAI, settings: Settings, corpus: Corpus, relations: Relations | None = None
    ) -> None:
        self._client = client
        self._settings = settings
        self._corpus = corpus
        self._relations = relations
        self._instructions = build_system_text(corpus)
        corpus_fingerprint = hashlib.sha256(self._instructions.encode()).hexdigest()[:16]
        self._prompt_cache_key = f"judo-chat:answer:{corpus_fingerprint}"
        self.last_cache_touch: float | None = None

    def _request(self, content: str, max_output_tokens: int) -> dict[str, object]:
        request: dict[str, object] = {
            "model": self._settings.answer_model,
            "instructions": self._instructions,
            "input": content,
            "max_output_tokens": max_output_tokens,
            "prompt_cache_key": self._prompt_cache_key,
            "store": False,
        }
        if self._settings.answer_effort is not None:
            request["reasoning"] = {"effort": self._settings.answer_effort}
        return request

    async def answer(self, query: str, matches: list[Match], history: Sequence[Turn] = ()) -> Answer:
        content = build_user_message(query, matches, self._corpus, self._relations, history)
        response = await self._client.with_options(timeout=self._settings.answer_timeout_s).responses.create(
            **self._request(content, self._settings.answer_max_tokens)
        )
        self.last_cache_touch = time.monotonic()
        usage = response.usage
        cache_read = usage.input_tokens_details.cached_tokens if usage is not None else 0
        cache_write = usage.input_tokens_details.cache_write_tokens if usage is not None else 0
        input_tokens = usage.input_tokens if usage is not None else 0
        output_tokens = usage.output_tokens if usage is not None else 0
        logger.info(
            "resposta: model=%s status=%s cache_read=%d cache_write=%d input=%d output=%d",
            response.model,
            response.status,
            cache_read,
            cache_write,
            input_tokens,
            output_tokens,
        )
        text = response.output_text.strip()
        if response.status != "completed" or not text:
            return Answer(UNAVAILABLE_MESSAGE, True, cache_read, cache_write)
        return Answer(text, False, cache_read, cache_write)

    async def keep_alive(self) -> tuple[int, int]:
        """A OpenAI faz cache de prefixos automaticamente; não há TTL para renovar."""
        return (0, 0)
