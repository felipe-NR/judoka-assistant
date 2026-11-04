import anthropic
import httpx
import openai
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from judo_chat.errors import register_error_handlers

_REQUEST = httpx.Request("POST", "https://api.provedor.test")


def _status_error(cls: type[Exception], status: int) -> Exception:
    return cls("erro", response=httpx.Response(status, request=_REQUEST), body=None)


def _client(error: Exception) -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/")
    def root() -> None:
        raise error

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("cls", [anthropic.RateLimitError, openai.RateLimitError])
def test_rate_limit_becomes_503_with_retry_after(cls: type[Exception]) -> None:
    response = _client(_status_error(cls, 429)).get("/")
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "10"
    assert "sobrecarregado" in response.json()["detail"]


@pytest.mark.parametrize(
    "error",
    [
        _status_error(anthropic.InternalServerError, 500),
        anthropic.APIConnectionError(request=_REQUEST),
        _status_error(openai.InternalServerError, 500),
        openai.APIConnectionError(request=_REQUEST),
    ],
)
def test_provider_failure_becomes_502(error: Exception) -> None:
    response = _client(error).get("/")
    assert response.status_code == 502
    assert response.json() == {"detail": "O assistente não conseguiu responder agora."}
