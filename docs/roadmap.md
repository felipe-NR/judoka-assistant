# Roadmap

Trabalho identificado e ainda não feito. Cada item vira um PR próprio. Os itens abaixo
surgiram em 2026-10-23, no redesenho da página de chat (PR #12).

Só entra aqui o que não depende de validação externa. O trabalho que espera a confirmação de
uma fonte de fora fica em [`validacoes-externas.md`](validacoes-externas.md) e vem para cá
quando a confirmação chega.

## Página e API

### Filtro de assunto que restringe a resposta

Os botões Técnicas, Regras e História só trocam a pergunta de exemplo, porque
`POST /api/perguntar` não recebe o assunto. Para o filtro valer, a API precisa receber o
assunto, e o guardrail ou o prompt da resposta precisam usá-lo. Qualquer mudança nessa rota
continua passando pelo rate limit (`src/judo_chat/question_rate_limit.py`).

### Fontes servidas pela própria página

Shippori Mincho B1 e Atkinson Hyperlegible vêm do Google Fonts, então cada visita faz
requisições a um terceiro. Servir os arquivos junto com a página (`src/judo_chat/static/`)
tira essa dependência.

## GitHub Actions

### Runners no Ubuntu 26

Desde 2026-10-19 o rótulo `ubuntu-latest` está migrando para o Ubuntu 26
([runner-images#14748](https://github.com/actions/runner-images/issues/14748)), e os dois
workflows fixam `ubuntu-24.04` desde 2026-10-28. Eles só rodam no push no `main`, então testar
no Ubuntu 26 direto neles seria fazer deploy a partir dele. O job `test` pode ser testado antes
num branch, com `ubuntu-26.04` e um gatilho de `pull_request`; os jobs que fazem deploy só
trocam depois disso.
