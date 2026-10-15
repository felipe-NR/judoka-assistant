"""Erros dos provedores de IA viram mensagens genéricas em pt-BR; o detalhe fica no log."""

import logging

import anthropic
import openai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def _rate_limited(request: Request, error: Exception) -> JSONResponse:
    logger.warning("limite de requisições do provedor de IA: %s", error)
    return JSONResponse(
        status_code=503,
        content={"detail": "O assistente está sobrecarregado. Tente de novo em alguns segundos."},
        headers={"Retry-After": "10"},
    )


async def _upstream_failed(request: Request, error: Exception) -> JSONResponse:
    logger.error("falha na API do provedor de IA: %s", error)
    return JSONResponse(status_code=502, content={"detail": "O assistente não conseguiu responder agora."})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(anthropic.RateLimitError, _rate_limited)
    app.add_exception_handler(anthropic.APIError, _upstream_failed)
    app.add_exception_handler(openai.RateLimitError, _rate_limited)
    app.add_exception_handler(openai.APIError, _upstream_failed)
