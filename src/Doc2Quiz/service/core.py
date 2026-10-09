import json
from pathlib import Path

from Doc2Quiz.service.anti_verbatim import is_too_similar
from Doc2Quiz.config import settings
from shared.logging import get_logger
from shared.document import extractFromPdf, extractFromMd

logger = get_logger("core")

_LEVEL_LABELS = {
    "BUT":      "BUT (Bac+2/3, approche technologique et professionnelle)",
    "Licence":  "Licence (Bac+3, fondamentaux académiques)",
    "Master":   "Master (Bac+5, approche avancée et analytique)",
    "Doctorat": "Doctorat (niveau recherche, rigueur scientifique maximale)",
}

_REVISION_LABELS = {
    "Questions de cours": "une question de cours théorique (définition, concept, mécanisme)",
    "Exercices":          "une question d'application pratique (calcul, démarche, cas concret)",
    "Les deux":           "une question de cours OU d'application pratique",
}


# Extraction
def process_uploaded_pdf(file_input) -> dict:
    filepath = file_input.name if hasattr(file_input, "name") else str(file_input)
    return extractFromPdf(filepath)


def process_uploaded_md(file_input) -> dict:
    filepath = file_input.name if hasattr(file_input, "name") else str(file_input)
    return extractFromMd(filepath)


# Parsing JSON robuste

def _parse_llm_json(raw: str) -> dict | None:
    text = raw.strip()

    # Retire les balises markdown si présentes
    if text.startswith("```"):
        lines = [l for l in text.splitlines() if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Tentative directe
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extrait le premier objet JSON dans la chaîne
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    return None


# Generate question

def generate_qcm_question(
    source_text: str,
    level: str,
    revision_type: str,
    llm_client,
) -> dict:
    """
    Génère une question QCM (4 options, 1 correcte) pour une section.
    Retourne un dict : { question, options, correct, type }.
    """
    level_label    = _LEVEL_LABELS.get(level, "niveau universitaire généraliste")
    revision_label = _REVISION_LABELS.get(revision_type, "une question de compréhension")

    JSON_FORMAT = (
        "Réponds UNIQUEMENT avec un objet JSON valide, sans markdown, sans texte autour.\n"
        "Format attendu :\n"
        '{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "correct": "A"}\n\n'
        "Règles :\n"
        "- La question teste la compréhension, pas la mémorisation mot pour mot\n"
        "- 4 options plausibles, une seule correcte\n"
        "- Écris les formules mathématiques en texte simple (ex: 'a puissance 13 modulo n'), pas en LaTeX\n"
        '- "correct" contient uniquement la lettre : A, B, C ou D'
    )

    prompt_initial = (
        f"Tu es un enseignant expert. Génère {revision_label} de type QCM "
        f"adaptée au {level_label}.\n\n"
        f"Texte source :\n{source_text}\n\n"
        f"{JSON_FORMAT}"
    )

    prompt_rephrase = (
        "Ta question précédente était trop proche mot pour mot du texte source. "
        "Reformule-la avec une structure et des mots complètement différents.\n\n"
        f"Texte source :\n{source_text}\n\n"
        f"{JSON_FORMAT}"
    )

    last_result: dict | None = None

    for attempt in range(settings.anti_verbatim_max_retries + 1):
        prompt = prompt_initial if attempt == 0 else prompt_rephrase

        # Appel LLM
        try:
            res = llm_client.generate_text(prompt)
            raw = res.response if hasattr(res, "response") else str(res)
        except Exception as exc:
            logger.error("Erreur appel LLM (tentative %d) : %s", attempt + 1, exc)
            continue

        # Parse JSON
        parsed = _parse_llm_json(raw)
        if parsed is None:
            logger.warning(
                "Réponse LLM non-JSON (tentative %d) : %r", attempt + 1, raw[:120]
            )
            last_result = {
                "question": raw.strip(),
                "options":  [],
                "correct":  "",
                "type":     "qcm",
            }
            continue

        question_text = parsed.get("question", "").strip()
        options       = parsed.get("options", [])
        correct       = parsed.get("correct", "A").strip().upper()

        # Anti-verbatim
        if not is_too_similar(question_text, source_text):
            logger.info("Question acceptée (tentative %d)", attempt + 1)
            return {
                "question": question_text,
                "options":  options,
                "correct":  correct,
                "type":     "qcm",
            }

        logger.warning("Tentative %d rejetée — trop similaire au source", attempt + 1)
        last_result = {
            "question": question_text,
            "options":  options,
            "correct":  correct,
            "type":     "qcm",
        }

    logger.error(
        "Échec anti-verbatim après %d tentatives — retour de la dernière question",
        settings.anti_verbatim_max_retries + 1,
    )
    return last_result or {"question": "", "options": [], "correct": "", "type": "qcm"}


# Generate QCM

def generation_qcm(
    file_input,
    llm_client,
    level: str = "",
    revision: str = "Les deux",
) -> list[dict]:
    """
    Extrait le document → segmente en sections → génère 1 question QCM par section.
    Retourne une liste de dicts { question, options, correct, type, section }.
    """
    filename  = file_input.name if hasattr(file_input, "name") else str(file_input)
    extension = Path(filename).suffix.lower()

    if extension == ".md":
        document = process_uploaded_md(file_input)
    elif extension == ".pdf":
        document = process_uploaded_pdf(file_input)
    else:
        raise ValueError(f"Format de fichier non supporté : {extension}")
    
    sections_raw = document.get("sections", [])
    max_q = getattr(settings, "qcm_max_questions", len(sections_raw))
    sections_raw = sections_raw[:max_q]
    total = len(sections_raw)
    logger.info(f"[{total}] sections détectées (cap={max_q})")

    qcm: list[dict] = []

    for idx, section in enumerate(sections_raw, start=1):
        if isinstance(section, dict):
            source_text = section.get("text") or section.get("content") or str(section)
        else:
            source_text = str(section)

        if not source_text.strip():
            continue

        logger.info(f"[{idx}/{total}] Génération en cours...")
        question_data = generate_qcm_question(source_text, level, revision, llm_client)
        question_data["section"] = section
        if not question_data.get("question"):
            logger.warning(f"[{idx}/{total}] Section ignorée — question vide")
            continue
        qcm.append(question_data)
        logger.info(f"[{idx}/{total}] Question générée")

    logger.info(f"QCM terminé — {len(qcm)} questions")
    return qcm