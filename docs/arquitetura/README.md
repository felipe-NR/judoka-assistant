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
