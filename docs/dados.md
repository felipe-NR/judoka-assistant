# Dados

De onde vem o corpus, o que se edita à mão e como gerar o glossário. A fonte de cada dado e
o que ainda falta confirmar com fontes externas estão em
[`validacoes-externas.md`](validacoes-externas.md).

| Caminho | Conteúdo | Editar? |
|-|-|-|
| `data/curadoria/*.yaml` | Nome oficial, grupo, status e textos pt-BR de cada técnica | Sim |
| `data/glossario/nomes_populares.yaml` | Nomes populares, com as técnicas a que se referem | Sim |
| `data/glossario/termos_regras.yaml` | Termos de regras, arbitragem e graduação que o guardrail recebe; cada um precisa aparecer no documento indicado | Sim |
| `data/regras/*.md`, `data/historia/*.md` | Textos de regras e história | Sim |
| `data/graduacao/*.md` | Exames de faixa (cinza a marrom), Gokyo, sequências e contragolpes, do Projeto Budô | Sim |
| `docs/fontes/fecju_kodokan_videos.csv` | Vídeos do canal do Kodokan listados pela FECJU | Sim |
| `data/fgj/*.yaml` | Fonte primária: tradução, descrição Kodokan, princípio, kyo-grupo e kanji das 100 técnicas, glossário e pronúncia da FGJ | Não, gerado por `scripts/import_fgj.py` |
| `data/glossario/tecnicas.yaml` | Glossário final | Não, é gerado |

Depois de editar a curadoria, gere o glossário de novo (o script lê o CSV do
`judo-techniques-bot` na pasta vizinha):

```bash
uv run python scripts/build_glossary.py
```

O build falha quando um nome do CSV não é grafia do nome oficial nem consta de
`nomes_populares.yaml`, quando uma linha das fontes fica sem destino ou quando duas
técnicas disputam o mesmo nome.

A fonte primária das técnicas é o Curso de Waza da Federação Gaúcha de Judô (FGJ, 2026),
importado com `uv run --with pdfplumber python scripts/import_fgj.py CURSO.pdf LISTA_KANJI.pdf`.
O texto da FGJ é usado sem edição; o que não vem dela segue `docs/guia-estilo-ptbr.md`, e
`tests/unit/test_corpus_style.py` pega regressões. As fichas de técnica estão com `provenance: generated`; os exames de faixa
trazem a URL da página do Projeto Budô de onde vieram.
