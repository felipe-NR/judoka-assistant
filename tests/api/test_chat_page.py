from fastapi import FastAPI
from fastapi.testclient import TestClient

from judo_chat.main import mount_chat_page


def test_chat_page_is_served_only_when_mounted() -> None:
    without_page = FastAPI()
    assert TestClient(without_page).get("/").status_code == 404
    with_page = FastAPI()
    mount_chat_page(with_page)
    assert TestClient(with_page).get("/").status_code == 200


def test_page_declares_the_link_preview_image() -> None:
    # O WhatsApp não mostra a prévia sem og:image, e a URL precisa ser absoluta.
    app = FastAPI()
    mount_chat_page(app)
    client = TestClient(app)

    page = client.get("/").text
    url = "https://felipe-nr.github.io/judoka-assistant/"
    assert f'property="og:url" content="{url}"' in page
    image = f"{url}icon-512.png"
    assert f'property="og:image" content="{image}"' in page
    assert client.get(image.removeprefix(url)).status_code == 200


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


def test_saved_conversation_is_cleared_only_after_confirmation() -> None:
    # A conversa fica no aparelho sem prazo; só o "Nova conversa" confirmado apaga
    # (docs/decisoes/0002-disponibilizar-como-pwa.md).
    app = FastAPI()
    mount_chat_page(app)
    page = TestClient(app).get("/").text
    assert 'const SAVED = "judo-chat:conversa";' in page
    assert "const MAX_SAVED = 20;" in page
    assert '<dialog id="confirm-new"' in page
    assert 'value="confirm"' in page
    # A remoção da conversa só aparece dentro de clearConversation, chamada pela confirmação.
    assert page.count("localStorage.removeItem(SAVED)") == 1
    clear = page.split("function clearConversation()")[1].split("\n  }\n")[0]
    assert "localStorage.removeItem(SAVED)" in clear
