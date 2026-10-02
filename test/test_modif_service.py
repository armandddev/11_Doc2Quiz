from types import SimpleNamespace

from Doc2Quiz.service.modif_service import corriger_question, modifier_question


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