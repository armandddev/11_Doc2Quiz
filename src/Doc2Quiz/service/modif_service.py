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


def _answer_text(option: str) -> str:
    return re.sub(r"^[A-D][.)]\s*", "", str(option).strip(), flags=re.IGNORECASE).casefold()


def _requests_all_answers_changed(instruction: str) -> bool:
    text = instruction.casefold()
    return (
        "toutes" in text
        and any(word in text for word in ("réponse", "reponse", "option", "valeur"))
        and any(word in text for word in ("change", "modifie", "remplace", "reformule"))
    )


def _all_answers_changed(original: list[str], updated: list[str]) -> bool:
    original_answers = {_answer_text(option) for option in original}
    updated_answers = {_answer_text(option) for option in updated}
    return bool(updated_answers) and not original_answers.intersection(updated_answers)


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
    original_options = question.get("options", [])
    prompt = f"""Applique la demande de l'enseignant à cette question de QCM.
Réponds uniquement avec un JSON contenant les clés question, options et bonne_reponse.
Respecte exactement la demande. Si elle demande de changer les réponses, remplace
les textes des options concernés au lieu de les recopier.

Question actuelle : {question.get('question', '')}
Options actuelles : {original_options}
Réponse actuelle : {question.get('bonne_reponse', '')}
Demande de l'enseignant : {erreur}
"""

    for attempt in range(2):
        current_prompt = prompt
        if attempt:
            current_prompt += (
                "\nLa réponse précédente n'appliquait pas la demande. "
                "Réécris réellement les réponses demandées, sans recopier "
                "les textes existants."
            )
        response = llm_client.generate_text(current_prompt, format="json").response
        correction = _parse_correction_response(response)

        if not isinstance(correction.get("question"), str):
            raise ValueError("La correction IA ne contient pas de question valide.")
        if not isinstance(correction.get("options"), list):
            raise ValueError("La correction IA ne contient pas d'options valides.")
        if not isinstance(correction.get("bonne_reponse"), str):
            raise ValueError("La correction IA ne contient pas de bonne réponse valide.")

        if (
            _requests_all_answers_changed(erreur)
            and not _all_answers_changed(original_options, correction["options"])
        ):
            if attempt == 0:
                continue
            raise ValueError(
                "L'IA n'a pas modifié toutes les réponses demandées. Réessayez."
            )
        break

    return correction
