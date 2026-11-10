import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from shared.document.models import Section
from shared.document.segmentation import segment_text, _chunk_text
from shared.document import extraction


class FakeLLM:

    def __init__(self, response: str):
        self.response = response
        self.calls = 0
        self.prompts = []

    def generate_text(self, prompt, **kwargs):
        self.calls += 1
        self.prompts.append(prompt)
        return SimpleNamespace(response=self.response)


def test_segmentation_fait_un_appel_par_chunk():
    text = "Notion de cours. " * 400  # ~6800 caractères
    llm = FakeLLM('["Notion de cours"]')
    segment_text(text, [], llm_client=llm)
    nb_chunks = len(_chunk_text(text))
    print(f"\n[US-38] segmentation : {llm.calls} appel(s) pour {nb_chunks} chunk(s)")
    assert llm.calls == nb_chunks


def test_bug_section_sans_champs_obligatoires():
    with pytest.raises(TypeError):
        Section(**{"title": "a", "text": "b"})


def test_detection_llm_telle_que_concue_coute_1_appel_par_section(monkeypatch):
    """AVANT : si le bug était corrigé en gardant le LLM, 1 appel par section."""
    from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper
    from shared.document.detection import detection_section_displine

    appels = []

    def faux_generate(self, prompt, **kwargs):
        appels.append(prompt)
        return SimpleNamespace(response='{"discipline": "maths", "content_type": "calcul"}')

    monkeypatch.setattr(OllamaWrapper, "generate_text", faux_generate)
    sections = [{"title": f"S{i}", "text": f"Texte {i}"} for i in range(4)]
    for s in sections:
        detection_section_displine(extraction._to_section(s))

    print(f"\n[US-38] détection LLM : {len(appels)} appel(s) pour {len(sections)} sections")
    assert len(appels) == len(sections)


def test_detection_heuristique_0_appel_llm(monkeypatch):
    """APRÈS : content_type renseigné, 0 appel LLM."""
    from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper

    appels = []
    monkeypatch.setattr(
        OllamaWrapper, "generate_text",
        lambda self, prompt, **kw: appels.append(prompt) or SimpleNamespace(response="{}"),
    )
    sections = [
        {"title": "S0", "text": "Calculez la vitesse : 84 / 7 = 12 m/s."},
        {"title": "S1", "text": "Définissez la vitesse moyenne."},
        {"title": "S2", "text": "Un algorithme est une suite finie d'instructions."},
        {"title": "S3", "text": "Résolvez 3x² - 5x - 7 = 0."},
    ]
    resultat = extraction._detect_sections(sections)

    print(f"\n[US-38] détection heuristique : {len(appels)} appel(s) pour {len(sections)} sections")
    assert len(appels) == 0
    assert all("content_type" in s for s in resultat)


def test_summarize_text_n_a_aucun_appelant():
    src = Path(__file__).resolve().parents[2] / "src"
    appelants = []
    for f in src.rglob("*.py"):
        if f.name in ("summary.py", "__init__.py"):
            continue
        for n, ligne in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"summarize_text\s*\(", ligne):
                appelants.append(f"{f.name}:{n}")
    print(f"\n[US-38] summarize_text : {len(appelants)} appelant(s)")
    assert appelants == []


def test_generation_sans_resume_dans_le_prompt():
    from Doc2Quiz.service.core import generate_qcm_question

    reponse = (
        '{"question": "Quel est le rôle de la dérivation ?", '
        '"options": ["A. Mesurer une variation", "B. Trier des données", '
        '"C. Compresser un fichier", "D. Chiffrer un message"], '
        '"feedbacks": ["ok", "non", "non", "non"], "correct": "A"}'
    )
    llm = FakeLLM(reponse)
    generate_qcm_question("La dérivée mesure la variation d'une fonction.", "BUT", "Les deux", llm)

    print(f"\n[US-38] génération : {llm.calls} appel(s) pour 1 question")
    assert llm.calls == 1
    prompt = llm.prompts[0].lower()
    assert "résumé" not in prompt and "summary" not in prompt
    
ECHANTILLON = [
    ("Calculez la vitesse : 84 / 7 = 12 m/s.", "calcul"),
    ("Résolvez 3x² - 5x - 7 = 0.", "calcul"),
    ("Un train parcourt 120 km en 2 h. Calculez 120 / 2.", "calcul"),
    ("Définissez la vitesse moyenne.", "théorique"),
    ("Un algorithme est une suite finie d'instructions.", "théorique"),
    ("La dérivée mesure la variation d'une fonction.", "théorique"),
]
CAS_PIEGE = ("Le web a été inventé en 1989 par Tim Berners-Lee.", "théorique")


def test_cas_b_concordance_heuristique_vs_verite_terrain():
    from shared.document.detection import detection_section_heuristic

    def predit(texte):
        s = Section(id="x", title="x", level=None, text=texte, summary="",
                    notion_ids=None, pages=[])
        return detection_section_heuristic(s).content_type

    ok = sum(predit(t) == attendu for t, attendu in ECHANTILLON)
    acc = ok / len(ECHANTILLON)
    print(f"\n[US-38] Cas B : concordance {ok}/{len(ECHANTILLON)} = {acc:.0%}")
    t, attendu = CAS_PIEGE
    print(f"[US-38] Cas B (piège date + trait d'union) : prédit={predit(t)!r}, attendu={attendu!r}")
    assert acc >= 0.8