from typing import Annotated

from fastapi import Depends, Request

from judo_chat.corpus.models import Corpus
from judo_chat.normalizer import Recognizer
from judo_chat.providers import AnswerProvider, GuardrailProvider


def get_corpus(request: Request) -> Corpus:
    return request.app.state.corpus


def get_recognizer(request: Request) -> Recognizer:
    return request.app.state.recognizer


def get_guardrail(request: Request) -> GuardrailProvider:
    return request.app.state.guardrail


def get_answerer(request: Request) -> AnswerProvider:
    return request.app.state.answerer


CorpusDep = Annotated[Corpus, Depends(get_corpus)]
RecognizerDep = Annotated[Recognizer, Depends(get_recognizer)]
GuardrailDep = Annotated[GuardrailProvider, Depends(get_guardrail)]
AnswererDep = Annotated[AnswerProvider, Depends(get_answerer)]
