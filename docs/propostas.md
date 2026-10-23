# Três propostas de assistente de judô em pt-BR

## Contexto

O assistente responde em pt-BR a perguntas em linguagem natural de usuários brasileiros. O escopo se limita a técnicas, história e regras do judô (uma resposta pode cruzar os três temas), e qualquer outro assunto é recusado. As propostas juntam o que as sessões dos repositórios vizinhos relataram em 2026-10-03 e 2026-10-04. A proposta A está implementada neste repositório (ver o README).

| Repo | Oferece | Não oferece |
|-|-|-|
| `judobase` (cliente async da API não oficial da IJF, MIT) | Nomes de técnica da IJF em romaji (`EventTag.name`), código estável (`code_short`, `id_tag`), classe da técnica via `id_groups` e estatística de uso por competição | Texto sobre técnicas, regras ou história, conteúdo em pt-BR. A API vem de engenharia reversa e os termos de uso da IJF não foram verificados. O `ftechique` dos atletas é vocabulário controlado, não traz nomes populares |
| `judo-techniques-bot` (bot do Reddit, regex, sem LLM) | 132 linhas com nome japonês, variantes, nomes em inglês e vídeo (`judo_techniques_bot/data/techniques_fixtures.csv`) | Descrições, regras, história, pt-BR. O LICENSE está vazio: reusar o CSV exige permissão do autor (AbundantSalmon). A regex de reconhecimento casa substrings ("Ko-uchi-gari" dispara O-uchi-gari) |
| `production-agentic-rag-course` (referência de RAG) | Esqueleto FastAPI (lifespan, Depends), guardrail por LLM, busca híbrida no OpenSearch, grafo LangGraph, tracing Langfuse | Avaliação offline, prompts em pt-BR. Os fallbacks do guardrail e do grading falham aberto |

Nenhum repositório tem o texto em pt-BR sobre técnicas, regras e história. Desde 2026-10-05, a fonte primária das técnicas é o Curso de Waza da Federação Gaúcha de Judô (FGJ, 2026), com tradução, descrição Kodokan, princípio e kyo-grupo das 100 técnicas oficiais, importado em `data/fgj/`. Esse corpus foi redigido para a proposta A a partir dos dados locais (`provenance: generated`) e precisa de revisão por alguém do judô.

## Base comum às três propostas

### Glossário de técnicas com nomes populares

Cada técnica tem um nome principal e um conjunto de nomes populares. No Brasil é comum uma técnica ser conhecida pelo nome oficial do Kodokan e também por outro nome, às vezes usado de forma errada há anos ("ashi barai", "morote seoi-nage", "mata-leão").

| Campo | Conteúdo |
|-|-|
| `name` | Nome oficial do Kodokan, nome principal |
| `ijf_name` | Nome curto da IJF quando difere (`Juji-gatame` para `Ude-hishigi-juji-gatame`). É o padrão de competição, não conta como erro |
| `aliases` | Só variantes de grafia: hífen, espaço, caixa, macron, rendaku |
| `popular_names` | Conjunto derivado de `data/glossario/nomes_populares.yaml` |
| `english_names` | `{name, usage: judo/bjj}`; os de BJJ nunca viram base de tradução |
| `name_pt_br`, `description_pt_br`, `provenance` | Texto em pt-BR e sua origem (`generated`, `translated_from_en`, `reviewed`, `web:<url>`) |
| `kind`, `group`, `status` | technique/category/concept/grip; grupo do Kodokan; kodokan/nonstandard/forbidden_ijf |
| `video_url`, `judobase` | Vídeo do CSV do bot; `code_short` e `id_tag` da IJF |

Cada nome popular é guardado uma única vez, como entidade própria: `{name, technique_ids, kind, confidence, source, note}`. Um nome com mais de um `technique_ids` é ambíguo (Ashi-barai → Deashi-harai ou Okuriashi-harai; Seoi; Drop Seoi; Sankaku; Rasteira; Jigoku-jime). O conjunto `popular_names` de cada técnica é calculado no carregamento, o que evita duas cópias divergentes.

Regra de classificação, aplicada pelo `scripts/build_glossary.py`:
- Iguala o nome oficial ou o nome da IJF depois da normalização → vai para `aliases`.
- Tem um elemento japonês mas não iguala (truncamento, elemento trocado, nome fora do Kodokan) ou é termo de dojô em português → vai para `nomes_populares.yaml`. O build falha se um nome do CSV não se encaixar em nenhum dos dois.
- Não tem elemento japonês (Kimura, Side Control) → vai para `english_names` com `usage=bjj`; os de uso comum no Brasil também viram nome popular `kind: bjj`.

Política de resposta: o assistente usa o nome oficial e avisa quando o usuário usou um nome popular. Diante de um nome ambíguo, ele não escolhe em silêncio: apresenta as candidatas com o que distingue cada uma e responde sobre todas ou pergunta.

### Reconhecimento de nomes

