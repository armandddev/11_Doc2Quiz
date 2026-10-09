from shared.document.extraction import extractFromPdf
from pathlib import Path
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from Doc2Quiz.ollama_client import OllamaWrapper
from Doc2Quiz.service.core import generation_qcm

SAMPLE_PDF = Path("data/coursarithm2627v2fini.pdf")

def test_pdf_is_segmented():
    document = extractFromPdf("docs/cahier_des_charges.pdf")

    assert document["text"]
    assert document["pages"] > 0
    assert isinstance(document["sections"], list)
    assert len(document["sections"]) > 0

    first_section = document["sections"][0]
    assert "id" in first_section
    assert "title" in first_section
    assert "summary" in first_section
    assert "notion_ids" in first_section
    assert first_section["notion_ids"] is None
    assert len(first_section["summary"]) > 10

    assert document["section_notion_links"] == []

    for section in document["sections"]:
        assert section["id"].startswith("section-")
        assert section["summary"]

def get_sections(filepath: str) -> list:
    return extractFromPdf(filepath).get("sections", [])

def section_text(s) -> str:
    return s.get("text") or s.get("content") or str(s)


def test_nb_sections_et_contenu():
    """Nombre de sections, sections vides, et taille — sur le vrai PDF."""
    sections = get_sections(str(SAMPLE_PDF))
    total = len(sections)
    print(f"\n[SEGMENTATION] {total} sections détectées")

    vides = [i for i, s in enumerate(sections) if not section_text(s).strip()]
    trop_courtes = [i for i, s in enumerate(sections) if 0 < len(section_text(s).split()) < 20]
    trop_longues = [i for i, s in enumerate(sections) if len(section_text(s).split()) > 500]

    for i, s in enumerate(sections):
        txt = section_text(s)
        print(f"  §{i+1} ({len(txt.split())} mots) : {txt[:60]!r}")

    print(f"\n  Vides        : {len(vides)}")
    print(f"  Trop courtes : {len(trop_courtes)} (< 20 mots)")
    print(f"  Trop longues : {len(trop_longues)} (> 500 mots)")

    assert 5 <= total <= 20,        f"{total} sections — cible 8-15 pour ~200 lignes"
    assert len(vides) == 0,         f"{len(vides)} sections vides"
    assert len(trop_courtes) == 0,  f"{len(trop_courtes)} sections < 20 mots"
    assert len(trop_longues) == 0,  f"{len(trop_longues)} sections > 500 mots"


def test_segmentation_par_llm():
    """Délègue la segmentation à Ollama IUT et vérifie le résultat."""
    client = OllamaWrapper()
    assert client.is_server_running(), "Serveur Ollama IUT inaccessible"

    raw_text = (
        extractFromPdf(str(SAMPLE_PDF)).get("raw_text", "")
        or " ".join(section_text(s) for s in get_sections(str(SAMPLE_PDF)))
    )

    prompt = (
        "Segmente ce cours en sections thématiques.\n"
        "Réponds UNIQUEMENT avec un tableau JSON, sans markdown :\n"
        '[{"titre": "...", "contenu": "..."}]\n\n'
        f"{raw_text[:3000]}"
    )

    res = client.generate_text(prompt)
    raw = res.response if hasattr(res, "response") else str(res)
    print(f"\n[LLM SEGMENTATION] Réponse brute : {raw[:200]!r}")

    start = raw.find("[")
    end = raw.rfind("]")

    assert start != -1, f"Pas de tableau JSON trouvé dans : {raw[:200]}"

    if end != -1 and end > start:
        fragment = raw[start:end + 1]
    else:
        fragment = raw[start:].rstrip()
        last_complete = fragment.rfind("},")
        if last_complete != -1:
            fragment = fragment[:last_complete + 1] + "]"
        else:
            fragment = fragment.rstrip(",{") + "]"

    try:
        sections = json.loads(fragment)
    except json.JSONDecodeError as e:
        pytest.fail(f"JSON invalide même après correction : {e}\nFragment : {fragment[:300]}")

    print(f"\n[LLM SEGMENTATION] {len(sections)} sections")
    for s in sections:
        print(f"  - {s.get('titre','?')} ({len(s.get('contenu','').split())} mots)")

    assert isinstance(sections, list) and len(sections) > 0
    assert all("titre" in s and "contenu" in s for s in sections), \
        "Chaque section doit avoir 'titre' et 'contenu'"
    assert all(len(s["contenu"].split()) >= 3 for s in sections), \
        "Certaines sections LLM ont un contenu vide"


def test_cap_max_sections():
    """Avec qcm_max_questions=3, on génère exactement 3 questions via Ollama IUT."""
    client = OllamaWrapper()
    assert client.is_server_running(), "Serveur Ollama IUT inaccessible"

    fake_doc = {
        "sections": [
            {"text": f"Section {i} — contenu suffisant pour générer une question QCM pertinente."}
            for i in range(6)
        ]
    }
    fake_file = type("F", (), {"name": "cours.pdf"})()

    with patch("Doc2Quiz.service.core.extractFromPdf", return_value=fake_doc), \
         patch("Doc2Quiz.service.core.settings") as s:
        s.anti_verbatim_threshold   = 0.4
        s.anti_verbatim_max_retries = 2
        s.qcm_max_questions         = 3
        results = generation_qcm(fake_file, client, level="Licence", revision="Les deux")

    print(f"\n[CAP] {len(results)} questions générées (cap=3, sections=6)")
    for i, q in enumerate(results):
        print(f"  Q{i+1} : {q.get('question','')[:80]}")

    assert len(results) == 3, f"Cap non respecté : {len(results)} questions au lieu de 3"