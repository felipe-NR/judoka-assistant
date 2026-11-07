import logging

from fastapi import APIRouter, Depends

from judo_chat.answer import (
    REFUSAL_MESSAGE,
    UNAVAILABLE_MESSAGE,
    Turn,
    detect_intents,
    fgj_quotes_intact,
    video_groups,
)
from judo_chat.dependencies import (
    AnswererDep,
    CorpusDep,
    GuardrailDep,
    RecognizerDep,
    enforce_question_rate_limit,
)
from judo_chat.normalizer import terms_outside_techniques
from judo_chat.schemas import (
    AskRequest,
    AskResponse,
    DetectedTechnique,
    LegacyVideo,
    VideoGroupOut,
    VideoLink,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["perguntas"])


@router.post("/perguntar", response_model=AskResponse, dependencies=[Depends(enforce_question_rate_limit)])
async def ask(
    body: AskRequest,
    recognizer: RecognizerDep,
    guardrail: GuardrailDep,
    answerer: AnswererDep,
    corpus: CorpusDep,
) -> AskResponse:
    history = [Turn(role=t.role, text=t.text) for t in body.history]
    matches = recognizer.find(body.query)
    detected = [
        DetectedTechnique(
            term=m.term, technique_ids=list(m.technique_ids), match_type=m.match_type, ambiguous=m.ambiguous
        )
        for m in matches
    ]
    found_terms = recognizer.find_terms(body.query)
    last_matches: list = []
    if not matches and not found_terms and history:
        # "E o outro?": o guardrail vê as técnicas da última pergunta para julgar a continuação.
        last_question = next((t.text for t in reversed(history) if t.role == "usuario"), "")
        last_matches = recognizer.find(last_question)

    technique_names = [corpus.technique(tid).name for m in (matches or last_matches) for tid in m.technique_ids]
    terms = [corpus.rule_term_label(t) for t in terms_outside_techniques(found_terms, technique_names)]
    # O guardrail recebe os mesmos turnos completos que o modelo de resposta: nenhum trecho do
    # histórico chega à resposta sem passar antes pela classificação.
    guardrail_history = [f"{'Usuário' if t.role == 'usuario' else 'Assistente'}: {t.text}" for t in history]
    verdict = await guardrail.classify(body.query, guardrail_history, technique_names, terms)
    if not verdict.allowed:
        # Falha do guardrail também bloqueia a resposta, mas sem dizer que a pergunta saiu do escopo.
        message = UNAVAILABLE_MESSAGE if verdict.failed else REFUSAL_MESSAGE
        return AskResponse(answer=message, category="fora", refused=True, techniques_detected=detected)

    if not matches and verdict.continuation:
        matches = last_matches
    answer = await answerer.answer(body.query, matches, history, terms)
    # A lista curta de combinações não traz fichas nem os vídeos de cada golpe (2026-11-06).
    short_list = detect_intents(body.query) == ["combinacao"]
    groups = [] if answer.refused else video_groups(answer.text, matches, recognizer, corpus, only_question=short_list)
    if not short_list:
        for technique_id, intact in fgj_quotes_intact(answer.text, groups, corpus).items():
            logger.info("descrição FGJ %s: %s", "literal" if intact else "PARAFRASEADA", technique_id)
    return AskResponse(
        answer=answer.text,
        category="fora" if answer.refused else verdict.category,
        refused=answer.refused,
        techniques_detected=detected,
        video_groups=[
            VideoGroupOut(
                technique=g.technique,
                anchor=g.anchor,
                videos=[VideoLink(url=v.url, kodokan=v.kodokan) for v in g.videos],
                kanji=g.kanji,
                pronunciation=g.pronunciation,
                kodokan_missing=g.kodokan_missing,
            )
            for g in groups
        ],
        videos=[LegacyVideo(technique=g.technique, url=v.url, kodokan=v.kodokan) for g in groups for v in g.videos],
    )
