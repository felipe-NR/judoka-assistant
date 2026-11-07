import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from judo_chat.corpus.loader import CorpusError, load_corpus
from judo_chat.corpus.models import Corpus
from judo_chat.corpus.render import render_corpus

from ..conftest import DATA_DIR


def test_corpus_counts(corpus: Corpus) -> None:
    techniques = [t for t in corpus.techniques if t.kind == "technique"]
    assert len(techniques) >= 100
    assert all(t.name_pt_br and t.description_pt_br for t in corpus.techniques)
    assert {d.theme for d in corpus.documents} == {"regras", "historia", "graduacao", "termos"}
    assert len([d for d in corpus.documents if d.id.startswith("graduacao/") and "faixa-" in d.id]) == 7


def test_kodokan_katame_waza_is_complete(corpus: Corpus) -> None:
    groups = [t.group for t in corpus.techniques if t.status != "nonstandard"]
    assert groups.count("katame-waza/osaekomi-waza") == 10
    assert groups.count("katame-waza/shime-waza") == 12
    assert groups.count("katame-waza/kansetsu-waza") == 10


def test_unrelated_video_is_removed(corpus: Corpus) -> None:
    assert all("dQw4w9WgXcQ" not in v.url for t in corpus.techniques for v in t.videos)


def test_kodokan_videos_cover_the_official_list(corpus: Corpus) -> None:
    with_kodokan = [t for t in corpus.techniques if any(v.source == "kodokan" for v in t.videos)]
    # 100 técnicas oficiais na lista da FECJU. O Sasae-tsurikomi-ashi não tem vídeo lá e entrou à
    # parte, do canal do Kodokan (2026-11-06); o link do Osoto-guruma aponta para o vídeo do O-guruma.
    assert len(with_kodokan) == 99
    assert corpus.technique("sasae-tsurikomi-ashi").videos[0].source == "kodokan"
    assert corpus.technique("osoto-guruma").videos[0].source == "outro"
    assert corpus.technique("o-guruma").videos[0].source == "kodokan"


def _render_in_subprocess(seed: str) -> bytes:
    code = (
        "import sys; from pathlib import Path; from judo_chat.corpus.loader import load_corpus;"
        "from judo_chat.corpus.render import render_corpus;"
        f"sys.stdout.buffer.write(render_corpus(load_corpus(Path({str(DATA_DIR)!r}))).encode())"
    )
    env = {**os.environ, "PYTHONHASHSEED": seed}
    return subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, check=True).stdout


def test_render_is_byte_identical_across_hash_seeds() -> None:
    assert _render_in_subprocess("1") == _render_in_subprocess("2")


def test_render_lists_popular_names_sorted(corpus: Corpus) -> None:
    text = render_corpus(corpus)
    assert '"Ashi-barai" (ambíguo) -> Deashi-harai | Okuriashi-harai' in text


def _copy_data(tmp_path: Path) -> Path:
    for path in DATA_DIR.rglob("*"):
        if path.is_file():
            target = tmp_path / path.relative_to(DATA_DIR)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    return tmp_path


def test_loader_rejects_unknown_technique_id(tmp_path: Path) -> None:
    data = _copy_data(tmp_path)
    popular = data / "glossario" / "nomes_populares.yaml"
    popular.write_text(
        popular.read_text("utf-8") + "\n- name: Inexistente\n  technique_ids: [nao-existe]\n"
        "  confidence: baixa\n  source: teste\n",
        "utf-8",
    )
    with pytest.raises(CorpusError, match="nao-existe"):
        load_corpus(data)


def test_loader_rejects_rule_term_missing_from_its_document(tmp_path: Path) -> None:
    data = _copy_data(tmp_path)
    terms = data / "glossario" / "termos_regras.yaml"
    terms.write_text(terms.read_text("utf-8") + "- termo: Koka\n  documento: regras/pontuacao\n", "utf-8")
    with pytest.raises(CorpusError, match="Koka"):
        load_corpus(data)


def test_loader_rejects_phases_of_unknown_technique(tmp_path: Path) -> None:
    data = _copy_data(tmp_path)
    phases = data / "fases" / "tagusari_2016.yaml"
    phases.write_text(
        phases.read_text("utf-8") + "- id: nao-existe\n  kuzushi: a\n  tsukuri: b\n  kake: c\n",
        "utf-8",
    )
    with pytest.raises(CorpusError, match="nao-existe"):
        load_corpus(data)


