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
| Técnicas | Descrição do Kodokan e princípio de cada técnica, com o vídeo oficial quando existe. | "trazem o vídeo oficial quando existe" (`2-judogi`); a descrição e o princípio são os textos da FGJ que a resposta cita |
| Regras | Pontuação, shido e hansoku-make, e o que cai no seu próximo exame de faixa. | "com o que cai no seu próximo exame" (`1-faixa`) e o exemplo "O que dá shido?" (`15-gola`) |
| História | De Jigoro Kano e do Kodokan à chegada do judô ao Brasil. | exemplos "Quem foi Jigoro Kano?" (`15-gola`) e "quando o judô chegou ao Brasil?" (`3-tatame`) |

Até 2026-10-28 o texto de Técnicas era "Kuzushi, tsukuri e kake de cada técnica", tirado dos
passos da resposta do seoi-nage. Os protótipos escreveram esses passos à mão, e a resposta não
tinha como cumprir a frase. A base tem as três fases só das seis te-waza do gokyo
(`data/fases/tagusari_2016.yaml`); a fonte que falta para as outras está em
`docs/validacoes-externas.md`, seção "Kuzushi, tsukuri e kake por técnica".

## Decisão: abertura com perguntas sugeridas (2026-10-23)

**Contexto.** A abertura do chat tinha só uma frase por assunto. Os protótipos `1-faixa` e
`2-judogi` abriam com uma frase curta seguida de perguntas prontas para tocar, e o `1-faixa`
punha embaixo de cada pergunta uma linha dizendo de onde sai a resposta.

**Decisão.** A folha de abertura mostra a frase do assunto e três perguntas sugeridas no
desenho do `1-faixa`, com a borda azul do judogi no lugar da dourada. Tocar numa pergunta
envia a pergunta na hora. Trocar o assunto no filtro troca a frase e as perguntas; a folha
some na primeira pergunta, como antes.

**Perguntas.** Só entram perguntas que o corpus responde. A linha de baixo é o grupo do
gokyo (`data/graduacao/gokyo.md`) ou o título do documento em `data/regras` e
`data/historia`:

| Assunto | Pergunta | Linha de baixo |
|-|-|-|
| Técnicas | Como faço o seoi-nage? | Nage-waza, 1.º grupo do gokyo |
| Técnicas | Como entro no uchi-mata? | Nage-waza, 2.º grupo do gokyo |
| Técnicas | Como sair do kesa-gatame? | Katame-waza |
| Regras | O que dá shido? | Penalidades (shido e hansoku-make) |
| Regras | Quanto tempo de osaekomi vale ippon? | Pontuação e duração da luta |
| Regras | Quais técnicas são proibidas? | Técnicas e ações proibidas em competição |
| História | Quem foi Jigoro Kano? | Jigoro Kano e a fundação do Kodokan |
| História | Quando o judô chegou ao Brasil? | O judô no Brasil |
| História | Desde quando o judô é olímpico? | O judô nos Jogos Olímpicos e a IJF |

**Consequências.** Cada toque numa sugestão é uma pergunta paga ao provedor e conta no rate
limit, como uma pergunta digitada. Se um documento do corpus mudar de título ou sair, a lista
`STARTERS` em `src/judo_chat/static/index.html` precisa acompanhar.
