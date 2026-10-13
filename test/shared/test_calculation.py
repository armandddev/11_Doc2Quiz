import json

import pytest

from shared.document.calculation import (
    contains_calculation,
    extract_numeric_values,
    generate_calculation_exercises,
    is_calculation_content_type,
    validate_calculation_text,
)


class FakeClient:
    def __init__(self, questions):
        self.questions = questions
        self.prompts = []

    def generate_text(self, prompt):
        self.prompts.append(prompt)

        class Result:
            response = json.dumps({"questions": self.questions})

        return Result()


def test_calculation_tag_comes_from_us08_contract():
    assert is_calculation_content_type("calcul")
    assert is_calculation_content_type(" Calcul ")
    assert not is_calculation_content_type("théorique")


def test_detects_real_calculation_and_numeric_values():
    assert contains_calculation("Calculez la vitesse : 84 / 7 = 12 m/s.")
    assert not contains_calculation("Définissez la vitesse moyenne.")
    assert extract_numeric_values("1,5 kg + 2 kg = 3,5 kg") == {1.5, 2.0, 3.5}


def test_rejects_source_values_and_definition_only_text():
    assert validate_calculation_text("Résolvez 3x² - 5x - 7 = 0.", {2, 4, 6})[0]
    assert not validate_calculation_text("Résolvez 2x² - 4x - 6 = 0.", {2, 4, 6})[0]
    assert not validate_calculation_text("Définissez le discriminant.", {2, 4, 6})[0]


def test_generates_exercises_without_touching_the_interface():
    client = FakeClient([
        {
            "id": 1,
            "question": "Résolvez 3x² - 5x - 7 = 0.",
            "bonne_reponse": "Delta = 109, puis calcul des deux racines.",
        }
    ])

    exercises = generate_calculation_exercises(
        "Pour ax² + bx + c = 0, on utilise delta = b² - 4ac. Exemple : 2x² - 4x - 6 = 0.",
        "mathématiques",
        count=1,
        client=client,
    )

    assert exercises[0]["type"] == "exercice"
    assert "Valeurs interdites" in client.prompts[0]


def test_does_not_generate_for_a_theoretical_section():
    with pytest.raises(ValueError, match="réservée aux sections de type calcul"):
        generate_calculation_exercises(
            "Le discriminant est une notion algébrique.",
            "mathématiques",
            count=1,
            content_type="théorique",
        )