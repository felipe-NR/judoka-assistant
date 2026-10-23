from typing import Annotated

from fastapi import Depends, HTTPException, Request

from judo_chat.corpus.models import Corpus
from judo_chat.normalizer import Recognizer
from judo_chat.providers import AnswerProvider, GuardrailProvider
from judo_chat.question_rate_limit import QuestionRateLimiter, wait_text


def get_corpus(request: Request) -> Corpus:
    return request.app.state.corpus


def get_recognizer(request: Request) -> Recognizer:
    return request.app.state.recognizer


def get_guardrail(request: Request) -> GuardrailProvider:
    return request.app.state.guardrail


def get_answerer(request: Request) -> AnswerProvider:
    return request.app.state.answerer


def get_question_rate_limiter(request: Request) -> QuestionRateLimiter:
    return request.app.state.question_rate_limiter


def enforce_question_rate_limit(
    request: Request, limiter: Annotated[QuestionRateLimiter, Depends(get_question_rate_limiter)]
) -> None:
    # Atrás do Funnel, o uvicorn (--proxy-headers) põe aqui o IP do X-Forwarded-For.
    client_ip = request.client.host if request.client else "desconhecido"
    decision = limiter.check_and_record(client_ip)
    if decision.allowed:
        return
    headers = {"Retry-After": str(decision.retry_after_s)}
    if decision.limit == "global_por_dia":
        detail = "O assistente atingiu o limite de perguntas por hoje. Tente de novo mais tarde."
        raise HTTPException(status_code=503, detail=detail, headers=headers)
    detail = f"Você fez muitas perguntas seguidas. Tente de novo em {wait_text(decision.retry_after_s)}."
    raise HTTPException(status_code=429, detail=detail, headers=headers)


CorpusDep = Annotated[Corpus, Depends(get_corpus)]
RecognizerDep = Annotated[Recognizer, Depends(get_recognizer)]
GuardrailDep = Annotated[GuardrailProvider, Depends(get_guardrail)]
AnswererDep = Annotated[AnswerProvider, Depends(get_answerer)]