A forma canônica de comparação usa minúsculas, remove diacríticos, espaço e hífen, troca `ou`→`o`, equaliza o rendaku (barai/harai, gari/kari, gatame/katame, jime/shime etc.) e a grafia "nague", e colapsa letras dobradas. No texto livre, o reconhecedor procura janelas de até 6 palavras, fica com a mais longa e descarta palavras de borda que somem na canonização ("é", "ou"). Os casos que a regex do bot errava estão nos testes.

### Guardrail que falha fechado

Um classificador (Haiku 5.5 com effort `low`, saída estruturada) devolve `tecnica|historia|regras|fora`. Exceção, timeout, saída fora do schema, `stop_reason` diferente de `end_turn` ou resposta vazia bloqueiam a resposta. Quando o bloqueio vem de falha, a mensagem é de indisponibilidade, e não de fora do escopo. A pergunta vai delimitada em `<pergunta>` e é tratada como dado.

### Avaliação

`tests/eval/cases.yaml` tem 164 perguntas: 129 dentro do escopo (técnica com grafias variadas, nomes populares e ambíguos, conceitos, regras, história, misto) e 35 fora (25 temas gerais e 10 adversariais). O reconhecedor roda contra todas sem rede, no CI. Guardrail e resposta rodam com `pytest -m eval`, com as metas de falso-aceite adversarial igual a 0, recusa correta de 95% ou mais e falsa recusa de 5% ou menos.

## Proposta A: LLM com o corpus inteiro no contexto (implementada)

- **Fluxo:** pergunta → reconhecedor → guardrail (Haiku 5.5) → Haiku 5.5 com instruções e corpus num bloco de system cacheado → resposta. A primeira versão usava o Sonnet 5.5; a troca pelo Haiku 4.5 em 2026-10-04 cortou o custo projetado para 23-30% do anterior, e a troca pelo Haiku 5.5 em 2026-10-07 levou a pergunta com cache quente de ~US$ 0,007 para ~US$ 0,001 (ver README). A produção usa a OpenAI: gpt-6-luna na resposta e guardrail pela Decisions API.
- **Corpus no contexto:** o bloco de system (instruções e corpus) tem 90,8 mil caracteres: 124 entradas de glossário (104 técnicas), 41 nomes populares, 4 textos de regras, 3 de história, 11 de graduação e 2 de termos da FGJ. São 46 mil tokens no Haiku 5.5 (medido em 2026-10-07; 36 mil no Haiku 4.5), abaixo dos 100 mil que mudam a tabela de preço, e cerca de 28 mil no gpt-6-luna, o modelo da produção (log de 2026-10-23).
- **Cache:** o bloco de system é montado uma vez no startup e serializado de forma determinística (ordenado, sem set iterado sem `sorted`, sem data). Um teste compara os bytes gerados com `PYTHONHASHSEED` diferentes. As técnicas reconhecidas e os candidatos dos nomes ambíguos vão na mensagem do usuário, depois do breakpoint. TTL de 1 hora, renovado pelo re-aquecimento (`keepalive.py`) das 07h às 23h; um modelo só para a resposta.
- **Recusa por política do modelo:** o Haiku 5.5 não tem fallback no servidor; a recusa vira a mensagem de indisponibilidade e o log registra a categoria. `fallbacks: "default"` (beta `server-side-fallback-2026-07-01`) vale para o Sonnet 5.5 e o Opus 5.5; ligável em `JUDO_CHAT_USE_REFUSAL_FALLBACKS` ao voltar para o Sonnet 5.5, e a configuração recusa a combinação com o Haiku.
- **Prós:** poucas peças e resposta que cruza temas porque o modelo vê tudo. Atualizar o conteúdo é editar a curadoria e rodar o build.
- **Contras:** o custo cresce com o corpus (o cache reduz a leitura a cerca de 10%). Não escala além do contexto. A citação de fonte é por seção, não por trecho.

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
| Estado | implementada | proposta | proposta |
| Infra | API de LLM | + OpenSearch, embeddings | + LangGraph, Langfuse, snapshot do judobase |
| Chamadas de LLM por pergunta | 2 | 2 | 3-5 |
| Tamanho do corpus | limitado ao contexto | cresce | cresce |
| Cita a fonte | por seção | por trecho | por trecho |
| Estatística de técnicas | não | não | sim |

## Recomendação

Revisada em 2026-10-23, na auditoria pela ótica do CAG (cache-augmented generation). A proposta A já é CAG: o corpus inteiro fica num prefixo cacheado, e o reconhecedor funciona como um retriever lexical que anexa as fichas das técnicas depois desse prefixo. A recomendação anterior ("migrar para a B quando entrarem textos longos") não dizia quando o corpus deixa de caber, e pulava um passo mais barato que a B.

**Manter a A** enquanto as três condições valerem:

