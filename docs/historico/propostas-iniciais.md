# Propostas iniciais

Registro das três propostas de assistente de judô, escritas em 2026-10-03 e 2026-10-04. Este
arquivo não é atualizado. A proposta A foi a escolhida e está implementada; como ela funciona
hoje está em [`../arquitetura/README.md`](../arquitetura/README.md), e as condições para
manter essa escolha estão em [`../decisoes/0001-manter-cag.md`](../decisoes/0001-manter-cag.md).

## Contexto

O assistente responde em pt-BR a perguntas em linguagem natural de usuários brasileiros. O escopo se limita a técnicas, história e regras do judô (uma resposta pode cruzar os três temas), e qualquer outro assunto é recusado. As propostas juntam o que as sessões dos repositórios vizinhos relataram em 2026-10-03 e 2026-10-04.

| Repo | Oferece | Não oferece |
|-|-|-|
| `judobase` (cliente async da API não oficial da IJF, MIT) | Nomes de técnica da IJF em romaji (`EventTag.name`), código estável (`code_short`, `id_tag`), classe da técnica via `id_groups` e estatística de uso por competição | Texto sobre técnicas, regras ou história, conteúdo em pt-BR. A API vem de engenharia reversa e os termos de uso da IJF não foram verificados. O `ftechique` dos atletas é vocabulário controlado, não traz nomes populares |
| `judo-techniques-bot` (bot do Reddit, regex, sem LLM) | 132 linhas com nome japonês, variantes, nomes em inglês e vídeo (`judo_techniques_bot/data/techniques_fixtures.csv`) | Descrições, regras, história, pt-BR. O LICENSE está vazio: reusar o CSV exige permissão do autor (AbundantSalmon). A regex de reconhecimento casa substrings ("Ko-uchi-gari" dispara O-uchi-gari) |
| `production-agentic-rag-course` (referência de RAG) | Esqueleto FastAPI (lifespan, Depends), guardrail por LLM, busca híbrida no OpenSearch, grafo LangGraph, tracing Langfuse | Avaliação offline, prompts em pt-BR. Os fallbacks do guardrail e do grading falham aberto |

Nenhum repositório tinha o texto em pt-BR sobre técnicas, regras e história. Desde 2026-10-05, a fonte primária das técnicas é o Curso de Waza da Federação Gaúcha de Judô (FGJ, 2026), importado em `data/fgj/`.

As três propostas compartilham o glossário com nomes populares, o reconhecimento de nomes, o guardrail que falha fechado e a avaliação, descritos em [`../arquitetura/README.md`](../arquitetura/README.md).

## Proposta A: LLM com o corpus inteiro no contexto (escolhida)

- **Fluxo:** pergunta → reconhecedor → guardrail → modelo de resposta com instruções e corpus num bloco de system cacheado → resposta.
- **Prós:** poucas peças e resposta que cruza temas porque o modelo vê tudo. Atualizar o conteúdo é editar a curadoria e rodar o build.
- **Contras:** o custo cresce com o corpus (o cache reduz a leitura a cerca de 10%). Não escala além do contexto. A citação de fonte é por seção, não por trecho.

### Troca de modelos

- A primeira versão usava o Sonnet 5.5 nas duas chamadas.
- Em 2026-10-04, a troca pelo Haiku 4.5 cortou o custo projetado para 23-30% do anterior.
- Em 2026-10-07, a troca pelo Haiku 5.5 levou a pergunta com cache quente de ~US$ 0,007 para ~US$ 0,001.
- A produção passou para a OpenAI: gpt-6-luna na resposta e guardrail pela Decisions API.

## Proposta B: RAG clássico com busca híbrida

- **Fluxo:** pergunta → reconhecedor → guardrail → expansão de consulta → busca híbrida (BM25 com analyzer `portuguese` + vetor, fundidos por RRF) filtrada pelo tema → top-k trechos → resposta citando os trechos.
- **Expansão pelo glossário:** os nomes populares e as grafias reconhecidas são reescritos para o nome oficial antes da busca, e a ficha da técnica entra direto no contexto pelo `id`. Isso resolve o caso em que "ashi barai" não aparece em nenhum trecho do regulamento.
- **Stack:** OpenSearch seguindo `src/services/opensearch/index_config_hybrid.py` do curso com o analyzer trocado; embeddings multilíngues (jina-embeddings-v3 via API ou bge-m3 local); chunk por ficha de técnica e por artigo de regra. Docling só para o PDF do regulamento.
- **Prós:** o corpus pode crescer (regulamentos de vários anos, textos longos de história) e a resposta cita o trecho.
- **Contras:** índice e pipeline de ingestão para manter. Exige avaliação de retrieval (recall@k), a ser acrescentada aos casos de avaliação.

## Proposta C: RAG agentic com roteamento (LangGraph)

- **Fluxo:** o grafo do curso adaptado: guardrail → roteador → tools → grading por documento → rewrite (no máximo 2 tentativas) → geração → checagem de grounding.
- **Tools:** `ficha_tecnica(nome)` (consulta o reconhecedor e devolve a ficha, incluindo os candidatos de um nome ambíguo); `buscar_corpus(tema, consulta)` (a busca da proposta B); `estatistica_tecnica(code_short, competicao?)` (uso das técnicas nos eventos do judobase, a partir de um snapshot periódico ligado ao glossário pelo `code_short`).
- **Correções ao copiar o curso:** fallbacks que falham fechado, prompts e mensagens em pt-BR, remoção do código morto `DECISION_PROMPT` e grading por documento.
- **Prós:** recusa auditável no trace; combina texto com estatística ("qual técnica mais pontuou nos Jogos de Paris").
- **Contras:** 3-5 chamadas de LLM por pergunta; mais peças; depende da API instável do judobase.

## Comparação

| | A | B | C |
|-|-|-|-|
| Infra | API de LLM | + OpenSearch, embeddings | + LangGraph, Langfuse, snapshot do judobase |
| Chamadas de LLM por pergunta | 2 | 2 | 3-5 |
| Tamanho do corpus | limitado ao contexto | cresce | cresce |
| Cita a fonte | por seção | por trecho | por trecho |
| Estatística de técnicas | não | não | sim |
