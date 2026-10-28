# 0001: Manter o CAG

- **Estado:** aceita.
- **Data:** 2026-10-23, na auditoria pela ótica do CAG (cache-augmented generation).

## Contexto

O assistente segue a proposta A de [`../historico/propostas-iniciais.md`](../historico/propostas-iniciais.md):
o corpus inteiro fica num prefixo cacheado, e o reconhecedor funciona como um retriever lexical
que anexa as fichas das técnicas depois desse prefixo. A recomendação anterior ("migrar para a B
quando entrarem textos longos") não dizia quando o corpus deixa de caber, e pulava um passo mais
barato que a B.

## Decisão

Manter o CAG enquanto as três condições valerem:

1. **Tamanho:** o bloco de system fica abaixo do degrau de preço do provedor. No gpt-6-luna, o
   modelo da produção, o degrau é em 272 mil tokens de entrada, acima do qual a entrada custa 2
   vezes mais e a saída 1,5 vez (tabela da OpenAI conferida em 2026-10-23). Hoje são cerca de 28
   mil, perto de 10% do degrau. No Haiku 5.5 o degrau é em 100 mil tokens, acima do qual entrada
   e saída custam 5 vezes mais; hoje são 46 mil.
2. **Qualidade:** a avaliação (`pytest -m eval`) passa nas metas: falso-aceite adversarial 0,
   recusa correta de 95% ou mais e falsa recusa de 5% ou menos. Na avaliação de 2026-10-23 os
   resultados foram 0, 100% e 0%.
3. **Custo:** a pergunta com cache quente continua barata. Na OpenAI, que é a produção, ela
   custa ~US$ 0,0004 e a gravação do prefixo ~US$ 0,007 (medido em 2026-10-28); na Anthropic,
   ~US$ 0,001 por pergunta. As faixas estão no README, seções "Custo com OpenAI" e "Custo com
   Anthropic".

## Quando uma condição falhar

**Primeiro passo: pré-filtro lexical por tema.** O corpus é dividido por tema (técnicas, regras,
história, graduação), e cada tema vira um prefixo cacheado próprio. A pergunta só leva o prefixo
dos temas que o guardrail e o reconhecedor apontarem. O guardrail já classifica em `tecnica`,
`historia` e `regras`, mas não separa graduação: perguntas de faixa e exame voltam como `regras`,
então essa categoria leva os prefixos de regras e de graduação. O código já faz uma versão
pequena disso: `_belt_documents` (`src/judo_chat/answer.py`) acha as faixas citadas na pergunta e
repete o documento delas depois do breakpoint. A busca continua lexical, sem modelo de
embeddings: as variações de nome do judô (nomes populares, grafias, rendaku), único ponto em que
embeddings ajudariam, já estão curadas em `nomes_populares.yaml` e no reconhecedor. Custos a
medir antes de adotar:

- vários prefixos gravam no cache separadamente, e a pergunta que cruza temas lê mais de um;
- uma pergunta mista classificada num tema só perde contexto, o que a avaliação precisa cobrir
  com os casos "misto".

**Migrar para a proposta B (RAG com busca híbrida)** só quando um tema sozinho não couber num
prefixo (regulamento completo em várias edições, textos longos de história) ou quando a citação
precisar apontar o trecho em vez da seção. A B traz índice, ingestão e avaliação de retrieval
para manter.

**Adotar a proposta C (RAG agentic)** só se as perguntas estatísticas entrarem no produto.

## Referências

- "Don't Do RAG" (Chan et al., WWW Companion '25, arXiv 2412.15605), que restringe o CAG a bases
  pequenas e viu o BM25 vencer na maior base testada (85 mil tokens).
- "RAG Está Morto?" (akitaonrails.com, 2026-04-06), que defende um retriever lexical de alto
  recall com o modelo filtrando o contexto, e embeddings só onde a busca lexical falhar.
