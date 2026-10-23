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
