from types import SimpleNamespace

import pytest

from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper
from Doc2Quiz.service.modif_service import corriger_question, modifier_question
from shared.qcm import enregistrer_modification


def test_modifier_question_retourne_une_copie_et_marque_la_modification():
    questions = [
        {
            "type": "qcm",
            "question": "Ancien énoncé",
            "options": ["A", "B", "C", "D"],
            "bonne_reponse": "A",
        }
    ]

    modified = modifier_question(
        questions,
        0,
        question="Nouvel énoncé",
        options=["A", "B", "C", "D"],
        bonne_reponse="B",
    )

    assert questions[0]["question"] == "Ancien énoncé"
    assert modified[0]["question"] == "Nouvel énoncé"
    assert modified[0]["bonne_reponse"] == "B"
    assert modified[0]["modifie_manuellement"] is True
    assert modified[0]["date_modification"]


def test_modifier_question_refuse_une_reponse_absente_des_options():
    questions = [{"options": ["A", "B"]}]

    try:
        modifier_question(
            questions,
            0,
            question="Question",
            options=["A", "B"],
            bonne_reponse="C",
        )
    except ValueError as error:
        assert "option" in str(error)
    else:
        raise AssertionError("Une réponse absente des options doit être refusée.")


def test_corriger_question_utilise_l_erreur_signalee():
    class FauxClient:
        def generate_text(self, prompt):
            assert "la réponse correcte est B" in prompt
            return SimpleNamespace(
                response='{"question": "Question corrigée", "options": ["A", "B"], "bonne_reponse": "B"}'
            )

    correction = corriger_question(
        {"question": "Ancienne question", "options": ["A", "C"], "bonne_reponse": "A"},
        "la réponse correcte est B",
        FauxClient(),
    )

    assert correction["question"] == "Question corrigée"
    assert correction["bonne_reponse"] == "B"

# Déclaré dans pystest.ini
# test nécessitant un serveur Ollama réel
@pytest.mark.integration
def test_enregistrer_modification_avec_ollama():
    client = OllamaWrapper(
        default_model="gemma4:26b",
        timeout_s=120.0,
        max_retries=2,
    )
    if not client.is_server_running():
        pytest.skip(
            "Serveur Ollama inaccessible — vérifier OLLAMA_BASE_URL dans le .env"
        )
    if client.default_model not in client.list_models():
        pytest.skip(
            f"Modèle Ollama absent : {client.default_model} — "
            "installer le modèle ou corriger OLLAMA_DEFAULT_LLM dans le .env"
        )

    result = enregistrer_modification(
        questions=[
            {
                "question": "Combien font 2 + 2 ?",
                "options": ["3", "4", "5"],
                "bonne_reponse": "3",
            }
        ],
        question_index="0",
        erreur="La bonne réponse devrait être 4.",
        llm_client=client,
    )

    updated_questions, question, options, bonne_reponse, message = result

    assert message == "**Correction IA enregistrée.**"
    assert question
    assert options
    assert bonne_reponse in options.splitlines()
    assert updated_questions[0]["question"] == question
    assert updated_questions[0]["bonne_reponse"] == bonne_reponse