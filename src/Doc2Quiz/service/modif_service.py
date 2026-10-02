"""Modification et validation des questions QCM."""

from copy import deepcopy
from datetime import datetime, timezone
import json


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
    bonne_reponse = bonne_reponse.strip()
    if not question or len(options) < 2 or any(not option for option in options):
        raise ValueError("L'énoncé et les options sont obligatoires.")
    if bonne_reponse not in options:
        raise ValueError("La bonne réponse doit être une option.")

    modified_questions = deepcopy(questions)
    modified_question = modified_questions[question_index]
    modified_question["question"] = question
    modified_question["options"] = options
    modified_question["bonne_reponse"] = bonne_reponse
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
    correction = json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())

    if not isinstance(correction.get("question"), str):
        raise ValueError("La correction IA ne contient pas de question valide.")
    if not isinstance(correction.get("options"), list):
        raise ValueError("La correction IA ne contient pas d'options valides.")
    if not isinstance(correction.get("bonne_reponse"), str):
        raise ValueError("La correction IA ne contient pas de bonne réponse valide.")
    return correction
