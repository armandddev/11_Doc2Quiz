import json
import time
from types import SimpleNamespace

import pytest

from Doc2Quiz.service.core import generation_qcm


pytestmark = pytest.mark.perf


class FauxClientLLM:
    """Client local qui remplace Ollama pendant le benchmark."""

    def __init__(self):
        self.nombre_appels = 0
        self.prompts = []

    def generate_text(self, prompt):
        self.nombre_appels += 1
        self.prompts.append(prompt)
        return SimpleNamespace(
            response=json.dumps(
                {
                    "question": "Quel est le rôle de la chlorophylle ?",
                    "options": [
                        "A. Absorber la lumière",
                        "B. Transporter l'oxygène",
                        "C. Produire des racines",
                        "D. Stocker l'eau",
                    ],
                    "correct": "A",
                }
            )
        )


def test_benchmark_pipeline_qcm_sans_reseau(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "shared.document.extraction._detect_sections",
        lambda sections: sections,
    )
    monkeypatch.setattr(
        "shared.document.segmentation.summarize_text",
        lambda text, summary_generator=None: text[:80],
    )

    fichier = tmp_path / "cours.md"
    fichier.write_text(
        "# Photosynthèse\n\n"
        "La chlorophylle absorbe la lumière et permet aux plantes de réaliser "
        "la photosynthèse.\n\n"
        "# Respiration\n\n"
        "Les cellules utilisent le glucose pour produire de l'énergie.\n\n"
        "# Écosystème\n\n"
        "Les êtres vivants et leur environnement forment un écosystème.",
        encoding="utf-8",
    )

    nombre_iterations = 5
    durees = []
    dernier_resultat = []
    client = FauxClientLLM()

    for _ in range(nombre_iterations):
        debut = time.perf_counter()
        dernier_resultat = generation_qcm(
            str(fichier),
            client,
            level="Licence",
            revision="Questions de cours",
        )
        durees.append(time.perf_counter() - debut)

    moyenne = sum(durees) / len(durees)
    print(
        f"\nBenchmark pipeline QCM hors réseau : "
        f"{moyenne:.4f} s en moyenne, {max(durees):.4f} s au maximum"
    )
    for index, resultat in enumerate(dernier_resultat, start=1):
        print(f"Question {index} : {resultat['question']}")
        print(f"Options : {', '.join(resultat['options'])}")
        print(f"Bonne réponse : {resultat['correct']}")

    assert len(dernier_resultat) == 3
    assert client.nombre_appels == nombre_iterations * 3
    assert len(client.prompts) == client.nombre_appels
    assert all("Licence" in prompt for prompt in client.prompts)
    assert all("question" in resultat for resultat in dernier_resultat)
    assert all(len(resultat["options"]) == 4 for resultat in dernier_resultat)
    assert all(resultat["correct"] == "A" for resultat in dernier_resultat)
    assert moyenne < 1.0
