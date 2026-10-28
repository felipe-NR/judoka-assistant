"""Gera os diagramas de arquitetura de docs/arquitetura/ (skin padrão da skill diagram-design).

Uso: uv run python scripts/diagramas_arquitetura.py docs/arquitetura
"""

# O arquivo é quase todo marcação SVG e texto corrido, que ficam mais legíveis numa linha só.
# ruff: noqa: E501

import sys
from html import escape
from pathlib import Path

OUT = Path(sys.argv[1])

PAPER, PAPER2 = "#f5f5f5", "#ececec"
INK, MUTED, SOFT = "#2d3142", "#4f5d75", "#5a6580"
ACCENT, LINK = "#bf4520", "#2e5aa8"
ACCENT_TINT = "rgba(191,69,32,0.08)"
WHITE = "#ffffff"
SANS = "'Geist', sans-serif"
MONO = "'Geist Mono', monospace"
SERIF = "'Instrument Serif', 'Noto Serif', serif"


def ink(a):
    return f"rgba(45,49,66,{a})"


def esc(t):
    return escape(t, quote=True)


def text(x, y, s, size, fill=INK, family=SANS, anchor="start", weight=None, spacing=None, italic=False):
    attrs = [f'x="{x}"', f'y="{y}"', f'fill="{fill}"', f'font-size="{size}"', f'font-family="{family}"']
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if spacing:
        attrs.append(f'letter-spacing="{spacing}"')
    if italic:
        attrs.append('font-style="italic"')
    return f"<text {' '.join(attrs)}>{esc(s)}</text>"


def mono_w(s, size=8, spacing=0.08):
    """Largura do texto mono pelo orçamento do style guide (0,62em) mais o tracking."""
    return len(s) * size * (0.62 + spacing)


def label(cx, y_line, s, fill=MUTED, above=True):
    """Rótulo de seta com máscara opaca 8px acima da linha (regra 2)."""
    w = int(mono_w(s) + 8 + 3) // 4 * 4
    top = y_line - 20 if above else y_line + 8
    return f'<rect x="{cx - w / 2}" y="{top}" width="{w}" height="12" rx="2" fill="{PAPER}"/>' + text(
        cx, top + 9, s, 8, fill, MONO, "middle", spacing="0.08em"
    )


def side_label(x_left, cy, s, fill=MUTED):
    """Rótulo ao lado de um segmento vertical, começando em x_left."""
    w = int(mono_w(s) + 8 + 3) // 4 * 4
    return f'<rect x="{x_left}" y="{cy - 6}" width="{w}" height="12" rx="2" fill="{PAPER}"/>' + text(
        x_left + w / 2, cy + 3, s, 8, fill, MONO, "middle", spacing="0.08em"
    )


def node(x, y, w, h, tag, name, sub, kind="backend", name_y=None):
    fills = {
        "backend": (WHITE, INK, ink(0.40), MUTED),
        "focal": (ACCENT_TINT, ACCENT, "rgba(191,69,32,0.50)", ACCENT),
        "external": (ink(0.03), ink(0.30), ink(0.22), SOFT),
        "input": ("rgba(79,93,117,0.10)", SOFT, "rgba(90,101,128,0.40)", SOFT),
    }
    fill, stroke, tag_stroke, tag_fill = fills[kind]
    tw = max(28, int(len(tag) * 7 * 0.7 + 10 + 3) // 4 * 4)
    cx = x + w / 2
    ny = name_y if name_y is not None else y + h / 2 + 4
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>',
        f'<rect x="{x + 8}" y="{y + 8}" width="{tw}" height="12" rx="2" fill="transparent" stroke="{tag_stroke}" stroke-width="0.8"/>',
        text(x + 8 + tw / 2, y + 17, tag, 7, tag_fill, MONO, "middle", spacing="0.08em"),
        text(cx, ny, name, 12, INK, SANS, "middle", weight=600),
    ]
    if sub:
        out.append(text(cx, ny + 15, sub, 9, MUTED, MONO, "middle"))
    return "\n".join(out)


MARKERS = f"""<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>
<marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{LINK}"/></marker>"""


