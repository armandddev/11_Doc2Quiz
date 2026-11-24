import asyncio
from types import SimpleNamespace

from Doc2Quiz.service.context_summary_service import (
    build_summary_prompt,
    refresh_context_summary,
)
from Doc2Quiz.service.core import generate_qcm_question


class FakeLLM:
    def __init__(self, response):
        self.response = response
        self.prompts = []

    def generate_text(self, prompt, **kwargs):
        self.prompts.append(prompt)
        return SimpleNamespace(response=self.response)


def test_generation_sans_retour_n_injecte_aucun_bloc(monkeypatch):
    llm = FakeLLM(
        '{"question":"q","options":["A. a","B. b","C. c","D. d"],'
        '"feedbacks":["a","b","c","d"],"correct":"A"}'
    )

    generate_qcm_question(
        "Le texte source",
        "BUT",
        "Les deux",
        llm,
        context_summary=None,
    )

    assert "[HISTORIQUE DES RETOURS DE L'ENSEIGNANT]" not in llm.prompts[0]


def test_prompt_resume_contient_50_retours_et_reste_limite(monkeypatch):
    feedbacks = [{"contenu": f"Retour varié numéro {index}"} for index in range(51)]
    prompt = build_summary_prompt(feedbacks)

    assert "Retour varié numéro 0" in prompt
    assert "Retour varié numéro 50" in prompt
    assert "5 à 10 lignes maximum" in prompt


def test_refresh_resume_stocke_50_retours(monkeypatch):
    feedbacks = [{"contenu": f"Retour numéro {index}"} for index in range(51)]
    llm = FakeLLM(
        "Les distracteurs sont trop évidents.\n"
        "Les réponses doivent être plus liées au support."
    )
    stored = {}

    async def fake_get_feedbacks(user_id):
        assert user_id == "teacher-1"
        return feedbacks

    async def fake_save(user_id, summary, feedback_count):
        stored.update(
            user_id=user_id,
            summary=summary,
            feedback_count=feedback_count,
        )

    monkeypatch.setattr(
        "Doc2Quiz.service.context_summary_service.get_feedbacks_for_user",
        fake_get_feedbacks,
    )
    monkeypatch.setattr(
        "Doc2Quiz.service.context_summary_service.save_context_summary",
        fake_save,
    )

    summary = asyncio.run(
        refresh_context_summary("teacher-1", llm_client=llm)
    )

    assert stored["feedback_count"] == 51
    assert "Retour numéro 50" in llm.prompts[0]
    assert summary == stored["summary"]
    assert len(summary.splitlines()) <= 10


def test_nouveau_retour_apparait_dans_le_prompt_injecte(monkeypatch):
    llm = FakeLLM(
        '{"question":"q","options":["A. a","B. b","C. c","D. d"],'
        '"feedbacks":["a","b","c","d"],"correct":"A"}'
    )
    summary = (
        "Les nouvelles attentes exigent des distracteurs non évidents."
    )

    generate_qcm_question(
        "Le texte source",
        "BUT",
        "Les deux",
        llm,
        context_summary=summary,
    )

    prompt = llm.prompts[0]
    assert prompt.index("[HISTORIQUE DES RETOURS DE L'ENSEIGNANT]") < prompt.index(
        "Tu es un enseignant expert"
    )
    assert "distracteurs non évidents" in prompt
