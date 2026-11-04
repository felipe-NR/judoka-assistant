from fastapi import FastAPI
from fastapi.testclient import TestClient

from judo_chat.main import mount_chat_page


def test_chat_page_is_served_only_when_mounted() -> None:
    without_page = FastAPI()
    assert TestClient(without_page).get("/").status_code == 404
    with_page = FastAPI()
    mount_chat_page(with_page)
    assert TestClient(with_page).get("/").status_code == 200


def test_pwa_files_are_served_and_consistent() -> None:
    # O manifest, o service worker e os ícones saem da mesma pasta da página
    # (docs/decisoes/0002-disponibilizar-como-pwa.md).
    app = FastAPI()
    mount_chat_page(app)
    client = TestClient(app)

    page = client.get("/").text
    assert 'rel="manifest" href="manifest.webmanifest"' in page
    assert 'rel="apple-touch-icon" href="apple-touch-icon.png"' in page
    assert 'register("sw.js")' in page

    response = client.get("/manifest.webmanifest")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/manifest+json")
    manifest = response.json()
    # Relativos, para valer em /judoka-assistant/ no Pages e na raiz quando a API serve a página.
    assert manifest["start_url"] == manifest["scope"] == "./"
    assert manifest["display"] == "standalone"
    purposes = {(icon["sizes"], icon["purpose"]) for icon in manifest["icons"]}
    assert {("192x192", "any"), ("512x512", "any"), ("512x512", "maskable")} <= purposes
    for icon in manifest["icons"]:
        image = client.get("/" + icon["src"])
        assert image.status_code == 200
        assert image.content.startswith(b"\x89PNG")

    worker = client.get("/sw.js").text
    # O pages.yml troca o marcador pelo commit; sem ele, o cache não muda entre publicações.
    assert 'const CACHE = "judo-chat-__VERSAO__";' in worker
    # O config.js leva a URL da API e não pode ficar no cache.
    assert "config.js" not in worker.split("const SHELL")[1].split("\n")[0]
    shell = ("manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png")
    for name in shell:
        assert f'"{name}"' in worker
        assert client.get("/" + name).status_code == 200
