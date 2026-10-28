# Arquitetura

Diagramas da arquitetura da proposta A (CAG: o corpus inteiro no contexto, com cache de
prompt). São páginas HTML com SVG embutido; abra no navegador, porque o GitHub mostra só o
código-fonte.

| Arquivo | O que mostra | Tipo |
|-|-|-|
| [`prompt-cag.html`](prompt-cag.html) | As partes do prompt de resposta e onde fica o corte do cache | Layer stack |
| [`pergunta-sequencia.html`](pergunta-sequencia.html) | Uma pergunta da página até a resposta, com as duas chamadas ao provedor | Sequence |
| [`corpus-fluxo.html`](corpus-fluxo.html) | Das fontes e da curadoria até o prefixo e o reconhecedor | Data flow |
| [`producao-implantacao.html`](producao-implantacao.html) | Onde cada parte roda, a entrada pública e o caminho do deploy | Deployment |

## Atualizar

Os quatro arquivos são gerados por `scripts/diagramas_arquitetura.py`, no estilo da skill
diagram-design com a skin padrão. Não edite o HTML à mão: mude o script e gere de novo.

```bash
uv run python scripts/diagramas_arquitetura.py docs/arquitetura
```

Com a skill diagram-design instalada, confira o resultado com os verificadores dela
(`self_check.py` e `verify-geometry.py`) e abra cada página no navegador.