def page(slug, eyebrow, h1, title, desc, width, height, body, note):
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(h1)}</title>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&family=Noto+Serif:ital@0;1&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --color-paper:   {PAPER};
      --color-ink:     {INK};
      --color-muted:   {MUTED};
      --color-accent:  {ACCENT};
      --font-sans:     'Geist', system-ui, sans-serif;
      --font-serif:    'Instrument Serif', 'Noto Serif', serif;
      --font-mono:     'Geist Mono', ui-monospace, monospace;
    }}
    body {{
      font-family: var(--font-sans);
      background: var(--color-paper);
      color: var(--color-ink);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 3rem 2rem;
    }}
    .frame {{ max-width: 1200px; width: 100%; }}
    .diagram-container {{ width: 100%; overflow-x: auto; }}
    .eyebrow {{
      font-family: var(--font-mono);
      font-size: 0.66rem;
      font-weight: 500;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--color-muted);
      margin-bottom: 0.5rem;
    }}
    h1 {{
      font-family: var(--font-serif);
      font-size: clamp(1.5rem, 2.4vw + 0.75rem, 2rem);
      font-weight: 400;
      letter-spacing: -0.02em;
      line-height: 1.15;
      color: var(--color-ink);
      margin-bottom: 1.5rem;
    }}
    .note {{ margin-top: 1.25rem; max-width: 72ch; font-size: 0.9rem; line-height: 1.55; color: var(--color-muted); }}
    .note code {{ font-family: var(--font-mono); font-size: 0.82rem; }}
    svg {{ width: 100%; min-width: {width}px; display: block; }}
    @media print {{
      .diagram-container {{ overflow-x: visible; }}
      svg {{ min-width: 0; }}
    }}
  </style>
</head>
<body>
  <div class="frame">
    <p class="eyebrow">{esc(eyebrow)}</p>
    <h1>{esc(h1)}</h1>
    <div class="diagram-container">
      <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{slug}-title {slug}-desc">
        <title id="{slug}-title">{esc(title)}</title>
        <desc id="{slug}-desc">{esc(desc)}</desc>
        <defs>
{MARKERS}
        </defs>
        <rect width="100%" height="100%" fill="{PAPER}"/>
{body}
      </svg>
    </div>
    <p class="note">{note}</p>
  </div>
