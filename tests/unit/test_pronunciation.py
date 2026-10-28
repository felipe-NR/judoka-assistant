import unicodedata
from pathlib import Path

import pytest
import yaml

from judo_chat.pronunciation import pronounce

PRONUNCIATION = Path(__file__).parents[2] / "data" / "fgj" / "pronuncia.yaml"


def _without_stress(text: str) -> str:
    """A tabela marca a tônica com acento agudo (TCHIKAMÁ), que a pronúncia gerada não tem."""
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", text).replace("́", ""))


# O "r" fraco não tem exemplo escrito, só a explicação.
_EXAMPLES = [row for row in yaml.safe_load(PRONUNCIATION.read_text()) if row["letra"] != "R"]


@pytest.mark.parametrize("row", _EXAMPLES, ids=[row["letra"] for row in _EXAMPLES])
def test_rule_matches_the_fgj_example(row: dict[str, str]) -> None:
    assert pronounce(row["exemplo"]) == _without_stress(row["pronuncia"])


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Seoi-nage", "SSEOI NAGUE"),
        ("Tsurikomi-goshi", "TSURIKOMI GOSHI"),
        ("Kami-shiho-gatame", "KAMI SHIRO GATAME"),
        ("Ude-hishigi-juji-gatame", "UDE RISHIGUI DJUDJI GATAME"),
        ("Uki-Waza", "UKI UAZA"),
    ],
)
def test_technique_names(name: str, expected: str) -> None:
    assert pronounce(name) == expected
