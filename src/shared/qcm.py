"""Fonctions communes utilisées par les pages de QCM."""

import re

from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper
from Doc2Quiz.service.modif_service import corriger_question, modifier_question
from shared.logging import get_logger


logger = get_logger("qcm_correction")
QUESTION_NUMBER_RE = re.compile(r"\b(?:question|q)\s*(\d+)\b", re.IGNORECASE)
ANSWER_LETTER_RE = re.compile(
    r"\b(?:réponse|reponse|répondre|repondre|est|devrait être|doit être)"
    r"\s*(?:la\s+)?([A-D])\b",
    re.IGNORECASE,
)


def _apply_explicit_answer(correction: dict, error: str) -> None:
    """Force la lettre explicitement demandée par l'enseignant."""
    matches = ANSWER_LETTER_RE.findall(error)
    if not matches:
        return

    requested = matches[-1].upper()
    options = correction.get("options", [])
    for option in options:
        if str(option).strip()[:1].upper() == requested:
            correction["bonne_reponse"] = option
            logger.info(
                "Réponse explicite de l'enseignant appliquée : %s",
                requested,
            )
            return


def enregistrer_modification(questions, question_index, erreur, llm_client=None):
    """Corrige une ou plusieurs questions avec les erreurs fournies."""
    try:
        if llm_client is None:
            llm_client = OllamaWrapper()

        correction = corriger_question(
            questions[int(question_index)],
            erreur,
            llm_client,
        )
        updated_questions = modifier_question(
            questions,
            int(question_index),
            question=correction["question"],
            options=correction["options"],
            bonne_reponse=correction["bonne_reponse"],
        )
    except (IndexError, TypeError, ValueError) as error:
        return questions, "", "", None, f"**Correction non enregistrée :** {error}"
    return (
        updated_questions,
        correction["question"],
        "\n".join(correction["options"]),
        correction["bonne_reponse"],
        "**Correction IA enregistrée.**",
    )


def enregistrer_modifications(questions, erreurs, llm_client=None):
    """Corrige les questions correspondant aux lignes de corrections fournies."""
    try:
        if llm_client is None:
            llm_client = OllamaWrapper()

        errors_by_question = str(erreurs or "").splitlines()
        updated_questions = questions
        corrected_count = 0

        for line_index, error in enumerate(errors_by_question):
            if not error.strip():
                continue
            matches = list(QUESTION_NUMBER_RE.finditer(error))
            targets = [
                (
                    int(match.group(1)) - 1,
                    error[match.start():next_match.start() if next_match else None].strip(),
                )
                for match, next_match in zip(matches, matches[1:] + [None])
            ] or [(line_index, error)]

            for question_index, question_error in targets:
                if question_index >= len(questions):
                    raise IndexError(
                        f"La question {question_index + 1} n'existe pas."
                    )
                if question_index < 0:
                    raise ValueError(
                        f"Numéro de question invalide : {question_index + 1}."
                    )

                correction = corriger_question(
                    questions[question_index],
                    question_error,
                    llm_client,
                )
                _apply_explicit_answer(correction, question_error)
                logger.info(
                    "Correction question %d reçue : question=%r, bonne_reponse=%r",
                    question_index + 1,
                    correction.get("question"),
                    correction.get("bonne_reponse"),
                )
                updated_questions = modifier_question(
                    updated_questions,
                    question_index,
                    question=correction["question"],
                    options=correction["options"],
                    bonne_reponse=correction["bonne_reponse"],
                )
                logger.info(
                    "Correction question %d appliquée : question=%r, bonne_reponse=%r",
                    question_index + 1,
                    updated_questions[question_index].get("question"),
                    updated_questions[question_index].get("bonne_reponse"),
                )
                corrected_count += 1

        if corrected_count == 0:
            raise ValueError("Aucune correction n'a été renseignée.")
    except (IndexError, TypeError, ValueError) as error:
        return questions, "", "", None, f"**Corrections non enregistrées :** {error}"

    return (
        updated_questions,
        "",
        "",
        None,
        f"**{corrected_count} correction(s) IA enregistrée(s).** "
        "Le QCM affiché a été actualisé.",
    )
