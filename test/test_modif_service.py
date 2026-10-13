from types import SimpleNamespace

import pytest

from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper
from Doc2Quiz.service.modif_service import corriger_question, modifier_question
from shared.qcm import enregistrer_modification, enregistrer_modifications
from Doc2Quiz.pages.page_QCM import render_qcm_html


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
    assert modified[0]["correct"] == "B"
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


def test_modifier_question_accepte_une_lettre_comme_reponse():
    modified = modifier_question(
        [{"options": ["A. Faux", "B. Vrai"]}],
        0,
        question="Question",
        options=["A. Faux", "B. Vrai"],
        bonne_reponse="B",
    )

    assert modified[0]["bonne_reponse"] == "B. Vrai"
    assert modified[0]["correct"] == "B"


def test_corriger_question_ignore_le_texte_apres_le_json():
    class FauxClient:
        def generate_text(self, prompt):
            return SimpleNamespace(
                response=(
                    '{"question":"Corrigée","options":["A","B"],'
                    '"bonne_reponse":"B"}\nVoici une explication.'
                )
            )

    correction = corriger_question({"question": "Q"}, "Erreur", FauxClient())

    assert correction["question"] == "Corrigée"
    assert correction["bonne_reponse"] == "B"


def test_apercu_utilise_la_reponse_corrigee():
    html = render_qcm_html(
        [{
            "question": "Question",
            "options": ["A. Ancienne", "B. Corrigée"],
            "correct": "A",
            "bonne_reponse": "B. Corrigée",
        }]
    )

    assert "A. Ancienne" in html
    assert "B. Corrigée" in html
    assert html.index("background:#e8f4fd") > html.index("A. Ancienne")


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


def test_enregistrer_modifications_associe_les_lignes_aux_questions():
    class FauxClient:
        def __init__(self):
            self.prompts = []

        def generate_text(self, prompt):
            self.prompts.append(prompt)
            question_number = len(self.prompts)
            return SimpleNamespace(
                response=(
                    f'{{"question": "Question corrigée {question_number}", '
                    f'"options": ["A", "B"], "bonne_reponse": "B"}}'
                )
            )

    questions = [
        {"question": "Question 1", "options": ["A", "B"], "bonne_reponse": "A"},
        {"question": "Question 2", "options": ["A", "B"], "bonne_reponse": "A"},
    ]
    client = FauxClient()

    updated, question, options, answer, message = enregistrer_modifications(
        questions,
        "La réponse de la question 1 doit être B.\n"
        "La réponse de la question 2 doit être B.",
        client,
    )

    assert updated[0]["question"] == "Question corrigée 1"
    assert updated[1]["question"] == "Question corrigée 2"
    assert updated[0]["bonne_reponse"] == "B"
    assert updated[1]["bonne_reponse"] == "B"
    assert question == ""
    assert options == ""
    assert answer is None
    assert message == (
        "**2 correction(s) IA enregistrée(s).** "
        "Le QCM affiché a été actualisé."
    )


def test_enregistrer_modifications_utilise_le_numero_de_question():
    class FauxClient:
        def generate_text(self, prompt):
            question_number = "8" if "question 8" in prompt.lower() else "9"
            return SimpleNamespace(
                response=(
                    f'{{"question": "Question corrigée {question_number}", '
                    f'"options": ["A", "B"], "bonne_reponse": "B"}}'
                )
            )

    questions = [
        {"question": f"Question {index}", "options": ["A", "B"], "bonne_reponse": "A"}
        for index in range(1, 10)
    ]

    updated, *_ = enregistrer_modifications(
        questions,
        "La question 8 est la D\nLa question 9 est la A",
        FauxClient(),
    )

    assert updated[7]["question"] == "Question corrigée 8"
    assert updated[8]["question"] == "Question corrigée 9"
    assert updated[0]["question"] == "Question 1"


def test_enregistrer_modifications_traite_deux_questions_sur_une_ligne():
    class FauxClient:
        def generate_text(self, prompt):
            number = "8" if "question 8" in prompt.lower() else "9"
            return SimpleNamespace(
                response=(
                    f'{{"question": "Question corrigée {number}", '
                    f'"options": ["A", "B"], "bonne_reponse": "B"}}'
                )
            )

    questions = [
        {"question": f"Question {index}", "options": ["A", "B"], "bonne_reponse": "A"}
        for index in range(1, 10)
    ]
    updated, *_ = enregistrer_modifications(
        questions,
        "La question 8 est la réponse A et la question 9 est la réponse C",
        FauxClient(),
    )

    assert updated[7]["question"] == "Question corrigée 8"
    assert updated[8]["question"] == "Question corrigée 9"


def test_enregistrer_modifications_respecte_la_reponse_explicite():
    class FauxClient:
        def generate_text(self, prompt):
            return SimpleNamespace(
                response=(
                    '{"question": "Question corrigée", '
                    '"options": ["A. Faux", "B. Faux", "C. Faux", "D. Vrai"], '
                    '"bonne_reponse": "B"}'
                )
            )

    questions = [{
        "question": "Question 1",
        "options": ["A. Faux", "B. Faux", "C. Faux", "D. Ancienne"],
        "bonne_reponse": "A. Faux",
    }]
    updated, *_ = enregistrer_modifications(
        questions,
        "La question 1 doit avoir la réponse D",
        FauxClient(),
    )

    assert updated[0]["bonne_reponse"] == "D. Vrai"
    assert updated[0]["correct"] == "D"

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