"""Pronúncia dos nomes japoneses para quem lê em português, pelas regras da FGJ
(`data/fgj/pronuncia.yaml`).

A tabela da FGJ é texto livre, então as regras estão escritas aqui e o teste confere cada uma
contra o exemplo da própria tabela. A tabela não diz qual sílaba é tônica (TCHIKAMÁ,
UÁZA), e a pronúncia gerada não marca a tônica. O "r" fraco não muda a escrita.
"""

import re

_VOWELS = "AEIOU"
# Na ordem em que se aplicam: o CH vira TCH antes de o H virar R, e o Ê vem antes do GU,
# cujo U não é vogal do nome.
_RULES = (
    (re.compile(r"CH"), "TCH"),
    # "rrá": o H aspirado, menos no SH, que a tabela não cobre e fica como está.
    (re.compile(r"(?<![CS])H"), "R"),
    (re.compile(r"J"), "DJ"),
    (re.compile(r"W"), "U"),
    # "ê": depois de vogal, para o "ae" não ser lido como o ditongo "ai" (SASAE).
    (re.compile(rf"(?<=[{_VOWELS}])E"), "Ê"),
    # "gue, gui": sem o U, o português leria "je, ji".
    (re.compile(r"G(?=[EI])"), "GU"),
    # "dois s, nunca z". No TS e no SH o S não soa como z.
    (re.compile(r"(?<!T)S(?!H)"), "SS"),
)


def pronounce(name: str) -> str:
    """ "Seoi-nage" -> "SSEOI NAGUE"."""
    text = name.upper().replace("-", " ")
    for pattern, replacement in _RULES:
        text = pattern.sub(replacement, text)
    return text
