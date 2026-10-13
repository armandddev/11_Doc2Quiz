"""Modification et validation des questions QCM."""

from copy import deepcopy
from datetime import datetime, timezone
import json
import re

from shared.logging import get_logger


logger = get_logger("modif_service")


def _parse_correction_response(response: str) -> dict:
    """Extrait le premier objet JSON renvoyé par le modèle."""
    cleaned = (response or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    if start < 0:
        raise ValueError("L'IA n'a renvoyé aucun objet JSON de correction.")

    try:
        correction, _ = json.JSONDecoder().raw_decode(cleaned[start:])
    except json.JSONDecodeError as error:
        logger.warning(
            "Réponse de correction JSON invalide : %s | aperçu=%r",
            error,
            cleaned[:300],
        )
        raise ValueError(
            "La réponse de correction de l'IA n'est pas un JSON valide."
        ) from error

    if not isinstance(correction, dict):
        raise ValueError("La correction IA doit être un objet JSON.")
    return correction


def _normaliser_bonne_reponse(options: list[str], bonne_reponse: str) -> str:
    """Convertit une lettre IA (ex. B) vers l'option complète correspondante."""
    candidate = bonne_reponse.strip()
    if candidate in options:
        return candidate

    letter = candidate.rstrip(".:)- ").upper()
    if len(letter) == 1 and letter.isalpha():
        for option in options:
            if option.strip()[:1].upper() == letter:
                return option

    raise ValueError("La bonne réponse doit être une option.")


def modifier_question(
    questions: list[dict],
    question_index: int,
    *,
    question: str,
    options: list[str],
    bonne_reponse: str,
) -> list[dict]:
    """Retourne une copie du QCM avec la question sélectionnée corrigée."""
    if question_index < 0 or question_index >= len(questions):
        raise IndexError("La question demandée n'existe pas.")

    question = question.strip()
    options = [option.strip() for option in options]
    bonne_reponse = _normaliser_bonne_reponse(options, bonne_reponse)
    if not question or len(options) < 2 or any(not option for option in options):
        raise ValueError("L'énoncé et les options sont obligatoires.")

    modified_questions = deepcopy(questions)
    modified_question = modified_questions[question_index]
    modified_question["question"] = question
    modified_question["options"] = options
    modified_question["bonne_reponse"] = bonne_reponse
    modified_question["correct"] = next(
        option[0].upper()
        for option in options
        if option == bonne_reponse
    )
    modified_question["modifie_manuellement"] = True
    modified_question["date_modification"] = datetime.now(timezone.utc).isoformat()
    return modified_questions


def corriger_question(question: dict, erreur: str, llm_client) -> dict:
    """Demande à l'IA de corriger une question à partir de l'erreur signalée."""
    prompt = f"""Corrige cette question de QCM à partir de l'erreur signalée.
Réponds uniquement avec un JSON contenant les clés question, options et bonne_reponse.

Question actuelle : {question.get('question', '')}
Options actuelles : {question.get('options', [])}
Réponse actuelle : {question.get('bonne_reponse', '')}
Erreur signalée par l'enseignant : {erreur}
"""
    response = llm_client.generate_text(prompt).response
    correction = _parse_correction_response(response)

    if not isinstance(correction.get("question"), str):
        raise ValueError("La correction IA ne contient pas de question valide.")
    if not isinstance(correction.get("options"), list):
        raise ValueError("La correction IA ne contient pas d'options valides.")
    if not isinstance(correction.get("bonne_reponse"), str):
        raise ValueError("La correction IA ne contient pas de bonne réponse valide.")
    return correction
