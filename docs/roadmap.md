# Roadmap

Trabalho identificado e ainda não feito. Cada item vira um PR próprio. Os itens abaixo
surgiram em 2026-10-23, no redesenho da página de chat (PR #12).

## Página e API

### Pronúncia das técnicas

As propostas de design mostravam "Fala-se SSEÔI NAGUE" abaixo do nome da técnica. A página
ainda não mostra porque a API não envia a pronúncia. Gerar a pronúncia a partir das regras
de `data/fgj/pronuncia.yaml` e enviá-la em `video_groups[]`, como já acontece com o `kanji`.

### Filtro de assunto que restringe a resposta

Os botões Técnicas, Regras e História só trocam a pergunta de exemplo, porque
`POST /api/perguntar` não recebe o assunto. Para o filtro valer, a API precisa receber o
assunto, e o guardrail ou o prompt da resposta precisam usá-lo. Qualquer mudança nessa rota
continua passando pelo rate limit (`src/judo_chat/question_rate_limit.py`).

### Kanji em respostas com várias técnicas

A coluna vertical do kanji só aparece quando a resposta apresenta uma técnica, porque com
várias ela não diria de qual técnica é o kanji. O kanji de cada técnica poderia ir ao lado do
título ou item onde ela é apresentada, no mesmo lugar dos vídeos.

### Fontes servidas pela própria página

Shippori Mincho B1 e Atkinson Hyperlegible vêm do Google Fonts, então cada visita faz
requisições a um terceiro. Servir os arquivos junto com a página (`src/judo_chat/static/`)
tira essa dependência.

### Tema escuro

A página anterior seguia `prefers-color-scheme: dark`. A atual tem paleta fixa (tatame,
judogi branco e azul) e precisa de uma versão escura própria.

### Indicador de espera

Enquanto a API responde, só o botão de envio fica desabilitado. O guardrail e a resposta
somam alguns segundos, então uma folha "respondendo…" no lugar da resposta ajudaria.

### Campo de pergunta que cresce com o texto

O campo tem uma linha e não pode ser redimensionado. Perguntas longas rolam dentro dele.
Ele deveria crescer com o texto até o limite de altura (`max-height`).

## Limpeza depois da migração do ngrok para o Tailscale Funnel

- O fallback de `JUDO_CHAT_API_URL` em `.github/workflows/pages.yml` ainda aponta para o
  domínio do ngrok, e o comentário no topo do workflow diz que a API roda localmente pelo
  ngrok.
- O header `ngrok-skip-browser-warning` continua no `fetch` da página
  (`src/judo_chat/static/index.html`), no CORS (`src/judo_chat/main.py`) e no teste de CORS
  (`tests/api/test_ask.py`).
- `start-ngrok.sh`, `stop-ngrok.sh` e a seção "Teste local via ngrok" do README: decidir se
  ficam como ferramenta de teste local ou saem do repositório.

## GitHub Actions

Avisos que aparecem nas annotations dos runs do `deploy.yml` (run 40030107154) e do
`pages.yml` (run 40027259894), em 2026-10-23.

### Actions que ainda rodam em Node.js 20

O GitHub já força essas actions a rodar em Node.js 24 e avisa que o Node.js 20 está
descontinuado
([changelog](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/)).
Subir cada uma para a versão que declara Node.js 24:

- `deploy.yml`: `actions/checkout@v4`, `astral-sh/setup-uv@v6`.
- `pages.yml`: `actions/checkout@v4`, `actions/configure-pages@v5`, `actions/deploy-pages@v4`
  e `actions/upload-artifact@v4`, que vem de dentro do `actions/upload-pages-artifact@v3`.

### `ubuntu-latest` passa a ser Ubuntu 26

Desde 2026-10-19 o rótulo `ubuntu-latest` está migrando para o Ubuntu 26
([runner-images#14748](https://github.com/actions/runner-images/issues/14748)). Os dois
workflows usam esse rótulo. Testar os jobs no Ubuntu 26 ou fixar `ubuntu-24.04` até testar.
