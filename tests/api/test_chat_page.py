from fastapi import FastAPI
from fastapi.testclient import TestClient

from judo_chat.main import mount_chat_page


def test_chat_page_is_served_only_when_mounted() -> None:
    without_page = FastAPI()
    assert TestClient(without_page).get("/").status_code == 404
    with_page = FastAPI()
    mount_chat_page(with_page)
    assert TestClient(with_page).get("/").status_code == 200
