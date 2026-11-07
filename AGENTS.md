# judoka-assistant

## Language

Write commit messages, pull request titles and pull request descriptions in English. Code,
prompts, docs and user-facing text keep the repository's existing language (pt-BR).

## Produção

O repositório no GitHub é público: nada de chaves, `.env`, IPs da tailnet ou outros dados
privados em código, docs, commits ou PRs. A API também é pública (Tailscale Funnel) e cada
pergunta gasta crédito do provedor. Toda rota nova que chame um provedor passa pelo rate
limit (`src/judo_chat/question_rate_limit.py`) e tem timeout. Configuração nova entra em
`Settings` (`src/judo_chat/config.py`); comentários explicam o porquê, com data ou PR.

O deploy da API é automático: cada push no `main` que mexe no backend passa pelos testes e é
instalado na VM pelo `.github/workflows/deploy.yml`, que chama `/usr/local/sbin/judoka-deploy
<commit>` (`deploy/judoka-deploy`) por SSH dentro da tailnet. Merge no `main` é deploy em
produção. Os testes do deploy rodam com `--cov` e falham abaixo do piso `fail_under` do
`pyproject.toml`: teste novo acompanha código novo. O `deploy/install.sh` também baixa a base de países do bloqueio por país
(`scripts/update_geoip.py`). A página sai pelo `pages.yml`, que grava a URL da API no `config.js` e o commit no
`sw.js` do PWA, como versão do cache. A configuração da VM, da tailnet e
dos secrets está em `docs/operacao/deploy.md`, seção "Deploy automático".

Toda mudança no fluxo de deploy (workflows, `deploy/`, configuração da VM, da tailnet ou dos
secrets) atualiza o `docs/operacao/deploy.md` e este arquivo no mesmo PR. Isso inclui trocar o
runner, fixo em `ubuntu-24.04`, ou a versão de uma action.

## Avaliação

O `uv run --env-file .env pytest -m eval` gasta crédito e, com a configuração da produção, grava
`tests/eval/resultado.json` e atualiza a tabela "Números" do README. Mudança em
`tests/eval/cases.yaml`, nos prompts ou nos modelos roda a avaliação de novo e versiona o
resultado no mesmo PR. O `docs.yml` roda o `tests/docs` em PR, sem rede, e aponta números
desalinhados; ele fica fora do deploy para não travar a produção e não detecta mudança de prompt
ou de modelo.

## Dados gerados

Arquivo gerado não se edita à mão. O `data/glossario/tecnicas.yaml` sai do
`scripts/build_glossary.py`, e `data/fgj/*.yaml`, do `scripts/import_fgj.py`; a tabela de
`docs/dados.md` diz o que é gerado. Mude a fonte ou o script, gere de novo e confira no
`git diff` que nada se perdeu. No PR #49, dois vídeos do Kodokan entraram só no
`tecnicas.yaml`, e o build seguinte os apagaria.

## Documentação

Mudança no que a resposta traz (formato, fichas, relações, vídeos, avisos) ou nos dados
atualiza, no mesmo PR, a seção "Como funciona" do `README.md` e os docs que descrevem o ponto.
Antes de abrir o PR, procure o termo afetado em `README.md` e `docs/`: o `tests/docs` só confere
números. Na auditoria de 2026-11-07, o README, `docs/dados.md` e `docs/validacoes-externas.md`
estavam desatualizados depois dos PRs #46 a #50.

## Arquitetura

Os diagramas de `docs/arquitetura/` mostram o prompt e o corte do cache, o caminho de uma
pergunta, a carga do corpus e onde a API roda. Mudança que altere algum desses pontos atualiza
os diagramas no mesmo PR: edite `scripts/diagramas_arquitetura.py`, gere os HTML de novo e
exporte os PNG, como descreve `docs/arquitetura/README.md`. Quando o PR muda o comportamento da
API e nenhum diagrama muda, a descrição do PR diz por quê.
