# Arquitetura

Diagramas da arquitetura CAG (o corpus inteiro no contexto, com cache de prompt). Cada
diagrama tem uma página HTML com SVG embutido, que é a fonte, e um PNG
exportado dela para aparecer aqui no GitHub.

## Anatomia do prompt

As partes do prompt do modelo de resposta e onde fica o corte do cache. O guardrail recebe
outro prompt, sem o corpus.

![Pilha das partes do prompt, com o corte do cache entre o prefixo e a mensagem da pergunta](prompt-cag.png)

## Uma pergunta, ponta a ponta

Uma pergunta da página até a resposta, com as duas chamadas ao provedor: o guardrail, um
classificador pela Decisions API, e o modelo de resposta, que gera o texto pela Responses API.

![Sequência de uma pergunta entre página, API, guardrail e modelo de resposta](pergunta-sequencia.png)

## Do dado ao prefixo

Das fontes e da curadoria até o prefixo e o reconhecedor.

![Fluxo do corpus das fontes até a chamada ao modelo](corpus-fluxo.png)

## Onde roda

Onde cada parte roda, a entrada pública e o caminho do deploy.

![Zonas de implantação: internet pública, GitHub e tailnet com a VM](producao-implantacao.png)

## Componentes

A escolha do CAG e as condições para revê-la estão em
[`../decisoes/0001-manter-cag.md`](../decisoes/0001-manter-cag.md).

### Glossário de técnicas com nomes populares

Cada técnica tem um nome principal e um conjunto de nomes populares. No Brasil é comum uma
técnica ser conhecida pelo nome oficial do Kodokan e também por outro nome, às vezes usado de
forma errada há anos ("ashi barai", "morote seoi-nage", "mata-leão").

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

Cada nome popular é guardado uma única vez, como entidade própria: `{name, technique_ids, kind,
confidence, source, note}`. Um nome com mais de um `technique_ids` é ambíguo (Ashi-barai →
Deashi-harai ou Okuriashi-harai; Seoi; Drop Seoi; Sankaku; Rasteira; Jigoku-jime). O conjunto
`popular_names` de cada técnica é calculado no carregamento, o que evita duas cópias
divergentes.

Regra de classificação, aplicada pelo `scripts/build_glossary.py`:

- Iguala o nome oficial ou o nome da IJF depois da normalização → vai para `aliases`.
- Tem um elemento japonês mas não iguala (truncamento, elemento trocado, nome fora do Kodokan)
  ou é termo de dojô em português → vai para `nomes_populares.yaml`. O build falha se um nome
  do CSV não se encaixar em nenhum dos dois.
- Não tem elemento japonês (Kimura, Side Control) → vai para `english_names` com `usage=bjj`;
  os de uso comum no Brasil também viram nome popular `kind: bjj`.

Política de resposta: o assistente usa o nome oficial e avisa quando o usuário usou um nome
popular. Diante de um nome ambíguo, ele não escolhe em silêncio: apresenta as candidatas com o
que distingue cada uma e responde sobre todas ou pergunta.

### Reconhecimento de nomes

A forma canônica de comparação usa minúsculas, remove diacríticos, espaço e hífen, troca
`ou`→`o`, equaliza o rendaku (barai/harai, gari/kari, gatame/katame, jime/shime etc.) e a
grafia "nague", e colapsa letras dobradas. No texto livre, o reconhecedor procura janelas de
até 6 palavras, fica com a mais longa e descarta palavras de borda que somem na canonização
("é", "ou"). Os casos que a regex do judo-techniques-bot errava estão nos testes.

### Guardrail que falha fechado

O guardrail classifica a pergunta em `tecnica`, `historia`, `regras` ou `fora`. Ele recebe as
próprias instruções, o histórico, a pergunta delimitada em `<pergunta>` (tratada como dado) e
as técnicas e os termos reconhecidos, sem o corpus.

- **OpenAI, a produção:** a Decisions API faz três perguntas na mesma chamada (a categoria, se
  a pergunta pede ajuda para agredir alguém fora do judô e se ela tenta mudar as instruções) e
  devolve probabilidades. A pergunta é bloqueada se uma delas passar do limite configurado.
- **Anthropic:** o Haiku 5.5 com effort `low` devolve a categoria por saída estruturada.

Erro da API, timeout, resposta fora do schema, `stop_reason` diferente de `end_turn` ou
resposta vazia bloqueiam a resposta. Quando o bloqueio vem de falha, a mensagem é de
indisponibilidade, e não de fora do escopo.

