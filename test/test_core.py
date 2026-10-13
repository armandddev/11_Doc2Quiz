from pathlib import Path
import pytest
from Doc2Quiz.service.core import generate_question, generation_qcm
from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper


@pytest.fixture
def llm_client():
    """Fixture instanciant le vrai wrapper Ollama."""
    return OllamaWrapper()


def test_generate_question_avec_ollama(llm_client):
    """Teste la génération directe d'une question avec le vrai LLM."""
    source = (
        "La photosynthèse est le processus par lequel les plantes vertes "
        "convertissent la lumière du soleil en énergie chimique sous forme de glucose."
    )

    resultat = generate_question(source, llm_client)

    print(f"\n--- Question générée par Ollama : {resultat}")
    assert isinstance(resultat, str)
    assert len(resultat) > 10


def test_generation_qcm_avec_fichier_md(tmp_path, llm_client):
    """Teste le flux complet d'extraction et génération QCM depuis un fichier Markdown."""
    fichier_test = tmp_path / "cours_photosynthese.md"
    fichier_test.write_text(
        "# La Photosynthèse\n\n"
        "La photosynthèse est le processus par lequel les plantes vertes "
        "convertissent la lumière du soleil en énergie chimique sous forme de glucose.",
        encoding="utf-8"
    )

    resultats = generation_qcm(str(fichier_test), llm_client)

    print(f"\n--- Résultat QCM : {resultats}")

    assert isinstance(resultats, list)
    assert len(resultats) > 0
    assert "question" in resultats[0]
    assert isinstance(resultats[0]["question"], str)
    assert len(resultats[0]["question"]) > 10


def test_generation_qcm_extension_invalide(llm_client):
    """Vérifie que la fonction lève une erreur pour un format non supporté."""
    with pytest.raises(ValueError, match="Format de fichier non"):
        generation_qcm("fichier.txt", llm_client)

def test_generation_qcm(tmp_path):
    # Création d'un vrai fichier Markdown de test
    fichier_test = tmp_path / "cours_photosynthese.md"
    fichier_test.write_text(
        "# La Photosynthèse\n\n"
        "La photosynthèse est le processus par lequel les plantes vertes "
        "convertissent la lumière du soleil en énergie chimique sous forme de glucose.",
        encoding="utf-8"
    )

    # Générations
    llm_client = OllamaWrapper()
    resultats = generation_qcm(str(fichier_test), llm_client)

    # Affichage dans la console
    print(resultats)

    # tests
    assert isinstance(resultats, list)
    assert len(resultats) > 0
    assert "question" in resultats[0]
    assert isinstance(resultats[0]["question"], str)
    assert len(resultats[0]["question"]) > 10