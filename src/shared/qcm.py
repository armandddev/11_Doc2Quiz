"""Fonctions communes utilisées par les pages de QCM."""

from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper
from Doc2Quiz.service.modif_service import corriger_question, modifier_question


def enregistrer_modification(questions, question_index, erreur):
    """Demande une correction IA et retourne le QCM corrigé et son affichage."""
    try:
        correction = corriger_question(
            questions[int(question_index)],
            erreur,
            OllamaWrapper(),
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