Com a Decisions API, na avaliação de 2026-10-14, a latência
mediana caiu de ~4 s para ~0,4 s. Como o modelo não raciocina nem vê o corpus, ele recusava
termos de arbitragem que a pergunta não liga ao judô (as 4 falsas recusas daquela avaliação).
Por isso o reconhecedor também acha os termos de `data/glossario/termos_regras.yaml` e os
envia ao guardrail em `<termos_reconhecidos>`, cada um com o título do documento que o
explica; só o nome do termo não bastou. Como uma injeção que cita um termo podia passar como
`regras`, entrou a pergunta sobre mudar as instruções. Na avaliação de 2026-10-23, a falsa
recusa caiu de 3,1% para 0%, com recusa correta de 100% e nenhum falso aceite adversarial.
Os limites estão em [`../configuracao.md`](../configuracao.md).

### Prompt e cache

O bloco de system (instruções e corpus) tem 90,8 mil caracteres: 124 entradas de glossário (104
técnicas), 41 nomes populares, 4 textos de regras, 3 de história, 11 de graduação e 2 de termos
da FGJ. São cerca de 28 mil tokens no gpt-6-luna, o modelo da produção (log de 2026-10-23), e
46 mil no Haiku 5.5 (2026-10-07).

O bloco é montado uma vez no startup e serializado de forma determinística (ordenado, sem set
iterado sem `sorted`, sem data). Um teste compara os bytes gerados com `PYTHONHASHSEED`
diferentes. As técnicas reconhecidas e os candidatos dos nomes ambíguos vão na mensagem do
usuário, depois do corte do cache.

O Haiku 5.5 não tem fallback no servidor para recusa por política: a recusa vira a mensagem de
indisponibilidade e o log registra a categoria. `fallbacks: "default"` (beta
`server-side-fallback-2026-07-01`) vale para o Sonnet 5.5 e o Opus 5.5; liga com
`JUDO_CHAT_USE_REFUSAL_FALLBACKS`, e a configuração recusa a combinação com o Haiku.

### Avaliação

`tests/eval/cases.yaml` tem 164 perguntas: 129 dentro do escopo (técnica com grafias
variadas, nomes populares e ambíguos, conceitos, regras, história, misto) e 35 fora (25 temas
gerais e 10 adversariais). O reconhecedor roda contra todas sem rede, no CI. Guardrail e
resposta rodam com `pytest -m eval`, com as metas de falso-aceite adversarial igual a 0,
recusa correta de 95% ou mais e falsa recusa de 5% ou menos.

### O que não passa pelo modelo

- **Vídeos:** depois da resposta, o reconhecedor acha as técnicas apresentadas (títulos e
  itens) e a API devolve os vídeos em `video_groups`, com o do Kodokan primeiro. A página os
  põe embaixo da seção de cada técnica.
- **Kanji e pronúncia:** cada grupo de `video_groups` traz o kanji da ficha da FGJ e a
  pronúncia gerada por `pronunciation.py` com as regras de `data/fgj/pronuncia.yaml`, sem
  marcar a tônica. A página mostra a pronúncia acima dos vídeos; o kanji vai numa coluna ao
  lado quando a resposta apresenta uma técnica, e junto dos vídeos de cada uma quando são várias.
- **Relações:** `relations.py` liga contragolpes, variações e combinações a partir dos textos
  da FGJ, dos nomes ("X-gaeshi", "Kuzure-X") e das séries do Projeto Budô. Perguntas sobre
  contragolpes, variações ou combinações levam as fichas das técnicas relacionadas.
- **Conversa:** a página envia as últimas 3 trocas em `history`; o servidor não guarda
  estado. O histórico vai ao modelo como dado, depois do trecho cacheado.

## Atualizar

Os HTML são gerados por `scripts/diagramas_arquitetura.py`, no estilo da skill
diagram-design com a skin padrão. Não edite o HTML à mão: mude o script e gere de novo.

```bash
uv run python scripts/diagramas_arquitetura.py docs/arquitetura
```

Depois exporte os PNG com o `export_png.py` da skill, em escala 2, um por diagrama:

```bash
python3 <skill>/scripts/export_png.py docs/arquitetura/prompt-cag.html docs/arquitetura/prompt-cag.png 2
```

Confira o resultado com os verificadores da skill (`self_check.py` e `verify-geometry.py`)
e olhe cada PNG.
