#!/usr/bin/env bash
# Prepara a VM para receber o deploy do GitHub Actions (.github/workflows/deploy.yml).
# Uso (como root, uma vez, ou de novo para trocar a chave): ./deploy/setup-ci.sh <chave-publica.pub>
#
# Cria o usuário judoka-deploy, que só consegue rodar /usr/local/sbin/judoka-deploy: a chave
# entra no authorized_keys com command= forçado e só aceita conexões vindas da tailnet.
set -euo pipefail

PUBKEY_FILE="${1:-}"
DEPLOY_USER="judoka-deploy"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$(id -u)" -ne 0 ]; then
  echo "Rode como root (sudo $0 <chave-publica.pub>)." >&2
  exit 1
fi
if [ -z "$PUBKEY_FILE" ] || [ ! -f "$PUBKEY_FILE" ]; then
  echo "Uso: $0 <chave-publica.pub>" >&2
  exit 1
fi

install -m 755 -o root -g root "$SRC_DIR/judoka-deploy" /usr/local/sbin/judoka-deploy

# O shell precisa ser o bash: o sshd roda o command= forçado com "<shell> -c".
if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "/home/$DEPLOY_USER" --shell /bin/bash "$DEPLOY_USER"
fi

SUDOERS="/etc/sudoers.d/judoka-deploy"
printf '%s ALL=(root) NOPASSWD: /usr/local/sbin/judoka-deploy\n' "$DEPLOY_USER" > "$SUDOERS.tmp"
chmod 440 "$SUDOERS.tmp"
visudo -cf "$SUDOERS.tmp" >/dev/null
mv "$SUDOERS.tmp" "$SUDOERS"

# restrict: sem pty, sem encaminhamento de porta ou agente. from=: só endereços da tailnet
# (100.64.0.0/10). O commit pedido pelo cliente chega em SSH_ORIGINAL_COMMAND e o
# judoka-deploy valida o formato antes de qualquer coisa.
SSH_DIR="/home/$DEPLOY_USER/.ssh"
install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "$SSH_DIR"
printf 'restrict,from="100.64.0.0/10",command="sudo -n /usr/local/sbin/judoka-deploy \\"$SSH_ORIGINAL_COMMAND\\"" %s\n' \
  "$(tr -d '\n' < "$PUBKEY_FILE")" > "$SSH_DIR/authorized_keys"
chown "$DEPLOY_USER:$DEPLOY_USER" "$SSH_DIR/authorized_keys"
chmod 600 "$SSH_DIR/authorized_keys"

echo "Pronto. O GitHub Actions entra como $DEPLOY_USER e só roda /usr/local/sbin/judoka-deploy."
