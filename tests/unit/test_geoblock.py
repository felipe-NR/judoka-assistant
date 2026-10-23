from fastapi import FastAPI
from fastapi.testclient import TestClient

from judo_chat.geoblock import BLOCKED_MESSAGE, GeoBlockMiddleware

_COUNTRIES = {"8.219.0.1": "SG", "191.17.215.90": "BR"}


def _client(ip: str) -> TestClient:
    app = FastAPI()

    @app.get("/")
    def root() -> dict[str, str]:
        return {"ok": "sim"}

    app.add_middleware(GeoBlockMiddleware, lookup=_COUNTRIES.get, blocked=["sg", "CN"])
    return TestClient(app, client=(ip, 50000))


def test_blocked_country_gets_403() -> None:
    response = _client("8.219.0.1").get("/")
    assert response.status_code == 403
    assert response.json() == {"detail": BLOCKED_MESSAGE}


def test_other_country_passes() -> None:
    assert _client("191.17.215.90").get("/").status_code == 200


def test_ip_outside_the_database_passes() -> None:
    assert _client("127.0.0.1").get("/").status_code == 200
