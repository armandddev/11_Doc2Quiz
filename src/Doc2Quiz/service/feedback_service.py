from storage.feedback_storage import save_feedback, upsert_rating
from shared.logging import get_logger

logger = get_logger("feedback_service")


async def reject_generation(
    user_id: str,
    generation_id: str,
    motif: str,
) -> str:
    """
    Enregistre le rejet global d'un QCM.

    question_id est None : retour de niveau génération.
    Raises ValueError si le motif est vide ou la génération inconnue.
    """
    if not motif or not motif.strip():
        raise ValueError("Le motif de rejet est obligatoire.")
    if not generation_id:
        raise ValueError("Aucune génération active à rejeter.")

    feedback_id = await save_feedback(
        user_id=user_id,
        generation_id=generation_id,
        feedback_type="rejet",
        contenu=motif.strip(),
        question_id=None,
    )
    logger.info(
        "Rejet enregistré | generation=%s feedback=%s", generation_id, feedback_id
    )
    return feedback_id


async def correct_question(
    user_id: str,
    generation_id: str,
    question_id: str,
    correction: str,
) -> str:
    """
    Enregistre une correction libre sur une question ou un distracteur.

    Raises ValueError si la correction est vide ou si les IDs manquent.
    """
    if not correction or not correction.strip():
        raise ValueError("La correction ne peut pas être vide.")
    if not generation_id:
        raise ValueError("Aucune génération active.")
    if not question_id:
        raise ValueError("question_id est requis pour une correction.")

    feedback_id = await save_feedback(
        user_id=user_id,
        generation_id=generation_id,
        feedback_type="correction",
        contenu=correction.strip(),
        question_id=question_id,
    )
    logger.info(
        "Correction enregistrée | question=%s feedback=%s", question_id, feedback_id
    )
    return feedback_id


async def rate_question(
    user_id: str,
    generation_id: str,
    question_id: str,
    rating: str,
) -> str:
    """
    Upsert d'une notation 👍/👎 sur une question.

    rating doit être 'thumbs_up' ou 'thumbs_down'.
    Si l'utilisateur avait déjà noté cette question, la notation est écrasée
    (pas de doublon). Raises ValueError pour toute entrée invalide.
    """
    if rating not in ("thumbs_up", "thumbs_down"):
        raise ValueError(
            f"La notation doit être 'thumbs_up' ou 'thumbs_down', reçu : {rating!r}."
        )
    if not generation_id:
        raise ValueError("Aucune génération active.")
    if not question_id:
        raise ValueError("question_id est requis pour une notation.")

    feedback_id = await upsert_rating(
        user_id=user_id,
        generation_id=generation_id,
        question_id=question_id,
        contenu=rating,
    )
    label = "👍" if rating == "thumbs_up" else "👎"
    logger.info(
        "Notation upsert %s | question=%s feedback=%s", label, question_id, feedback_id
    )
    return feedback_id