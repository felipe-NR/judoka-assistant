# Roadmap

Trabalho identificado e ainda não feito. Cada item vira um PR próprio. Os itens abaixo
surgiram em 2026-10-23, no redesenho da página de chat (PR #12), menos a tônica da pronúncia,
que ficou de fora quando a pronúncia entrou, em 2026-10-28.

## Página e API

### Tônica na pronúncia

A pronúncia de `video_groups[]` (`src/judo_chat/pronunciation.py`) segue as regras de letras
da FGJ, mas não marca a sílaba tônica: sai "SSEOI NAGUE", e as propostas de design mostravam
"SSEÔI NAGUE". A tabela da FGJ acentua os exemplos (TCHIKAMÁ, UÁZA) sem dizer a regra, então a
tônica precisa de outra fonte ou de uma lista revisada por técnica.

### Filtro de assunto que restringe a resposta

Os botões Técnicas, Regras e História só trocam a pergunta de exemplo, porque
`POST /api/perguntar` não recebe o assunto. Para o filtro valer, a API precisa receber o
assunto, e o guardrail ou o prompt da resposta precisam usá-lo. Qualquer mudança nessa rota
continua passando pelo rate limit (`src/judo_chat/question_rate_limit.py`).

### Fontes servidas pela própria página

Shippori Mincho B1 e Atkinson Hyperlegible vêm do Google Fonts, então cada visita faz
requisições a um terceiro. Servir os arquivos junto com a página (`src/judo_chat/static/`)
tira essa dependência.

### Tema escuro

A página anterior seguia `prefers-color-scheme: dark`. A atual tem paleta fixa (tatame,
judogi branco e azul) e precisa de uma versão escura própria.

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
