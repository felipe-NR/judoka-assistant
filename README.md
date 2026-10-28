# Judô Chat

Assistente que responde em português do Brasil a perguntas sobre técnicas, história e
regras do judô, e recusa qualquer outro assunto. O corpus inteiro vai no contexto do modelo,
com cache de prompt, depois de um guardrail de escopo que falha fechado. A arquitetura, com
diagramas, está em [`docs/arquitetura/`](docs/arquitetura/README.md); a decisão de manter
esse desenho está em [`docs/decisoes/0001-manter-cag.md`](docs/decisoes/0001-manter-cag.md), e
as alternativas avaliadas, em [`docs/historico/`](docs/historico/propostas-iniciais.md).

## Rodar

```bash
uv sync
cp .env.example .env   # preencha ANTHROPIC_API_KEY
uv run uvicorn judo_chat.main:app --reload
```

Por padrão, o provedor é a Anthropic. Para usar a OpenAI, adicione ao `.env`:

```bash
JUDO_CHAT_PROVIDER=openai
OPENAI_API_KEY=...
```

Nesse modo, os modelos padrão são `gpt-6-luna`. `JUDO_CHAT_ANSWER_MODEL` e
`JUDO_CHAT_GUARDRAIL_MODEL` permitem escolher outros modelos. A integração usa a
[Responses API da OpenAI](https://developers.openai.com/api/reference/python): o guardrail
usa saída estruturada, e a resposta usa cache de prefixos. As instruções e o corpus ficam
antes do histórico e da pergunta, e uma chave estável de cache separa o guardrail da
resposta. Os logs mostram `cache_read` e `cache_write` para medir os acertos. Na OpenAI, o
cache dura 30 minutos por padrão e cada gravação custa 1,25 vez a entrada; a resposta pede
`prompt_cache_options.ttl: "12h"` (gravação a 2,5 vezes), que cobre o dia com uma gravação
e dispensa o re-aquecimento, exclusivo da Anthropic. `JUDO_CHAT_OPENAI_CACHE_TTL=30m` volta
ao padrão.

Com `JUDO_CHAT_GUARDRAIL_API=decisions`, o guardrail usa a
[Decisions API](https://developers.openai.com/api/docs/guides/decisions), que cobra só a
entrada e devolve probabilidades em vez de texto. Ele faz três perguntas na
mesma chamada: a categoria, se a pergunta pede ajuda para agredir alguém fora do judô e se
ela tenta mudar as instruções do assistente. A pergunta é bloqueada se a categoria for
`fora` ou se `P(fora)`, `P(agressão)` ou `P(instruções)` passar do limite
(`JUDO_CHAT_GUARDRAIL_FORA_THRESHOLD`, `JUDO_CHAT_GUARDRAIL_HARM_THRESHOLD` e
`JUDO_CHAT_GUARDRAIL_INSTRUCTIONS_THRESHOLD`, todos 0,5). Na avaliação de 2026-10-14, a latência
mediana caiu de ~4 s para ~0,4 s. Como o modelo não raciocina nem vê o corpus, ele recusava
termos de arbitragem que a pergunta não liga ao judô (as 4 falsas recusas daquela avaliação).
Por isso o reconhecedor também acha os termos de `data/glossario/termos_regras.yaml` e os
envia ao guardrail em `<termos_reconhecidos>`, cada um com o título do documento que o
explica; só o nome do termo não bastou. Como uma injeção que cita um termo podia passar como
`regras`, entrou a pergunta sobre mudar as instruções. Na avaliação de 2026-10-23, a falsa
recusa caiu de 3,1% para 0%, com recusa correta de 100% e nenhum falso aceite adversarial.

A página de chat fica em http://localhost:8000 e a API em `POST /api/perguntar`
(`{"query": "como faço o ashi barai?"}`).

## Publicar (GitHub Pages + API na OCI)

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

### Deploy automático

O workflow `.github/workflows/deploy.yml` roda a cada push no `main` que mexe no backend
(`src/` fora de `static/`, `data/`, `pyproject.toml`, `uv.lock`, `deploy/`), e também pela
aba Actions (`workflow_dispatch`). Ele roda o `ruff` e os testes de `tests/api` e
`tests/unit` e, se passarem, instala o commit na VM. Por último, um job fora da tailnet
confere a URL pública com um preflight de CORS, que não chama o provedor nem conta no rate
limit. Ele fica fora porque, dentro da tailnet, o nome da VM resolve para o IP da tailnet e
não para o Funnel. Mudanças só na página continuam saindo pelo `pages.yml`.

Os dois workflows rodam em `ubuntu-24.04`, fixo até os jobs serem testados no Ubuntu 26
(`docs/roadmap.md`), e as actions estão nas versões que rodam em Node.js 24. O `setup-uv` vai
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

A URL da API é pública e cada pergunta gasta crédito do provedor; o CORS só barra
navegadores. Por isso, em produção:

- a API não serve a página de chat (`JUDO_CHAT_SERVE_CHAT_PAGE=false`);
- `/api/perguntar` aceita 8 perguntas por minuto e 80 por dia de cada IP, e 1000 por dia no
  total, em janelas móveis (`src/judo_chat/question_rate_limit.py`). Acima disso responde 429
  (por IP) ou 503 (total), com `Retry-After`. As contagens zeram quando o serviço reinicia;
  o teto de gasto fica nas contas dos provedores;
- pedidos de Singapura, Paquistão, China e Índia recebem 403 (seção abaixo);
- o uvicorn atende no máximo 8 conexões ao mesmo tempo.

### Bloqueio por país

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

## Como funciona

1. `normalizer.Recognizer` acha nomes de técnica na pergunta: nome oficial, nome da IJF,
   grafias variadas e nomes populares (ambíguos devolvem todas as candidatas). Acha também
   termos de regras, arbitragem e graduação, que só vão ao guardrail.
2. O guardrail classifica a pergunta em `tecnica`, `historia`, `regras` ou `fora` com o
   provedor configurado. Qualquer erro bloqueia a resposta.
3. O provedor configurado responde com instruções e corpus (~46 mil tokens no Haiku 5.5,
   ~28 mil no gpt-6-luna). Na Anthropic, o bloco de system fica cacheado por 1 hora; na
   OpenAI, por 12 horas.

## Custo com OpenAI

Medido em 2026-10-28 nos logs da produção de 2026-10-23 a 2026-10-28 (37 respostas), com a
tabela do gpt-6-luna para prompts de até 272 mil tokens: US$ 0,10/M de entrada, US$ 0,01/M de
leitura do cache, US$ 0,25/M de gravação com TTL de 12 horas e US$ 0,50/M de saída
([preços da OpenAI](https://developers.openai.com/api/docs/pricing)). O prefixo tem 27.611
tokens; uma resposta tem em mediana 135 tokens de saída.

| Caso | US$ por resposta | Respostas |
|-|-|-|
| Cache quente | ~0,0004 (0,0003 a 0,0006) | 31 |
| Cache frio (grava o prefixo) | ~0,007 | 6 |

O tráfego foi de 1 a 19 perguntas por dia, então as 6 gravações somaram 76% dos US$ 0,055 do
período. Com o TTL padrão de 30 minutos, a gravação custa metade, mas o mesmo tráfego teria 14
gravações e sairia cerca de 9% mais caro que o observado. Duas gravações vieram 4,5 e 5,7
horas depois da pergunta anterior, dentro das 12 horas pedidas e sem mudança no prefixo.

O guardrail registra os tokens de cada classificação desde o PR #26; antes disso, o custo dele
era uma estimativa: a Decisions API cobra só a entrada, sem cache, a US$ 0,10/M, e com a ordem
de grandeza do guardrail na Anthropic (~1.400 tokens) seriam cerca de US$ 0,00014 por pergunta.

Para medir de novo e acompanhar as gravações antes do TTL, leia o journal da VM por SSH dentro
da tailnet e passe para o script, num checkout local:

```bash
ssh <usuário>@<vm> 'sudo journalctl -u judoka-api -o short-iso' | uv run python scripts/custo_openai.py
```

O relatório dá o custo das respostas quentes e frias, do guardrail e de cada dia, e lista as
gravações que vieram antes do TTL, dizendo se a API reiniciou entre as duas perguntas.

## Custo com Anthropic

Calculado em 2026-10-07 com os tokens medidos na avaliação (effort `low`) e a tabela do
Haiku 5.5 para prompts de até 100 mil tokens (US$ 0,10/M de entrada, US$ 0,50/M de saída),
dólar a R$ 5, sem IOF. O bloco fixo tem ~46 mil tokens e fica em cache com TTL de 1 hora
(gravação a US$ 0,20/M, leitura a US$ 0,01/M). Uma resposta tem em média ~650 tokens de
saída, contando o pensamento; o guardrail, ~1.400 de entrada e ~55 de saída.

| Caso | US$ | R$ |
|-|-|-|
| Pergunta com cache quente | ~0,001 | ~0,005 |
| Gravação do cache (1 vez por dia, ou quando o corpus muda) | ~0,009 | ~0,046 |
| Re-aquecimento (leitura com `max_tokens: 0`) | ~0,0005 | ~0,0023 |
| Pergunta fora do escopo (só o guardrail) | ~0,0002 | ~0,0009 |

### Re-aquecimento do cache da Anthropic

Com `JUDO_CHAT_PROVIDER=anthropic`, `src/judo_chat/keepalive.py` roda dentro da API. Das 07h às 23h (horário de Brasília), se
ninguém perguntou nos últimos 55 minutos, ele lê o cache com `max_tokens: 0` para renovar o
TTL de 1 hora. Assim o corpus é gravado uma vez por dia (no primeiro re-aquecimento depois
das 07h) e de novo só quando o corpus, as instruções ou o modelo mudam; reiniciar a API não
grava. Custo: ~16 leituras por dia no máximo, ~R$ 0,04. O log mostra cada re-aquecimento
(`re-aquecimento: cache_read=... cache_write=...`). Configuração no `.env`:
`JUDO_CHAT_KEEPALIVE_ENABLED`, `JUDO_CHAT_KEEPALIVE_INTERVAL_S`,
`JUDO_CHAT_KEEPALIVE_WINDOW_START`, `JUDO_CHAT_KEEPALIVE_WINDOW_END`,
`JUDO_CHAT_KEEPALIVE_TIMEZONE`.

O Sonnet 5.5 custa 20 vezes o Haiku 5.5 por token; para usá-lo, veja `.env.example`.
O custo da OpenAI depende dos modelos configurados e aparece nos dados de uso da Responses API.

Detalhes que não passam pelo modelo:
- **Vídeos:** depois da resposta, o reconhecedor acha as técnicas apresentadas (títulos e
  itens) e a API devolve os vídeos em `video_groups`, com o do Kodokan primeiro. A página os
  põe embaixo da seção de cada técnica.
- **Kanji e pronúncia:** cada grupo de `video_groups` traz o kanji da ficha da FGJ e a
  pronúncia gerada por `pronunciation.py` com as regras de `data/fgj/pronuncia.yaml`, sem
  marcar a tônica. A página mostra a pronúncia acima dos vídeos; o kanji vai numa coluna ao
  lado quando a resposta apresenta uma técnica, e junto dos vídeos de cada uma quando são várias.
- **Relações:** `relations.py` liga contragolpes, variações e combinações a partir dos textos
  da FGJ, dos nomes ("X-gaeshi", "Kuzure-X") e das séries do Projeto Budô. Perguntas sobre
  contragolpes, variações ou combinações levam as fichas das técnicas relacionadas.
- **Conversa:** a página envia as últimas 3 trocas em `history`; o servidor não guarda
  estado. O histórico vai ao modelo como dado, depois do trecho cacheado.

## Dados

| Caminho | Conteúdo | Editar? |
|-|-|-|
| `data/curadoria/*.yaml` | Nome oficial, grupo, status e textos pt-BR de cada técnica | Sim |
| `data/glossario/nomes_populares.yaml` | Nomes populares, com as técnicas a que se referem | Sim |
| `data/glossario/termos_regras.yaml` | Termos de regras, arbitragem e graduação que o guardrail recebe; cada um precisa aparecer no documento indicado | Sim |
| `data/regras/*.md`, `data/historia/*.md` | Textos de regras e história | Sim |
| `data/graduacao/*.md` | Exames de faixa (cinza a marrom), Gokyo, sequências e contragolpes, do Projeto Budô | Sim |
| `docs/fontes/fecju_kodokan_videos.csv` | Vídeos do canal do Kodokan listados pela FECJU | Sim |
| `data/fgj/*.yaml` | Fonte primária: tradução, descrição Kodokan, princípio, kyo-grupo e kanji das 100 técnicas, glossário e pronúncia da FGJ | Não, gerado por `scripts/import_fgj.py` |
| `data/glossario/tecnicas.yaml` | Glossário final | Não, é gerado |

Depois de editar a curadoria, gere o glossário de novo (o script lê o CSV do
`judo-techniques-bot` na pasta vizinha):

```bash
uv run python scripts/build_glossary.py
```

O build falha quando um nome do CSV não é grafia do nome oficial nem consta de
`nomes_populares.yaml`, quando uma linha das fontes fica sem destino ou quando duas
técnicas disputam o mesmo nome.

A fonte primária das técnicas é o Curso de Waza da Federação Gaúcha de Judô (FGJ, 2026),
importado com `uv run --with pdfplumber python scripts/import_fgj.py CURSO.pdf LISTA_KANJI.pdf`.
O texto da FGJ é usado sem edição; o que não vem dela segue `docs/guia-estilo-ptbr.md`, e
`tests/unit/test_corpus_style.py` pega regressões. As fichas de técnica estão com `provenance: generated`; os exames de faixa
trazem a URL da página do Projeto Budô de onde vieram.

## Testes

```bash
uv run pytest            # sem rede: reconhecedor, corpus, guardrail com fakes, API
uv run pytest -m eval    # chama a API de verdade (custa dinheiro) e grava tests/eval/report.json
uv run ruff check . && uv run ruff format --check .
```
