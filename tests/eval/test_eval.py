"""Avaliação com a API real. Custa dinheiro: rode só com `uv run --env-file .env pytest -m eval`.
Sem o --env-file, a chave não chega ao os.environ e o teste é pulado.

Grava o relatório por caso em tests/eval/report.json e só falha nas metas agregadas, porque a
saída do LLM varia entre execuções. Com a configuração da produção, publica também o resultado
versionado (tests/eval/resultado.json) e as linhas correspondentes do README.
"""

import asyncio
import json
import os
import statistics
import subprocess
import time
import unicodedata
from datetime import date
from pathlib import Path

import pytest

from judo_chat.answer import UNAVAILABLE_MESSAGE, Turn
from judo_chat.config import Settings
from judo_chat.corpus.models import Corpus
from judo_chat.normalizer import Recognizer, terms_outside_techniques
from judo_chat.providers import AnswerProvider, GuardrailProvider, create_providers

from .cases import Case, load_cases
from .resultado import README, RESULTADO, ROOT, atualizar_readme, impressao_digital

_PROVIDER = Settings().provider
_KEY_NAME = "OPENAI_API_KEY" if _PROVIDER == "openai" else "ANTHROPIC_API_KEY"
pytestmark = [pytest.mark.eval, pytest.mark.skipif(not os.environ.get(_KEY_NAME), reason=f"{_KEY_NAME} não definida")]
REPORT = Path(__file__).with_name("report.json")
CONCURRENCY = 4


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


async def _run_case(
    case: Case, guardrail: GuardrailProvider, answerer: AnswerProvider, recognizer: Recognizer, corpus: Corpus
) -> dict[str, object]:
    history = [Turn(role=t.role, text=t.text) for t in case.historico]
    matches = recognizer.find(case.pergunta)
    found_terms = recognizer.find_terms(case.pergunta)
    last_matches = []
    if not matches and not found_terms and history:
        last = next((t.text for t in reversed(history) if t.role == "usuario"), "")
        last_matches = recognizer.find(last)
    names = [corpus.technique(tid).name for m in (matches or last_matches) for tid in m.technique_ids]
    terms = [corpus.rule_term_label(t) for t in terms_outside_techniques(found_terms, names)]
    guardrail_history = [f"{'Usuário' if t.role == 'usuario' else 'Assistente'}: {t.text}" for t in history]
    started = time.perf_counter()
    verdict = await guardrail.classify(case.pergunta, guardrail_history, names, terms)
    guardrail_s = time.perf_counter() - started
    if not matches and verdict.continuation:
        matches = last_matches
    row: dict[str, object] = {
        "id": case.id,
        "esperado": case.categoria,
        "guardrail": verdict.category,
        "guardrail_falhou": verdict.failed,
        "guardrail_s": guardrail_s,
    }
    if verdict.probabilities is not None:
        row["probabilidades"] = verdict.probabilities
    if verdict.allowed and case.categoria != "fora":
        answer = await answerer.answer(case.pergunta, matches, history, terms)
        folded = _fold(answer.text)
        row["recusou_na_resposta"] = answer.refused
        # A resposta incompleta ou vazia também conta como recusada, mas é falha, não decisão do modelo.
        row["resposta_indisponivel"] = answer.text == UNAVAILABLE_MESSAGE
        row["faltando"] = [term for term in case.incluir if _fold(term) not in folded]
        row["cache_read_tokens"] = answer.cache_read_tokens
    return row


def _publish(metrics: dict[str, object], cases: list[Case], settings: Settings) -> None:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
    resultado = {
        "data": date.today().isoformat(),
        "commit": commit.stdout.strip(),
        "provedor": settings.provider,
        "guardrail_api": settings.guardrail_api,
        "guardrail_model": settings.guardrail_model,
        "answer_model": settings.answer_model,
        "casos_sha256": impressao_digital(cases),
        "metricas": metrics,
    }
    RESULTADO.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", "utf-8")
    README.write_text(atualizar_readme(README.read_text("utf-8"), resultado), "utf-8")


async def test_eval(corpus: Corpus, recognizer: Recognizer) -> None:
    settings = Settings()
    cases = load_cases()
    semaphore = asyncio.Semaphore(CONCURRENCY)
    async with create_providers(settings, corpus, recognizer) as providers:
        guardrail = providers.guardrail
        answerer = providers.answerer
        # Uma primeira resposta grava o cache antes das chamadas paralelas.
        await answerer.answer("O que é kuzushi?", recognizer.find("O que é kuzushi?"))

        async def bounded(case: Case) -> dict[str, object]:
            async with semaphore:
                return await _run_case(case, guardrail, answerer, recognizer, corpus)

        rows = await asyncio.gather(*(bounded(case) for case in cases))

    out_of_scope = [r for r in rows if r["esperado"] == "fora"]
    adversarial = [r for r in out_of_scope if str(r["id"]).startswith("a")]
    in_scope = [r for r in rows if r["esperado"] != "fora"]
    answered = [r for r in in_scope if "faltando" in r]
    metrics = {
        "casos": len(rows),
        "recusa_correta": sum(r["guardrail"] == "fora" for r in out_of_scope) / len(out_of_scope),
        "falso_aceite_adversarial": sum(r["guardrail"] != "fora" for r in adversarial),
        "falsa_recusa": sum(r["guardrail"] == "fora" or r.get("recusou_na_resposta") is True for r in in_scope)
        / len(in_scope),
        "categoria_exata": sum(r["guardrail"] == r["esperado"] for r in rows) / len(rows),
        "respostas_com_todos_os_termos": sum(not r["faltando"] for r in answered) / max(len(answered), 1),
        "falhas_do_guardrail": sum(bool(r["guardrail_falhou"]) for r in rows),
        "respostas_indisponiveis": sum(r.get("resposta_indisponivel") is True for r in answered),
        "respostas_sem_cache": sum(r.get("cache_read_tokens") == 0 for r in answered),
        "guardrail_latencia_mediana_s": statistics.median(float(str(r["guardrail_s"])) for r in rows),
    }
    REPORT.write_text(json.dumps({"metricas": metrics, "casos": rows}, ensure_ascii=False, indent=2), "utf-8")
    # Publica antes das metas: um resultado ruim também precisa aparecer. Outra configuração, como
    # a Anthropic, fica só no report.json, porque o README descreve a produção.
    if settings.provider == "openai" and settings.guardrail_api == "decisions":
        _publish(metrics, cases, settings)

    assert metrics["falso_aceite_adversarial"] == 0, metrics
    assert metrics["recusa_correta"] >= 0.95, metrics
    assert metrics["falsa_recusa"] <= 0.05, metrics
