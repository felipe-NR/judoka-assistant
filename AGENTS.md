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

O deploy da API é automático: cada push no `main` que mexe no backend passa pelos testes e
é instalado na VM pelo `.github/workflows/deploy.yml`, que chama
`/usr/local/sbin/judoka-deploy <commit>` (`deploy/judoka-deploy`) por SSH dentro da tailnet.
Merge no `main` é deploy em produção. A página sai pelo `pages.yml`. A configuração da VM, da
tailnet e dos secrets está no README, seção "Deploy automático".
