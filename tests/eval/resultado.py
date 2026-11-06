"""Resultado publicado da avaliação, a fonte dos números do README.

`test_eval.py` grava `resultado.json` e reescreve as linhas do README. `tests/docs` confere,
sem rede, se o que está nos documentos ainda bate com esse resultado e com `cases.yaml`.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from .cases import Case

ROOT = Path(__file__).resolve().parents[2]
RESULTADO = Path(__file__).with_name("resultado.json")
README = ROOT / "README.md"
ARQUITETURA = ROOT / "docs" / "arquitetura" / "README.md"
COMANDO = "uv run --env-file .env pytest -m eval"


def impressao_digital(cases: Sequence[Case]) -> str:
    """Hash do conteúdo dos casos: comentários e formatação do YAML não contam."""
    texto = json.dumps([c.model_dump() for c in cases], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _percentual(valor: float) -> str:
    return f"{valor * 100:.1f}".removesuffix(".0").replace(".", ",") + "%"


def linhas_readme(resultado: Mapping[str, object]) -> dict[str, str]:
    """Início de cada linha da tabela "Números" -> linha inteira."""
    data = resultado["data"]
    metricas = resultado["metricas"]
    assert isinstance(metricas, dict)
    latencia = f"{metricas['guardrail_latencia_mediana_s']:.1f}".replace(".", ",")
    return {
        "| Avaliação com ": (
            f"| Avaliação com {metricas['casos']} perguntas ({data}) | "
            f"{metricas['falso_aceite_adversarial']} falso-aceite adversarial, "
            f"{_percentual(metricas['recusa_correta'])} de recusa correta, "
            f"{_percentual(metricas['falsa_recusa'])} de falsa recusa |"
        ),
        "| Latência do guardrail |": (
            f"| Latência do guardrail | ~{latencia} s de mediana pela Decisions API ({data}), contra ~4 s antes |"
        ),
    }


def atualizar_readme(texto: str, resultado: Mapping[str, object]) -> str:
    linhas = texto.split("\n")
    for inicio, linha in linhas_readme(resultado).items():
        posicoes = [i for i, atual in enumerate(linhas) if atual.startswith(inicio)]
        if len(posicoes) != 1:
            raise ValueError(f"o README deveria ter uma linha começando com {inicio!r}, tem {len(posicoes)}")
        linhas[posicoes[0]] = linha
    return "\n".join(linhas)


def problemas(
    resultado: Mapping[str, object] | None, cases: Sequence[Case], readme: str, arquitetura: str, tecnicas: int
) -> list[str]:
    """O que está desalinhado entre os documentos, os casos, o corpus e o último resultado."""
    achados = []
    if f"{tecnicas} técnicas" not in readme:
        achados.append(f'O README deveria citar "{tecnicas} técnicas", o total do corpus.')

    fora = [c for c in cases if c.categoria == "fora"]
    adversariais = sum(c.id.startswith("a") for c in fora)
    trechos = (
        f"tem {len(cases)} perguntas: {len(cases) - len(fora)} dentro do escopo",
        f"e {len(fora)} fora ({len(fora) - adversariais} temas gerais e {adversariais} adversariais",
    )
    corrido = " ".join(arquitetura.split())
    achados += [f'docs/arquitetura/README.md deveria dizer "{t}".' for t in trechos if t not in corrido]

    if resultado is None:
        return [*achados, f"Falta tests/eval/resultado.json: rode `{COMANDO}`."]
    if resultado["casos_sha256"] != impressao_digital(cases):
        achados.append(f"cases.yaml mudou depois da última avaliação: rode `{COMANDO}`.")
    achados += [
        f"O README deveria ter a linha: {linha}" for linha in linhas_readme(resultado).values() if linha not in readme
    ]
    return achados