def test_rule_terms_are_loaded(corpus: Corpus) -> None:
    assert "Sono-mama" in {term.termo for term in corpus.rule_terms}


def test_fgj_covers_the_100_official_techniques(corpus: Corpus) -> None:
    with_fgj = [t for t in corpus.techniques if t.fgj is not None]
    assert len(with_fgj) == 100
    assert all(t.status != "nonstandard" for t in with_fgj)
    assert sum(1 for t in with_fgj if t.fgj and t.fgj.kyo_grupo.gokyo) == 40
    seoi = corpus.technique("seoi-nage").fgj
    assert seoi is not None and seoi.kanji == "背負投"
    assert seoi.traducao == "PROJEÇÃO COM CARREGAMENTO NAS COSTAS"


def test_render_uses_fgj_description_verbatim(corpus: Corpus) -> None:
    from judo_chat.corpus.render import render_technique

    text = render_technique(corpus.technique("osoto-gari"))
    fgj = corpus.technique("osoto-gari").fgj
    assert fgj is not None
    assert f"Descrição Kodokan (FGJ): {fgj.descricao_kodokan}" in text
    assert "\nDescrição: " not in text


def test_phases_cover_the_six_te_waza_of_the_gokyo(corpus: Corpus) -> None:
    with_phases = {t.id for t in corpus.techniques if t.phases is not None}
    assert with_phases == {"seoi-nage", "tai-otoshi", "kata-guruma", "sukui-nage", "uki-otoshi", "sumi-otoshi"}


def test_render_carries_the_phases_with_their_source(corpus: Corpus) -> None:
    from judo_chat.corpus.render import render_technique

    phases = corpus.technique("tai-otoshi").phases
    assert phases is not None
    text = render_technique(corpus.technique("tai-otoshi"))
    assert f"Kuzushi (Tagusari 2016): {phases.kuzushi}" in text
    assert f"Kake (Tagusari 2016): {phases.kake}" in text
    assert "Tagusari" not in render_technique(corpus.technique("uchi-mata"))


def test_block_leaves_out_recognizer_only_fields(corpus: Corpus) -> None:
    text = render_corpus(corpus)
    assert "youtu" not in text
    assert "Outras grafias" not in text and "Inglês:" not in text
    assert "背負投" not in text
    # Conceitos com verbete da FGJ aparecem só no glossário de termos.
    assert "### Kuzushi" not in text and "- KUZUSHI:" in text


def _append(text: str) -> Callable[[str], str]:
    return lambda original: original + text


@pytest.mark.parametrize(
    ("relative", "change", "message"),
    [
        ("glossario/tecnicas.yaml", lambda _: "tecnicas: []\n", "esperava uma lista de objetos"),
        ("glossario/tecnicas.yaml", lambda original: original + original, "ids de técnica repetidos"),
        ("glossario/nomes_populares.yaml", lambda original: original + original, "nomes populares repetidos"),
        ("regras/pontuacao.md", lambda original: original.removeprefix("---\n"), "falta o cabeçalho YAML"),
        ("regras/pontuacao.md", lambda _: "---\n- titulo\n---\ncorpo\n", "cabeçalho YAML inválido"),
        ("fgj/tecnicas.yaml", _append("- id: nao-existe\n"), "técnica inexistente 'nao-existe'"),
        ("glossario/termos_regras.yaml", _append("- termo: Ippon\n  documento: regras/nao-existe\n"), "inexistente"),
        ("glossario/termos_regras.yaml", _append("- termo: Ippon\n  documento: regras/pontuacao\n"), "repetidos"),
        ("glossario/variantes_digitacao.yaml", lambda _: "- osoto\n", "esperava um mapa"),
    ],
)
def test_loader_rejects_invalid_data(tmp_path: Path, relative: str, change: Callable[[str], str], message: str) -> None:
    path = _copy_data(tmp_path) / relative
    path.write_text(change(path.read_text("utf-8")), "utf-8")
    with pytest.raises(CorpusError, match=message):
        load_corpus(tmp_path)


def test_loader_accepts_missing_optional_files(tmp_path: Path) -> None:
    data = _copy_data(tmp_path)
    for relative in ("fgj", "fases"):
        for path in (data / relative).iterdir():
            path.unlink()
    for relative in ("glossario/termos_regras.yaml", "glossario/variantes_digitacao.yaml"):
        (data / relative).unlink()
    corpus = load_corpus(data)
    assert corpus.techniques and not corpus.rule_terms
    assert not any(document.id.startswith("termos/") for document in corpus.documents)
