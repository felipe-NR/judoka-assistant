# Validações externas

O que só uma pessoa ou fonte fora do repositório pode confirmar: o autor de um dado, alguém do
judô, a FGJ, a IJF, o Kodokan. Este arquivo é a fonte da verdade sobre essas confirmações.
Cada entrada diz o que falta confirmar, com quem, e o que já foi confirmado, com fonte e data.

Enquanto uma entrada está pendente, o trabalho que depende dela fica aqui e não entra no
`docs/roadmap.md`. Quando ela é confirmada, a entrada registra a fonte e a data, e o trabalho
que ela libera vira um item do roadmap.

## Pendentes

### Licença dos dados de terceiros

- **Falta:** permissão do autor do judo-techniques-bot (AbundantSalmon) para usar o CSV, do
  qual o glossário gerado deriva. O LICENSE do repositório dele está vazio. Falta também
  verificar os termos de uso do data.ijf.org.
- **Desde:** 2026-10-04.

### Revisão do conteúdo gerado

- **Falta:** revisão por alguém do judô das descrições, regras e textos de história com
  `provenance: generated`.
- **Confirmado:** na web, em 2026-10-04, o retorno do yuko em 2025 e os tempos de imobilização
  (5, 10 e 20 segundos).

### Nomes curtos da IJF para as chaves de braço

- **Falta:** confirmar as formas curtas da IJF fora da amostra: Ude-gatame, Hiza-gatame,
  Waki-gatame, Hara-gatame, Ashi-gatame, Te-gatame e Sankaku-gatame.
- **Confirmado:** em 2026-10-05, a lista oficial da FECJU (100 técnicas: 68 nage-waza e 32
  katame-waza) bate com a classificação do corpus em todas.

### Mecânica de confiança baixa

- **Falta:** conferir nos vídeos do Kodokan o Harai-tsurikomi-ashi e o pé exato do
  Okuriashi-harai.
- **Confirmado:** 18 fichas reescritas e revisadas pela sessão do judo-techniques-bot em
  2026-10-05.

### Nomes populares de confiança média ou baixa

- **Falta:** conferir nas fontes autorizadas pelo usuário (sites das federações estaduais,
  Projeto Budô, @rafaelsilvajudo, @judoparatodosoficial). Reverse seoi-nage, Yagura-nage e
  Jigoku-jime continuam sem classificação oficial segura.

### Tônica na pronúncia

- **Falta:** a regra ou a fonte da sílaba tônica dos nomes. A tabela da FGJ
  (`data/fgj/pronuncia.yaml`) acentua os exemplos (TCHIKAMÁ, UÁZA) sem dizer a regra, e a
  pronúncia gerada por `src/judo_chat/pronunciation.py` sai sem tônica ("SSEOI NAGUE", e não o
  "SSEÔI NAGUE" das propostas de design). Pode vir da FGJ ou de uma lista revisada por técnica.
- **Libera:** marcar a tônica na pronúncia.
- **Desde:** 2026-10-28.

### SH e TS na pronúncia

- **Falta:** confirmar com a FGJ como escrever SH e TS. A tabela não cobre essas combinações, e
  aplicar as regras dela letra a letra daria "SSRIRO" para SHIRO e "TSSURI" para TSURI. A
  pronúncia gerada mantém as duas como estão (KAMI SHIRO GATAME, TSURIKOMI GOSHI), uma decisão
  provisória deste repositório e não da FGJ.
- **Libera:** ajustar `src/judo_chat/pronunciation.py`, se a resposta for outra.
- **Desde:** 2026-10-28.

### Kuzushi, tsukuri e kake por técnica

- **Falta:** uma fonte que descreva as três fases das outras técnicas de projeção. A FGJ não
  separa as fases, e o prompt não deixa o modelo dividir a descrição dela por conta própria.
  Fontes candidatas, levantadas na web em 2026-10-28:
  - Gomes et al. (2009), [Golpe de judô o soto gari: validação de lista de
    checagem](https://portalrevistas.ucb.br/index.php/RBCM/article/download/1032/1442), Revista
    Brasileira de Ciência e Movimento 17(4): o kuzushi do Osoto-gari separado, o tsukuri e o kake
    juntos. Licença não verificada. O mesmo grupo validou uma lista do Tai-otoshi (Academos,
    2008), não consultada.
  - Daigo, Kodokan Judo: Throwing Techniques (Kodansha, 2005): cobre as técnicas de projeção do
    Kodokan, mas não deu para confirmar se separa as fases. Livro pago, sem licença de reuso.
  - Nippon Budokan, guia de ensino de judô, capítulo III: descreve poucas projeções básicas
    (Hiza-guruma, por exemplo) com a direção do kuzushi e o tai-sabaki, sem as três fases
    nomeadas.
  - O site do Kodokan não tem página por técnica, só a lista com os vídeos.
- **Confirmado:** em 2026-10-28, as seis te-waza do gokyo (Seoi-nage, Tai-otoshi, Kata-guruma,
  Sukui-nage, Uki-otoshi e Sumi-otoshi), com o texto em português de Tagusari, Santos e Tani
  (2016), [Análise da complexidade das técnicas de te waza do judô pertencentes ao
  gokyo](https://doi.org/10.4025/jphyseduc.v27i1.2756), Journal of Physical Education 27, e2756,
  CC BY 4.0. Estão em `data/fases/tagusari_2016.yaml`, e a resposta as mostra em três passos.
- **Libera:** mais técnicas de nage-waza em três passos, no mesmo formato. O katame-waza não
  segue essa sequência. Com a maior parte das técnicas coberta, a abertura de Técnicas em
  `src/judo_chat/static/index.html` pode voltar a citar as três fases.
- **Desde:** 2026-10-28.

## Confirmadas

### Vídeos do Kodokan

98 técnicas têm vídeo do canal do Kodokan, listado primeiro (2026-10-05). Na FECJU, o link do
Osoto-guruma aponta para o vídeo do O-guruma e o do Sasae-tsurikomi-ashi não é vídeo; essas
duas ficam só com o vídeo do CSV do bot.

### Vídeo sem relação com judô

A linha "Kake" do CSV do bot apontava para um vídeo sem relação com judô (`dQw4w9WgXcQ`) e foi
removida (2026-10-04).

## Evidências

Os arquivos de evidência das sessões estão em `docs/glossario/`: `judobase_tag_mapping.csv`
(96 rótulos da IJF com o casamento com o CSV do bot) e `match_test.py` (teste da regex do bot,
roda a partir da raiz do judo-techniques-bot).
