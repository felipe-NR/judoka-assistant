from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from judo_chat import geoblock
from judo_chat.geoblock import BLOCKED_MESSAGE, CountryDatabase, GeoBlockMiddleware, open_country_database

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


class FakeReader:
    def __init__(self, records: dict[str, object]) -> None:
        self._records = records

    def get(self, ip: str) -> object:
        # O maxminddb levanta ValueError para texto que não é IP.
        if ip == "não-é-ip":
            raise ValueError(f"'{ip}' does not appear to be an IPv4 or IPv6 address")
        return self._records.get(ip)


_RECORDS: dict[str, object] = {
    "191.17.215.90": {"country": {"iso_code": "BR", "names": {"pt-BR": "Brasil"}}},
    "10.0.0.1": ["não é um dict"],
    "10.0.0.2": {"continent": {"code": "SA"}},
    "10.0.0.3": {"country": "BR"},
    "10.0.0.4": {"country": {"names": {"pt-BR": "Brasil"}}},
    "10.0.0.5": {"country": {"iso_code": 76}},
}


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> CountryDatabase:
    opened: list[Path] = []

    def open_database(path: Path) -> FakeReader:
        opened.append(path)
        return FakeReader(_RECORDS)

    monkeypatch.setattr(geoblock.maxminddb, "open_database", open_database)
    path = tmp_path / "paises.mmdb"
    path.write_bytes(b"")
    found = open_country_database(path)
    assert isinstance(found, CountryDatabase) and opened == [path]
    return found


def test_database_returns_the_iso_code(database: CountryDatabase) -> None:
    assert database("191.17.215.90") == "BR"


@pytest.mark.parametrize("ip", ["não-é-ip", "127.0.0.1", "10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"])
def test_database_returns_none_without_a_valid_code(database: CountryDatabase, ip: str) -> None:
    assert database(ip) is None


def test_missing_database_turns_the_block_off(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    assert open_country_database(tmp_path / "ausente.mmdb") is None
    assert "bloqueio por país desligado" in caplog.text