</body>
</html>
"""


# ---------------------------------------------------------------- 1. Layer stack
def prompt_layers():
    x0, x1 = 152, 840
    ys = [88, 152, 216, 280, 344]
    h = 64
    layers = [
        ("01", "Instruções", "escopo, recusa, formato da resposta", False),
        ("02", "Corpus inteiro", "técnicas, nomes populares, regras, história, faixas · ~28 mil tokens", True),
        ("03", "Histórico", "últimas 3 trocas da conversa, tratadas como dado", False),
        ("04", "Pergunta", "texto do usuário, até 1000 caracteres", False),
        ("05", "Anexos do reconhecedor", "faixas citadas, técnicas, relações, até 6 fichas", False),
    ]
    b = []
    # Direção (margem esquerda)
    b.append(text(24, 76, "ORDEM NO PROMPT", 8, MUTED, MONO, spacing="0.18em"))
    b.append(text(x0, 76, "PROMPT DO MODELO DE RESPOSTA · RESPONSES API", 8, INK, MONO, spacing="0.18em", weight=600))
    b.append(f'<line x1="72" y1="88" x2="72" y2="400" stroke="{ink(0.30)}" stroke-width="1"/>')
    b.append(f'<polygon points="68,400 76,400 72,408" fill="{MUTED}"/>')
    # Camadas
    for (idx, name, note, focal), y in zip(layers, ys, strict=True):
        if focal:
            b.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="{h}" fill="{ACCENT_TINT}"/>')
            b.append(
                f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="{h}" fill="none" stroke="{ACCENT}" stroke-width="1"/>'
            )
        else:
            b.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="{h}" fill="{WHITE}"/>')
        color = ACCENT if focal else MUTED
        b.append(text(x0 + 16, y + 36, idx, 8, color, MONO, spacing="0.14em", weight=600 if focal else None))
        b.append(text(x0 + 64, y + 38, name, 16, INK, SANS, weight=600))
        b.append(text(x1 - 16, y + 38, note, 10, color, MONO, "end", spacing="0.04em"))
    for y in ys[1:]:
        if y not in (152, 216):
            b.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{ink(0.12)}" stroke-width="1"/>')
    b.append(
        f'<rect x="{x0}" y="88" width="{x1 - x0}" height="320" fill="none" stroke="{ink(0.30)}" stroke-width="1"/>'
    )
    # Corte do cache (2º elemento em destaque)
    b.append(
        f'<line x1="{x0 - 16}" y1="216" x2="856" y2="216" stroke="{ACCENT}" stroke-width="1.6" stroke-dasharray="6,4"/>'
    )
    b.append(text(868, 220, "CORTE DO CACHE", 8, ACCENT, MONO, spacing="0.12em", weight=600))
    # Chaves à direita
    for y_top, y_bot, l1, l2, sub in [
        (92, 208, "PREFIXO", "CACHEADO", "igual sempre"),
        (224, 404, "A CADA", "PERGUNTA", "muda sempre"),
    ]:
        b.append(f'<path d="M 848 {y_top} H 856 V {y_bot} H 848" fill="none" stroke="{MUTED}" stroke-width="1"/>')
        mid = (y_top + y_bot) / 2
        b.append(text(868, mid - 8, l1, 8, MUTED, MONO, spacing="0.14em"))
        b.append(text(868, mid + 4, l2, 8, MUTED, MONO, spacing="0.14em"))
        b.append(text(868, mid + 18, sub, 9, SOFT, MONO))
    # Nota editorial
    b.append(text(x0, 452, "POR QUE ASSIM", 8, MUTED, MONO, spacing="0.18em"))
    b.append(
        text(
            x0,
            476,
            "O que se repete em toda pergunta fica antes do corte e o provedor relê do cache, a 10% do preço de entrada.",
            14,
            INK,
            SERIF,
            italic=True,
        )
    )
    b.append(
        text(
            x0,
            496,
            "O prefixo é montado uma vez na partida e sai sempre com os mesmos bytes; o que muda vai depois.",
            14,
            INK,
            SERIF,
            italic=True,
        )
    )
    b.append(text(x0, 536, "E O GUARDRAIL", 8, MUTED, MONO, spacing="0.18em"))
    for gy, line in (
        (560, "O guardrail não lê este prompt. Pela Decisions API ele recebe as próprias instruções,"),
        (580, "o histórico, a pergunta e as técnicas reconhecidas, sem o corpus, e devolve probabilidades."),
    ):
        b.append(text(x0, gy, line, 14, INK, SERIF, italic=True))
    return page(
        "prompt-cag",
        "Layer stack · Arquitetura CAG",
        "Anatomia do prompt",
        "Anatomia do prompt do judoka-assistant",
        "Pilha das cinco partes do prompt do modelo de resposta: instruções e corpus inteiro no prefixo cacheado, e depois do corte do cache o histórico, a pergunta e os anexos do reconhecedor. O guardrail recebe outro prompt, sem o corpus.",
        960,
        604,
        "\n".join(b),
        "Este é o prompt do modelo de resposta, que gera o texto; na OpenAI ele vai pela Responses API. O guardrail é outra chamada, "
        "um classificador pela Decisions API que não gera texto. Na Anthropic, as duas chamadas usam a Messages API, e o guardrail "
        "devolve a categoria por saída estruturada. "
        "O prefixo (instruções e corpus) é montado por <code>build_system_text</code> na partida da API e não muda entre perguntas. "
        "Na OpenAI, que é a produção, ele fica no cache por 12 horas (<code>prompt_cache_options.ttl</code>); na Anthropic, por 1 hora com "
        "re-aquecimento (<code>keepalive.py</code>). As camadas 03 a 05 são a mensagem do usuário, montada por <code>build_user_message</code>. "
        "Os ~28 mil tokens do corpus são a medida no gpt-6-luna; no Haiku 5.5 são cerca de 46 mil.",
    )


# ---------------------------------------------------------------- 2. Sequence
def question_sequence():
    P, A, G, M = 120, 360, 620, 860
    b = []
    for cx in (P, A, G, M):
        b.append(
            f'<line x1="{cx}" y1="128" x2="{cx}" y2="640" stroke="{ink(0.22)}" stroke-width="1" stroke-dasharray="3,3"/>'
        )
    # Fragmento ALT (atrás das mensagens)
    fx, fy, fw, fh = 88, 360, 804, 264
    b.append(
        f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="4" fill="{ink(0.02)}" stroke="{ink(0.22)}" stroke-width="1"/>'
    )
    b.append(
        f'<rect x="{fx}" y="{fy}" width="40" height="16" rx="2" fill="{PAPER}" stroke="{ink(0.22)}" stroke-width="1"/>'
    )
    b.append(text(fx + 20, fy + 12, "ALT", 8, MUTED, MONO, "middle", spacing="0.12em"))
    for gy, guard in ((392, "[fora do escopo ou falha]"), (464, "[dentro do escopo]")):
        gw = int(mono_w(guard, spacing=0.04) + 8 + 3) // 4 * 4
        b.append(f'<rect x="{fx + 8}" y="{gy - 9}" width="{gw}" height="12" rx="2" fill="{PAPER}"/>')
        b.append(text(fx + 12, gy, guard, 8, MUTED, MONO, spacing="0.04em"))
    b.append(
        f'<line x1="{fx + 8}" y1="444" x2="{fx + fw - 8}" y2="444" stroke="{ink(0.20)}" stroke-width="1" stroke-dasharray="4,3"/>'
    )
    # Barras de ativação
    act = 'fill="rgba(45,49,66,0.06)" stroke="#4f5d75" stroke-width="0.8"'
    b.append(f'<rect x="{A - 4}" y="176" width="8" height="432" {act}/>')
    b.append(f'<rect x="{G - 4}" y="304" width="8" height="32" {act}/>')
    b.append(f'<rect x="{M - 4}" y="492" width="8" height="32" {act}/>')

    def call(x1, x2, y, color, marker, dashed=False, width=1.2):
        dash = ' stroke-dasharray="5,4"' if dashed else ""
        return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="{width}"{dash} marker-end="url(#{marker})"/>'

    def self_loop(y1, y2):
        return f'<path d="M {A + 4} {y1} L {A + 40} {y1} L {A + 40} {y2} L {A + 4} {y2}" fill="none" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>'

    b += [
        call(P, A - 4, 176, LINK, "arrow-link"),
        self_loop(200, 224),
        self_loop(248, 272),
        call(A + 4, G - 4, 304, LINK, "arrow-link"),
        call(G - 4, A + 4, 336, MUTED, "arrow", dashed=True),
        call(A - 4, P, 420, MUTED, "arrow", dashed=True),
        call(A + 4, M - 4, 492, LINK, "arrow-link"),
        call(M - 4, A + 4, 524, MUTED, "arrow", dashed=True),
        self_loop(548, 572),
        call(A - 4, P, 604, ACCENT, "arrow-accent", width=1.4),
    ]
    b += [
        label((P + A) / 2, 176, "POST PERGUNTAR", LINK),
        side_label(A + 48, 212, "PAÍS + LIMITE"),
        side_label(A + 48, 260, "RECONHECEDOR"),
        label((A + G) / 2, 304, "CLASSIFICAR", LINK),
        label((A + G) / 2, 336, "CATEGORIA"),
        label((P + A) / 2, 420, "RECUSA"),
        label((G + M) / 2, 492, "PREFIXO+ANEXOS", LINK),
        label((G + M) / 2, 524, "RESPOSTA"),
        side_label(A + 48, 560, "VÍDEOS + KANJI"),
        label((P + A) / 2, 604, "200 · RESPOSTA", ACCENT),
    ]
    b += [
        node(P - 80, 72, 160, 56, "WEB", "Página", "GitHub Pages", "input"),
        node(A - 80, 72, 160, 56, "API", "API", "FastAPI · VM", "backend"),
        node(G - 80, 72, 160, 56, "CLASSIF", "Guardrail", "Decisions API", "external"),
        node(M - 80, 72, 160, 56, "LLM", "Modelo de resposta", "Responses API · cache", "focal"),
    ]
    # Legenda
    b.append(f'<line x1="56" y1="664" x2="944" y2="664" stroke="{ink(0.10)}" stroke-width="0.8"/>')
    b.append(text(56, 680, "LEGENDA", 8, MUTED, MONO, spacing="0.18em"))
    b.append(
        f'<rect x="56" y="696" width="14" height="10" rx="2" fill="{ACCENT_TINT}" stroke="{ACCENT}" stroke-width="1"/>'
    )
    b.append(text(76, 704, "Ator em foco", 8.5, MUTED))
    b.append(f'<rect x="188" y="692" width="4" height="18" {act}/>')
    b.append(text(200, 704, "Ativação", 8.5, MUTED))
    b.append(
        f'<line x1="300" y1="702" x2="328" y2="702" stroke="{LINK}" stroke-width="1.2" marker-end="url(#arrow-link)"/>'
    )
    b.append(text(336, 704, "Chamada HTTP", 8.5, MUTED))
    b.append(
        f'<line x1="456" y1="702" x2="484" y2="702" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="5,4" marker-end="url(#arrow)"/>'
    )
    b.append(text(492, 704, "Retorno", 8.5, MUTED))
    b.append(
        f'<line x1="592" y1="702" x2="620" y2="702" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#arrow-accent)"/>'
    )
    b.append(text(628, 704, "Resposta final", 8.5, MUTED))
    return page(
        "pergunta-sequencia",
        "Sequence · Arquitetura CAG",
        "Uma pergunta, ponta a ponta",
        "Uma pergunta, ponta a ponta",
        "Sequência de uma pergunta: a página chama a API, que passa pelo bloqueio por país, pelo rate limit e pelo reconhecedor, consulta o guardrail e, dentro do escopo, chama o modelo de resposta com o prefixo cacheado antes de devolver a resposta com vídeos e kanji.",
        1000,
        724,
        "\n".join(b),
        "Só o guardrail e o modelo de resposta chamam um provedor. Na produção (OpenAI), o guardrail é um classificador pela Decisions API, "
        "que devolve probabilidades em vez de texto, e o modelo de resposta gera o texto pela Responses API, com o prefixo no cache. "
        "Na Anthropic, as duas chamadas usam a Messages API. Antes delas, o bloqueio por país responde 403 e o rate limit responde 429, "
        "sem gastar crédito. Se o guardrail falhar, a página recebe a mensagem de indisponibilidade pelo mesmo ramo da recusa. "
        "Vídeos, kanji e pronúncia saem dos dados (<code>video_groups</code>), sem modelo.",
    )


# ---------------------------------------------------------------- 3. Data flow
def corpus_flow():
    label_col_w, slot, right_pad, header_h, lane_h = 140, 112, 28, 36, 80
    lanes = [
        ("CURADORIA", "PESSOAS", "CUR"),
        ("SCRIPTS", "OFFLINE", "SCR"),
        ("API", "NA PARTIDA", "INI"),
        ("API", "POR PERGUNTA", "PRG"),
    ]
    steps = [("01", "FONTE"), ("02", "IMPORTAÇÃO"), ("03", "VERSIONADO"), ("04", "CARGA"), ("05", "PROMPT")]
    focal_step = 4
    n_steps, n_lanes = len(steps), len(lanes)
    W = label_col_w + n_steps * slot + right_pad
    legend_top = header_h + n_lanes * lane_h
    H = legend_top + 80

    def cx(j):
        return label_col_w + j * slot + slot / 2

    def ltop(k):
        return header_h + k * lane_h

    def nx(j):
        return cx(j) - 50

    def ny(k):
        return ltop(k) + 8

    chip_colors = {"FL": "#9c6b50", "DB": "#5e7a9b", "TB": "#b8915a"}
    nodes = [
        (0, 0, "Fontes externas", "FGJ · bot · Kodokan", "PDFs · CSV", None, "FL", False),
        (1, 1, "Importação", "PDF/CSV → YAML", "scripts/import_fgj.py", "FL", "DB", False),
        (0, 2, "Curadoria à mão", "regras · história", "data/curadoria", None, "DB", False),
        (1, 2, "data/ no git", "YAML versionado", "fgj · glossário", "DB", "DB", False),
        (2, 3, "load_corpus", "YAML → Corpus", "+ reconhecedor", "DB", "TB", False),
        (2, 4, "Prefixo", "instruções + corpus", "render_corpus", "TB", "FL", False),
        (3, 3, "Reconhecedor", "técnicas · termos", "fichas e relações", "TB", "FL", False),
        (3, 4, "Chamada ao modelo", "prefixo + anexos", "Responses API", "FL", None, True),
    ]
    b = [
        '<defs><pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
        f'<circle cx="11" cy="11" r="0.8" fill="{ink(0.10)}"/></pattern>'
        f'<marker id="arr-muted" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{MUTED}"/></marker>'
        f'<marker id="arr-accent" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{ACCENT}"/></marker></defs>',
        '<rect width="100%" height="100%" fill="url(#dots)"/>',
    ]
    for k in range(n_lanes):
        if k % 2 == 0:
            b.append(f'<rect x="0" y="{ltop(k)}" width="{W}" height="{lane_h}" fill="{ink(0.018)}"/>')
    for k in range(n_lanes + 1):
        b.append(f'<line x1="0" y1="{ltop(k)}" x2="{W}" y2="{ltop(k)}" stroke="{ink(0.12)}" stroke-width="0.8"/>')
    b.append(
        f'<line x1="{label_col_w}" y1="{header_h}" x2="{label_col_w}" y2="{legend_top}" stroke="{ink(0.12)}" stroke-width="0.8"/>'
    )
    for j, (num, lab) in enumerate(steps):
        focal = j == focal_step
        fill = "rgba(191,69,32,0.20)" if focal else ink(0.12)
        color = ACCENT if focal else INK
        b.append(f'<rect x="{cx(j) - 16}" y="6" width="32" height="16" rx="8" fill="{fill}"/>')
        b.append(text(cx(j), 17, num, 8, color, MONO, "middle", weight=600))
        b.append(text(cx(j), 31, lab, 7, ACCENT if focal else MUTED, MONO, "middle", spacing="0.12em"))
    for k, (l1, l2, _) in enumerate(lanes):
        mid = ltop(k) + lane_h / 2
        b.append(text(label_col_w / 2, mid - 4, l1, 7, MUTED, MONO, "middle", spacing="0.14em"))
        b.append(text(label_col_w / 2, mid + 8, l2, 7, MUTED, MONO, "middle", spacing="0.14em"))

    def mid_y(k):
        return ny(k) + 32

    arrows = []

    def horiz(k, j1, j2):
        arrows.append(
            f'<line x1="{nx(j1) + 100}" y1="{mid_y(k)}" x2="{nx(j2)}" y2="{mid_y(k)}" stroke="{MUTED}" stroke-width="1" marker-end="url(#arr-muted)"/>'
        )

    def vert(j, k1, k2, accent=False):
        color, marker, width = (ACCENT, "arr-accent", 1.2) if accent else (MUTED, "arr-muted", 1)
        arrows.append(
            f'<line x1="{cx(j)}" y1="{ny(k1) + 64}" x2="{cx(j)}" y2="{ny(k2)}" stroke="{color}" stroke-width="{width}" marker-end="url(#{marker})"/>'
        )

    def cross(k1, j1, k2, j2):
        x_end = cx(j2)
        y = mid_y(k1)
        arrows.append(
            f'<path d="M {nx(j1) + 100} {y} H {x_end - 8} Q {x_end} {y} {x_end} {y + 8} V {ny(k2)}" fill="none" stroke="{MUTED}" stroke-width="1" marker-end="url(#arr-muted)"/>'
        )

    cross(0, 0, 1, 1)
    horiz(1, 1, 2)
    vert(2, 0, 1)
    cross(1, 2, 2, 3)
    horiz(2, 3, 4)
    vert(3, 2, 3)
    horiz(3, 3, 4)
    vert(4, 2, 3, accent=True)
    b += arrows
    # Rótulo da seta em foco, ao lado do segmento vertical
    lw = int(mono_w("PREFIXO") + 8 + 3) // 4 * 4
    b.append(f'<rect x="{cx(4) + 8}" y="{ny(3) - 14}" width="{lw}" height="12" rx="2" fill="{PAPER}"/>')
    b.append(text(cx(4) + 8 + lw / 2, ny(3) - 5, "PREFIXO", 8, ACCENT, MONO, "middle", spacing="0.08em"))
    for k, j, title, sub, tool, chip_in, chip_out, focal in nodes:
        x, y = nx(j), ny(k)
        if focal:
            b.append(f'<rect x="{x}" y="{y}" width="100" height="64" rx="6" fill="{PAPER}"/>')
            b.append(
                f'<rect x="{x}" y="{y}" width="100" height="64" rx="6" fill="rgba(191,69,32,0.07)" stroke="{ACCENT}" stroke-width="1"/>'
            )
            role_fill, role_text = "rgba(191,69,32,0.18)", ACCENT
        else:
            b.append(
                f'<rect x="{x}" y="{y}" width="100" height="64" rx="6" fill="{PAPER}" stroke="{ink(0.25)}" stroke-width="1"/>'
            )
            role_fill, role_text = ink(0.12), INK
        b.append(f'<rect x="{x + 4}" y="{y + 4}" width="18" height="10" rx="3" fill="{role_fill}"/>')
        b.append(text(x + 13, y + 11, lanes[k][2], 6, role_text, MONO, "middle", weight=600))
        b.append(text(cx(j), y + 25, title, 9, INK, SANS, "middle", weight=600))
        b.append(text(cx(j), y + 37, sub, 6.5, MUTED, MONO, "middle"))
        b.append(text(cx(j), y + 48, tool, 6.5, SOFT, MONO, "middle"))
        for code, dx in ((chip_in, 4), (chip_out, 80)):
            if code:
                b.append(f'<rect x="{x + dx}" y="{y + 54}" width="16" height="8" rx="3" fill="{chip_colors[code]}"/>')
                b.append(text(x + dx + 8, y + 60, code, 5, WHITE, MONO, "middle", weight=700))
    # Legenda
    rows = [legend_top + 16, legend_top + 37, legend_top + 59]
    b.append(text(24, rows[0] + 3, "ETAPAS", 7, MUTED, MONO, spacing="0.14em"))
    for j, (num, lab) in enumerate(steps):
        x = 144 + j * 112
        focal = j == focal_step
        b.append(
            f'<rect x="{x}" y="{rows[0] - 6}" width="24" height="12" rx="6" fill="{"rgba(191,69,32,0.20)" if focal else ink(0.12)}"/>'
        )
        b.append(text(x + 12, rows[0] + 3, num, 7, ACCENT if focal else INK, MONO, "middle", weight=600))
        b.append(text(x + 30, rows[0] + 3, lab.capitalize(), 7.5, ACCENT if focal else MUTED, SANS))
    b.append(text(24, rows[1] + 3, "TIPO DE DADO", 7, MUTED, MONO, spacing="0.14em"))
    x = 144
    for code, meaning in (("FL", "arquivo ou texto"), ("DB", "YAML em data/"), ("TB", "Corpus em memória")):
        b.append(f'<rect x="{x}" y="{rows[1] - 4}" width="16" height="8" rx="3" fill="{chip_colors[code]}"/>')
        b.append(text(x + 8, rows[1] + 2, code, 5, WHITE, MONO, "middle", weight=700))
        b.append(text(x + 22, rows[1] + 3, meaning, 7.5, MUTED, SANS))
        x += 112
    b.append(text(x + 8, rows[1] + 3, "chip esquerdo = entrada · direito = saída", 6.5, SOFT, MONO))
    b.append(text(24, rows[2] + 3, "FLUXO", 7, MUTED, MONO, spacing="0.14em"))
    b.append(
        f'<line x1="144" y1="{rows[2]}" x2="172" y2="{rows[2]}" stroke="{MUTED}" stroke-width="1" marker-end="url(#arr-muted)"/>'
    )
    b.append(text(180, rows[2] + 3, "repasse de dados", 7.5, MUTED, SANS))
    b.append(
        f'<line x1="288" y1="{rows[2]}" x2="316" y2="{rows[2]}" stroke="{ACCENT}" stroke-width="1.2" marker-end="url(#arr-accent)"/>'
    )
    b.append(text(324, rows[2] + 3, "prefixo entregue a cada pergunta", 7.5, MUTED, SANS))
    return page(
        "corpus-fluxo",
        "Data flow · Arquitetura CAG",
        "Do dado ao prefixo",
        "Do dado ao prefixo",
        "Fluxo do corpus: fontes externas e curadoria viram YAML versionado em data/, a API carrega o Corpus na partida, monta o prefixo e o reconhecedor, e cada pergunta leva o prefixo e os anexos ao modelo.",
        W,
        H,
        "\n".join(b),
        "Atualizar o conteúdo é editar <code>data/</code> (à mão ou pelos scripts) e reiniciar a API: o Corpus é carregado uma vez na partida "
        "(<code>load_corpus</code>) e dele saem o prefixo cacheado e o reconhecedor. Uma mudança no corpus muda os bytes do prefixo, então a "
        "primeira pergunta depois do deploy grava um cache novo.",
    )


# ---------------------------------------------------------------- 4. Deployment
def production_deployment():
    b = []

    def zone(x, y, w, h, lab):
        lw = int(len(lab) * 8 * (0.62 + 0.18) + 12 + 3) // 4 * 4
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{ink(0.02)}" stroke="{ink(0.20)}" stroke-width="1" stroke-dasharray="4,4"/>'
            + f'<rect x="{x + 12}" y="{y - 6}" width="{lw}" height="12" fill="{PAPER}"/>'
            + text(x + 18, y + 3, lab, 8, MUTED, MONO, spacing="0.18em")
        )

    b.append(zone(24, 72, 240, 480, "INTERNET PÚBLICA"))
    b.append(zone(296, 72, 680, 168, "GITHUB"))
    b.append(zone(296, 272, 680, 280, "TAILNET · VM NA OCI"))
    # Caminhos (antes dos nós)
    b.append(
        f'<line x1="240" y1="136" x2="336" y2="136" stroke="{LINK}" stroke-width="1.2" marker-end="url(#arrow-link)"/>'
    )
    b.append(
        f'<line x1="736" y1="152" x2="536" y2="152" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>'
    )
    b.append(
        f'<path d="M 176 168 V 344 Q 176 352 184 352 H 336" fill="none" stroke="{LINK}" stroke-width="1.2" marker-end="url(#arrow-link)"/>'
    )
    b.append(
        f'<path d="M 112 168 V 408 Q 112 416 120 416 H 292" fill="none" stroke="{ink(0.55)}" stroke-width="1.2" stroke-dasharray="5,4"/>'
    )
    b.append(f'<line x1="296" y1="404" x2="296" y2="428" stroke="{INK}" stroke-width="2.4"/>')
    b.append(
        f'<line x1="536" y1="352" x2="656" y2="352" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>'
    )
    b.append(
        f'<path d="M 796 432 V 496 Q 796 504 788 504 H 240" fill="none" stroke="{LINK}" stroke-width="1.2" marker-end="url(#arrow-link)"/>'
    )
    b.append(
        f'<line x1="856" y1="200" x2="856" y2="304" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#arrow-accent)"/>'
    )
    # Rótulos
    b.append(label(288, 136, "GET PÁGINA", LINK))
    b.append(label(636, 152, "DEPLOY PAGES"))
    b.append(label(260, 352, "POST PERGUNTAR", LINK))
    b.append(label(204, 416, "PORTA DIRETA", INK))
    b.append(label(596, 352, "127.0.0.1:8010"))
    b.append(label(440, 504, "HTTPS:443", LINK))
    b.append(side_label(864, 252, "SSH:22 TAG:CI", ACCENT))

    def chip(x, y, w, name, version):
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="24" rx="4" fill="{ink(0.05)}" stroke="{MUTED}" stroke-width="1"/>'
            + text(x + 8, y + 16, name, 12, INK, SANS)
            + text(x + w - 8, y + 16, version, 9, MUTED, MONO, "end")
        )

    b.append(node(48, 104, 192, 64, "USER", "Navegador", "visitante", "input"))
    b.append(node(48, 472, 192, 64, "EXT", "OpenAI", "Decisions + Responses", "external"))
    b.append(node(336, 104, 200, 96, "CDN", "GitHub Pages", None, "backend", name_y=144))
    b.append(chip(352, 160, 168, "index.html", "pages.yml"))
    b.append(node(736, 104, 200, 96, "CI", "GitHub Actions", None, "backend", name_y=144))
    b.append(chip(752, 160, 168, "deploy.yml", "ubuntu-24.04"))
    b.append(node(336, 312, 200, 80, "EDGE", "Tailscale Funnel", "entrada pública da API", "focal"))
    b.append(node(656, 304, 280, 128, "VM", "judoka-api", "E2.1.Micro · Ubuntu 24.04", "backend", name_y=334))
    b.append(chip(672, 360, 248, "judo_chat (uvicorn)", "commit do main"))
    b.append(chip(672, 392, 248, "judoka-deploy", "só aceita main"))
    # Legenda
    ly = 584
    b.append(f'<line x1="24" y1="{ly}" x2="976" y2="{ly}" stroke="{ink(0.10)}" stroke-width="0.8"/>')
    b.append(text(24, ly + 16, "LEGENDA", 8, MUTED, MONO, spacing="0.18em"))
    iy = ly + 36
    b.append(
        f'<rect x="24" y="{iy - 8}" width="18" height="12" rx="2" fill="{ink(0.02)}" stroke="{ink(0.20)}" stroke-dasharray="4,4"/>'
    )
    b.append(text(48, iy + 2, "Zona de rede", 8.5, MUTED))
    b.append(
        f'<line x1="152" y1="{iy - 2}" x2="180" y2="{iy - 2}" stroke="{LINK}" stroke-width="1.2" marker-end="url(#arrow-link)"/>'
    )
    b.append(text(188, iy + 2, "Atravessa zonas", 8.5, MUTED))
    b.append(
        f'<line x1="300" y1="{iy - 2}" x2="328" y2="{iy - 2}" stroke="{MUTED}" stroke-width="1.2" marker-end="url(#arrow)"/>'
    )
    b.append(text(336, iy + 2, "Dentro da zona", 8.5, MUTED))
    b.append(
        f'<line x1="448" y1="{iy - 2}" x2="476" y2="{iy - 2}" stroke="{ACCENT}" stroke-width="1.4" marker-end="url(#arrow-accent)"/>'
    )
    b.append(text(484, iy + 2, "Deploy aprovado", 8.5, MUTED))
    b.append(
        f'<line x1="600" y1="{iy - 2}" x2="624" y2="{iy - 2}" stroke="{ink(0.55)}" stroke-width="1.2" stroke-dasharray="5,4"/>'
    )
    b.append(f'<line x1="628" y1="{iy - 8}" x2="628" y2="{iy + 4}" stroke="{INK}" stroke-width="2.4"/>')
    b.append(text(640, iy + 2, "Entrada bloqueada", 8.5, MUTED))
    b.append(f'<rect x="768" y="{iy - 8}" width="18" height="12" rx="2" fill="{ACCENT_TINT}" stroke="{ACCENT}"/>')
    b.append(text(792, iy + 2, "Nó em foco", 8.5, MUTED))
    return page(
        "producao-implantacao",
        "Deployment · Arquitetura CAG",
        "Onde roda",
        "Onde o judoka-assistant roda",
        "Implantação em três zonas: o navegador na internet pública busca a página no GitHub Pages e pergunta pela entrada pública da API, o Tailscale Funnel, que entrega à API na VM; o GitHub Actions faz deploy pela tailnet via SSH, e não há porta aberta direto na VM.",
        1000,
        640,
        "\n".join(b),
        "A VM não abre porta na OCI: o tráfego público entra pelo Funnel, que dá HTTPS e entrega a "
        "<code>127.0.0.1:8010</code>; ali o bloqueio por país e o rate limit agem antes de qualquer chamada a provedor. O GitHub Actions entra na "
        "tailnet como nó efêmero com <code>tag:ci</code> e a chave dele só roda <code>judoka-deploy &lt;commit&gt;</code>, que recusa commit fora do "
        "<code>main</code>. A API chama a OpenAI pela Decisions API (guardrail) e pela Responses API (resposta); com "
        '<code>JUDO_CHAT_PROVIDER=anthropic</code>, as duas chamadas vão à Messages API. Detalhes no README, seção "Deploy automático".',
    )


OUT.mkdir(parents=True, exist_ok=True)
for name, fn in [
    ("prompt-cag.html", prompt_layers),
    ("pergunta-sequencia.html", question_sequence),
    ("corpus-fluxo.html", corpus_flow),
    ("producao-implantacao.html", production_deployment),
]:
    (OUT / name).write_text(fn())
    print("ok", name)
