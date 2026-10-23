# Judô Chat

Assistente que responde em português do Brasil a perguntas sobre técnicas, história e
regras do judô, e recusa qualquer outro assunto. Implementa a proposta A de
[`docs/propostas.md`](docs/propostas.md): o corpus inteiro vai no contexto do modelo, com
cache de prompt, depois de um guardrail de escopo que falha fechado.

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
`uv sync --frozen --no-dev`, reinicia o serviço e liga o Funnel. Logs:
`journalctl -u judoka-api -f`.

A URL da API é pública e cada pergunta gasta crédito do provedor; o CORS só barra
navegadores. Por isso, em produção:

- a API não serve a página de chat (`JUDO_CHAT_SERVE_CHAT_PAGE=false`);
- `/api/perguntar` aceita 8 perguntas por minuto e 80 por dia de cada IP, e 1000 por dia no
  total, em janelas móveis (`src/judo_chat/question_rate_limit.py`). Acima disso responde 429
  (por IP) ou 503 (total), com `Retry-After`. As contagens zeram quando o serviço reinicia;
  o teto de gasto fica nas contas dos provedores;
- o uvicorn atende no máximo 8 conexões ao mesmo tempo.

### Teste local via ngrok

Para testar a página contra uma API desta máquina, use o domínio fixo do ngrok da conta
(`https://quadrantal-glenda-interstream.ngrok-free.dev`):

```bash
./start-ngrok.sh   # sobe a API na porta 8010 (JUDO_CHAT_PORT) e o túnel ngrok
./stop-ngrok.sh    # derruba os dois
```

A chave do provedor fica só no `.env` local; a página nunca a vê. Com a API desligada, a
página carrega mas avisa que não conseguiu falar com o servidor. A conta ngrok gratuita tem
um túnel por vez: o script se recusa a subir se o túnel de outro projeto (por exemplo o
`delivery-platform`) estiver no ar. Para usar outra URL de API, crie a variável de
repositório `JUDO_CHAT_API_URL` e rode o workflow de novo.

## Como funciona

1. `normalizer.Recognizer` acha nomes de técnica na pergunta: nome oficial, nome da IJF,
   grafias variadas e nomes populares (ambíguos devolvem todas as candidatas). Acha também
   termos de regras, arbitragem e graduação, que só vão ao guardrail.
2. O guardrail classifica a pergunta em `tecnica`, `historia`, `regras` ou `fora` com o
   provedor configurado. Qualquer erro bloqueia a resposta.
3. O provedor configurado responde com instruções e corpus (~46 mil tokens). Na Anthropic,
   o bloco de system fica cacheado por 1 hora; na OpenAI, por 12 horas.

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
