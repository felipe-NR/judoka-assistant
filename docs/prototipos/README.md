# Protótipos da identidade visual

Páginas estáticas, mobile first, geradas em 2026-10-23 com a skill frontend-design para
definir o visual do chat. Cada uma mostra a mesma conversa de exemplo (uma resposta sobre o
seoi-nage e uma recusa). Abra o arquivo no navegador; só as fontes vêm da internet.

| Rodada | Protótipos | Resultado |
|-|-|-|
| 1 | `1-faixa`, `2-judogi`, `3-tatame` | `1-faixa` descartado; a tipografia do `2-judogi` (Atkinson Hyperlegible e Shippori Mincho B1) ficou |
| 2 | `4-judogi-azul`, `5-judogi-branco`, `6-tatame-kanji` | as observações sobre os três guiaram a rodada 3 |
| 3 | `7-rodape-branco`, `8-abas-no-topo`, `9-flutuante` | `4-judogi-azul` e `9-flutuante` seguem para as misturas |
| 4 | `10-azul-flutuante`, `11-tatame-folha-azul`, `12-azul-pilulas` | misturas do `4-judogi-azul` com o `9-flutuante` |
| 5 | `13-trama-na-moldura`, `14-faixa-do-kanji`, `15-gola` | novas misturas do 4 com o 9; `15-gola` escolhido e implementado no PR #12 |

## Textos reaproveitados

O texto inicial de cada assunto do filtro em `src/judo_chat/static/index.html` junta
trechos dos protótipos:

| Assunto | Texto | Origem |
|-|-|-|
| Técnicas | Kuzushi, tsukuri e kake de cada técnica, com o vídeo oficial do Kodokan quando existe. | passos da resposta do seoi-nage (todos) e "trazem o vídeo oficial quando existe" (`2-judogi`) |
| Regras | Pontuação, shido e hansoku-make, e o que cai no seu próximo exame de faixa. | "com o que cai no seu próximo exame" (`1-faixa`) e o exemplo "O que dá shido?" (`15-gola`) |
| História | De Jigoro Kano e do Kodokan à chegada do judô ao Brasil. | exemplos "Quem foi Jigoro Kano?" (`15-gola`) e "quando o judô chegou ao Brasil?" (`3-tatame`) |
