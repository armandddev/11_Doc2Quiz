import pytest

from Doc2Quiz.ollama_client import OllamaWrapper
from Doc2Quiz.service.core import expand_qcm


@pytest.fixture
def ollama_client():
    """Utilise le serveur Ollama configuré dans l'environnement de test."""
    client = OllamaWrapper()
    if not client.is_server_running():
        pytest.skip(f"Serveur Ollama inaccessible : {client.base_url}")
    return client


def make_qcm(section_count=1):
    return [
        {
            "question": f"Question initiale de la section {index} ?",
            "options": ["A. Oui", "B. Non"],
            "correct": "A",
            "section": {
                "id": f"section-{index}",
                "title": f"Section {index}",
                "text": "Contenu pédagogique suffisamment détaillé pour générer des questions.",
            },
        }
        for index in range(section_count)
    ]


@pytest.mark.integration
def test_expand_qcm_ajoute_deux_questions_sur_un_qcm_existant(ollama_client):
    """Teste l'ajout direct sans extraction ni segmentation de document."""
    expanded = expand_qcm(
        make_qcm(),
        ollama_client,
        selected_sections=["section-0"],
    )

    assert len(expanded) == 3
    assert sum(question.get("is_new", False) for question in expanded) == 2
    assert len({question["question"] for question in expanded}) == len(expanded)


def test_expand_qcm_refuse_un_qcm_vide():
    with pytest.raises(ValueError, match="Aucun QCM"):
        expand_qcm([], OllamaWrapper())
