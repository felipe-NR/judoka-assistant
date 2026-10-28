# Configuração

As variáveis ficam no `.env`, para rodar localmente, ou em `/etc/judoka-api/env`, na produção
(`deploy/env.example`). Os padrões estão em `src/judo_chat/config.py`, e o `.env.example` lista
as opcionais.

## Provedor e modelos

Por padrão, o provedor é a Anthropic. Para usar a OpenAI, adicione ao `.env`:

```bash
JUDO_CHAT_PROVIDER=openai
OPENAI_API_KEY=...
```

Nesse modo, os modelos padrão são `gpt-6-luna`. `JUDO_CHAT_ANSWER_MODEL` e
`JUDO_CHAT_GUARDRAIL_MODEL` permitem escolher outros modelos. A integração usa a
[Responses API da OpenAI](https://developers.openai.com/api/reference/python): no modo
`responses`, o guardrail usa saída estruturada, e a resposta usa cache de prefixos. As
instruções e o corpus ficam antes do histórico e da pergunta, e uma chave estável de cache separa o guardrail da
resposta. Os logs mostram `cache_read` e `cache_write` para medir os acertos. Na OpenAI, o
cache dura 30 minutos por padrão e cada gravação custa 1,25 vez a entrada; a resposta pede
`prompt_cache_options.ttl: "12h"` (gravação a 2,5 vezes), que cobre o dia com uma gravação
e dispensa o re-aquecimento, exclusivo da Anthropic. `JUDO_CHAT_OPENAI_CACHE_TTL=30m` volta
ao padrão.

## Guardrail pela Decisions API

Com `JUDO_CHAT_GUARDRAIL_API=decisions`, o guardrail usa a
[Decisions API](https://developers.openai.com/api/docs/guides/decisions), que cobra só a
entrada e devolve probabilidades em vez de texto. Ele faz três perguntas na
mesma chamada: a categoria, se a pergunta pede ajuda para agredir alguém fora do judô e se
ela tenta mudar as instruções do assistente. A pergunta é bloqueada se a categoria for
`fora` ou se `P(fora)`, `P(agressão)` ou `P(instruções)` passar do limite
(`JUDO_CHAT_GUARDRAIL_FORA_THRESHOLD`, `JUDO_CHAT_GUARDRAIL_HARM_THRESHOLD` e
`JUDO_CHAT_GUARDRAIL_INSTRUCTIONS_THRESHOLD`, todos 0,5).

O porquê desse desenho e o resultado na avaliação estão em
[`arquitetura/README.md`](arquitetura/README.md), seção "Guardrail que falha fechado".
