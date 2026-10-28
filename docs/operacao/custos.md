# Custos

Quanto cada pergunta custa em cada provedor e como medir de novo. A produção usa a OpenAI.

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

## Re-aquecimento do cache da Anthropic

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
