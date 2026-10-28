# Produção e deploy

Onde a página e a API rodam, como o deploy chega à VM e o que protege a API pública. O
diagrama está em [`../arquitetura/README.md`](../arquitetura/README.md), seção "Onde roda".

## Página e API

A página de chat fica em https://felipe-nr.github.io/judoka-assistant/, publicada pelo
workflow `.github/workflows/pages.yml` a cada push que mexe em `src/judo_chat/static/`.
O GitHub Pages só serve arquivos estáticos; a URL da API vem da variável de repositório
`JUDO_CHAT_API_URL`.

Em produção a API roda numa VM E2.1.Micro Always Free da OCI, separada da VM do ai-memory,
como serviço systemd (`deploy/judoka-api.service`) ouvindo só em `127.0.0.1:8010`. O acesso
público entra pelo Tailscale Funnel, que dá HTTPS sem abrir porta na OCI. Para instalar ou
atualizar, na VM:

```bash
sudo install -d -m 700 /etc/judoka-api
sudo cp deploy/env.example /etc/judoka-api/env   # preencha OPENAI_API_KEY
sudo ./deploy/install.sh                          # ou: sudo ./deploy/install.sh <branch ou commit>
```

O script cria o usuário `judoka`, põe o código em `/opt/judoka-assistant`, roda
`uv sync --frozen --no-dev`, baixa a base de países do bloqueio por país, reinicia o serviço
e liga o Funnel. Logs:
`journalctl -u judoka-api -f`.

## Deploy automático

O workflow `.github/workflows/deploy.yml` roda a cada push no `main` que mexe no backend
(`src/` fora de `static/`, `data/`, `pyproject.toml`, `uv.lock`, `deploy/`), e também pela
aba Actions (`workflow_dispatch`). Ele roda o `ruff` e os testes de `tests/api` e
`tests/unit` e, se passarem, instala o commit na VM. Por último, um job fora da tailnet
confere a URL pública com um preflight de CORS, que não chama o provedor nem conta no rate
limit. Ele fica fora porque, dentro da tailnet, o nome da VM resolve para o IP da tailnet e
não para o Funnel. Mudanças só na página continuam saindo pelo `pages.yml`.

Os dois workflows rodam em `ubuntu-24.04`, fixo, e as actions estão nas versões que rodam em
Node.js 24. O `setup-uv` vai
com a versão exata (`@v10.3.3`), porque desde a v8 ele não publica tags de major.

O runner entra na tailnet como nó efêmero com a tag `tag:ci` e faz SSH na VM como
`judoka-deploy`. A chave desse usuário só roda `/usr/local/sbin/judoka-deploy <commit>`, que
recusa commits fora do `main`. Esse comando roda o `install.sh` a partir de um clone do root,
e não de `/opt/judoka-assistant`, que pertence ao usuário do serviço.

Para configurar, uma vez:

1. Gere a chave do deploy fora do repositório:
   `ssh-keygen -t ed25519 -N "" -C github-actions-deploy -f judoka-deploy-ci`.
2. Na VM, a partir de um checkout do repositório:
   `sudo ./deploy/setup-ci.sh judoka-deploy-ci.pub`. Rodar de novo troca a chave.
3. Na política da tailnet, declare o dono de `tag:ci` em `tagOwners` e libere a porta 22 da
   VM para ele. A VM não tem tag, então ela entra em `hosts` com o IP dela na tailnet (o IP
   fica só na política, fora deste repositório) e a regra vai em `grants`:
   `{"src": ["tag:ci"], "dst": ["judoka-api"], "ip": ["tcp:22"]}`. Depois crie um cliente
   OAuth com escrita em `auth_keys` e a tag `tag:ci`.
4. No GitHub, crie o environment `production`, restrito ao branch `main`, com os secrets
   `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET` e `JUDO_CHAT_DEPLOY_SSH_KEY` (a chave privada) e
   a variável `JUDO_CHAT_DEPLOY_HOST` (o nome MagicDNS da VM). A variável `JUDO_CHAT_API_URL`, do
   repositório, já existe por causa do `pages.yml`.

O `install.sh` manual continua valendo para a primeira instalação e para emergências.

## Proteções da API pública

A URL da API é pública e cada pergunta gasta crédito do provedor; o CORS só barra
navegadores. Por isso, em produção:

- a API não serve a página de chat (`JUDO_CHAT_SERVE_CHAT_PAGE=false`);
- `/api/perguntar` aceita 8 perguntas por minuto e 80 por dia de cada IP, e 1000 por dia no
  total, em janelas móveis (`src/judo_chat/question_rate_limit.py`). Acima disso responde 429
  (por IP) ou 503 (total), com `Retry-After`. As contagens zeram quando o serviço reinicia;
  o teto de gasto fica nas contas dos provedores;
- pedidos de Singapura, Paquistão, China e Índia recebem 403 (seção abaixo);
- o uvicorn atende no máximo 8 conexões ao mesmo tempo.

## Bloqueio por país

A API responde 403 a qualquer rota quando o IP de origem é de Singapura, Paquistão, China
ou Índia (`JUDO_CHAT_BLOCKED_COUNTRIES`, em JSON: `'["SG","PK","CN","IN"]'`; `'[]'`
desliga). Quase todo acesso desses países a sites pequenos é bot de datacenter, e cada
pergunta respondida gasta tokens. Como no rate limit, o IP vem do `X-Forwarded-For` que o
Funnel envia, aceito pelo uvicorn porque o Funnel conecta de 127.0.0.1
(`--forwarded-allow-ips`).

A base de países fica em `.geoip/` (fora do git). O `install.sh` a baixa a cada deploy; se o
download falhar, a base anterior continua valendo. A DB-IP publica uma base nova por mês.
Para baixar à mão (na VM, como o usuário `judoka`, ou localmente):

```bash
uv run python scripts/update_geoip.py
```

Sem a base, a API sobe com o bloqueio desligado e avisa no log. A base é a
[IP to Country Lite da DB-IP](https://db-ip.com) (CC BY 4.0), que não exige conta; uma
`GeoLite2-Country.mmdb` da MaxMind também serve, apontada por `JUDO_CHAT_GEOIP_DB`.
