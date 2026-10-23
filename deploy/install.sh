#!/usr/bin/env bash
# Instala ou atualiza a API de produção na VM (Ubuntu 24.04) e a expõe pelo Tailscale Funnel.
# Uso (como root): ./deploy/install.sh [ref]   (ref padrão: main)
# Antes da primeira vez, crie /etc/judoka-api/env (modo 600) a partir de deploy/env.example.
set -euo pipefail

REF="${1:-main}"
REPO_URL="https://github.com/felipe-NR/judoka-assistant.git"
APP_DIR="/opt/judoka-assistant"
ENV_FILE="/etc/judoka-api/env"
PORT=8010
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$(id -u)" -ne 0 ]; then
  echo "Rode como root (sudo $0)." >&2
  exit 1
fi
if [ ! -f "$ENV_FILE" ]; then
  echo "Crie $ENV_FILE (modo 600) a partir de deploy/env.example." >&2
  exit 1
fi
chown root:root "$ENV_FILE"
chmod 600 "$ENV_FILE"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh
fi

if ! id judoka >/dev/null 2>&1; then
  useradd --system --home-dir "$APP_DIR" --no-create-home --shell /usr/sbin/nologin judoka
fi
install -d -o judoka -g judoka "$APP_DIR" /var/cache/judoka-uv

as_judoka() {
  runuser -u judoka -- env HOME="$APP_DIR" UV_CACHE_DIR=/var/cache/judoka-uv "$@"
}

if [ ! -d "$APP_DIR/.git" ]; then
  as_judoka git clone "$REPO_URL" "$APP_DIR"
fi
as_judoka git -C "$APP_DIR" fetch --prune origin
as_judoka git -C "$APP_DIR" checkout --detach "origin/$REF" 2>/dev/null \
  || as_judoka git -C "$APP_DIR" checkout --detach "$REF"
as_judoka bash -c "cd '$APP_DIR' && uv sync --frozen --no-dev --compile-bytecode"
# Base de países do bloqueio por país (src/judo_chat/geoblock.py, PR #15). Sem rede para a
# DB-IP, a base anterior continua valendo; sem base nenhuma, a API sobe sem o bloqueio.
as_judoka bash -c "cd '$APP_DIR' && .venv/bin/python scripts/update_geoip.py" \
  || echo "Aviso: não consegui atualizar a base de países (.geoip/)." >&2

install -m 644 "$SRC_DIR/judoka-api.service" /etc/systemd/system/judoka-api.service
systemctl daemon-reload
systemctl enable judoka-api.service
systemctl restart judoka-api.service

for _ in $(seq 1 60); do
  if curl -s -o /dev/null "http://127.0.0.1:$PORT/"; then break; fi
  sleep 1
done
if ! curl -s -o /dev/null "http://127.0.0.1:$PORT/"; then
  echo "A API não respondeu em $PORT. Veja: journalctl -u judoka-api -n 50" >&2
  exit 1
fi
journalctl -u judoka-api -n 20 --no-pager | grep -m1 "configuração:" || true

# O Funnel guarda a configuração no estado do tailscaled e volta sozinho depois de um reboot.
# Com o Funnel desabilitado na tailnet, o comando imprime o link de habilitação e fica
# esperando; o timeout devolve o controle.
if ! timeout 20 tailscale funnel --bg "http://127.0.0.1:$PORT"; then
  echo "O Funnel não ligou. Habilite-o no admin do Tailscale pelo link acima e rode de novo." >&2
  exit 1
fi
tailscale funnel status
