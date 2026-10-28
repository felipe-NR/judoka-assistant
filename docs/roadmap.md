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

## Custo

### Custo medido do guardrail

O README, seção "Custo com OpenAI", ainda dá o custo do guardrail como estimativa (~US$ 0,00014
por pergunta). Desde o PR #26 cada classificação registra os tokens no log; a primeira, em
2026-10-28, teve 1.540 tokens de entrada (US$ 0,000154). A partir de 2026-11-04, com uma
semana de log, rode `scripts/custo_openai.py` como descreve o README e troque a estimativa pela
mediana medida, com o período e o número de classificações.