1. **Tamanho:** o bloco de system fica abaixo do degrau de preço do provedor. No Haiku 5.5 o degrau é em 100 mil tokens, acima do qual entrada e saída custam 5 vezes mais. Hoje são 46 mil, menos da metade. No gpt-6-luna, confira na tabela de preço da OpenAI se existe degrau por tamanho de prompt antes de usar este limite.
2. **Qualidade:** a avaliação (`pytest -m eval`) passa nas metas: falso-aceite adversarial 0, recusa correta de 95% ou mais e falsa recusa de 5% ou menos. Na avaliação de 2026-10-23 os resultados foram 0, 100% e 0%.
3. **Custo:** a pergunta com cache quente continua barata. Na Anthropic, a faixa medida está no README (~US$ 0,001 por pergunta), e o re-aquecimento segura a leitura do prefixo em 10% do preço de entrada. Na OpenAI, que é a produção, essa faixa ainda não foi medida: o primeiro passo é somar `cache_read` e `cache_write` dos logs de um dia com o TTL de 12 horas.

**Primeiro passo quando uma condição falhar: A com pré-filtro lexical por tema.** O corpus é dividido por tema (técnicas, regras, história, graduação), e cada tema vira um prefixo cacheado próprio. A pergunta só leva o prefixo dos temas que o guardrail e o reconhecedor apontarem. O guardrail já classifica em `tecnica`, `historia` e `regras`, mas não separa graduação: perguntas de faixa e exame voltam como `regras`, então essa categoria leva os prefixos de regras e de graduação. O código já faz uma versão pequena disso: `_belt_documents` (`src/judo_chat/answer.py`) acha as faixas citadas na pergunta e repete o documento delas depois do breakpoint. A busca continua lexical, sem modelo de embeddings: as variações de nome do judô (nomes populares, grafias, rendaku), único ponto em que embeddings ajudariam, já estão curadas em `nomes_populares.yaml` e no reconhecedor. Custos a medir antes de adotar:

- vários prefixos gravam no cache separadamente, e a pergunta que cruza temas lê mais de um;
- uma pergunta mista classificada num tema só perde contexto, o que a avaliação precisa cobrir com os casos "misto".

**Migrar para a B** só quando um tema sozinho não couber num prefixo (regulamento completo em várias edições, textos longos de história) ou quando a citação precisar apontar o trecho em vez da seção. A B traz índice, ingestão e avaliação de retrieval para manter.

**Adotar a C** só se as perguntas estatísticas entrarem no produto.

Referências da auditoria: "Don't Do RAG" (Chan et al., WWW Companion '25, arXiv 2412.15605), que restringe o CAG a bases pequenas e viu o BM25 vencer na maior base testada (85 mil tokens); e "RAG Está Morto?" (akitaonrails.com, 2026-04-06), que defende um retriever lexical de alto recall com o modelo filtrando o contexto, e embeddings só onde a busca lexical falhar.

## Pendências

- **Licença:** pedir ao autor do judo-techniques-bot permissão para usar o CSV (o glossário gerado deriva dele) e verificar os termos de uso do data.ijf.org.
- **Revisão de conteúdo:** todas as descrições, regras e textos de história estão com `provenance: generated`. Foram conferidos na web, em 2026-10-04, só o retorno do yuko em 2025 e os tempos de imobilização (5, 10 e 20 segundos).
- **Lista do Kodokan:** confirmada em 2026-10-05 pela lista oficial da FECJU (100 técnicas: 68 nage-waza e 32 katame-waza), que bate com a classificação do corpus em todas. As formas curtas da IJF para as chaves de braço fora da amostra (Ude-gatame, Hiza-gatame, Waki-gatame, Hara-gatame, Ashi-gatame, Te-gatame, Sankaku-gatame) continuam sem confirmação.
- **Vídeos:** 98 técnicas têm vídeo do canal do Kodokan, listado primeiro. Na FECJU, o link do Osoto-guruma aponta para o vídeo do O-guruma e o do Sasae-tsurikomi-ashi não é vídeo; essas duas ficam só com o vídeo do CSV do bot.
- **Mecânica revisada:** 18 fichas reescritas e revisadas pela sessão do judo-techniques-bot em 2026-10-05; o Harai-tsurikomi-ashi e o pé exato do Okuriashi-harai ficaram com confiança baixa e devem ser conferidos nos vídeos do Kodokan.
- **Nomes populares de confiança média ou baixa:** conferir nas fontes autorizadas pelo usuário (sites das federações estaduais, Projeto Budô, @rafaelsilvajudo, @judoparatodosoficial). Reverse seoi-nage, Yagura-nage e Jigoku-jime continuam sem classificação oficial segura.
- **Vídeo removido:** a linha "Kake" do CSV do bot apontava para um vídeo sem relação com judô (`dQw4w9WgXcQ`).

Os arquivos de evidência das sessões estão em `docs/glossario/`: `judobase_tag_mapping.csv` (96 rótulos da IJF com o casamento com o CSV do bot) e `match_test.py` (teste da regex do bot, roda a partir da raiz do judo-techniques-bot).
