import asyncio

from Doc2Quiz.ollama_client import OllamaWrapper
from shared.logging import get_logger
from Doc2Quiz.storage.context_summary_storage import (
    delete_context_summary,
    get_context_summary,
    save_context_summary,
)
from Doc2Quiz.storage.feedback_storage import get_feedbacks_for_user

logger = get_logger("context_summary_service")

SUMMARY_INSTRUCTION = (
    "À partir de ces retours, produis un résumé concis des erreurs récurrentes "
    "et des attentes de cet enseignant."
)
SUMMARY_MAX_CHARS = 2400


def limit_summary(summary: str) -> str:
    lines = [line.strip() for line in summary.splitlines() if line.strip()]
    return "\n".join(lines[:10])[:SUMMARY_MAX_CHARS].rstrip()

def build_summary_prompt(feedbacks: list[dict]) -> str:
    """Construit le prompt à partir de tous les contenus disponibles."""
    # Récupére les commentaires valides
    contents = "\n".join(
        f"- {feedback['contenu'].strip()}"
        for feedback in feedbacks
        if isinstance(feedback.get("contenu"), str)
        and feedback["contenu"].strip()
    )
    return (
        f"{SUMMARY_INSTRUCTION}\n"
        "Résume-les en 5 à 10 lignes maximum, sans introduction ni commentaire.\n\n"
        f"Retours de l'enseignant :\n{contents}"
    )


def _response_text(result: object) -> str:
    response = getattr(result, "response", result)
    if not isinstance(response, str):
        raise ValueError("La réponse du LLM n'est pas textuelle.")
    return response.strip()


async def refresh_context_summary(
    user_id: str,
    llm_client: object | None = None,
) -> str | None:
    """
    Endpoint interne POST /context-summaries/refresh adapté à l'app Gradio.
    Recalcule et persiste le résumé pour un profil.
    """
    feedbacks = await get_feedbacks_for_user(user_id)
    usable_feedbacks = [
        feedback
        for feedback in feedbacks
        if isinstance(feedback.get("contenu"), str)
        and feedback["contenu"].strip()
    ]
    if not usable_feedbacks:
        await delete_context_summary(user_id)
        return None

    client = llm_client or OllamaWrapper()
    # Génération du résumé par l'IA
    result = await asyncio.to_thread(
        client.generate_text,
        build_summary_prompt(usable_feedbacks),
        options={"temperature": 0.1, "num_predict": 256},
    )
    summary = limit_summary(_response_text(result))
    if not summary:
        raise ValueError("Le LLM a produit un résumé vide.")

    await save_context_summary(user_id, summary, len(usable_feedbacks))
    logger.info(
        "Résumé de contexte mis à jour | user=%s retours=%d",
        user_id,
        len(usable_feedbacks),
    )
    return summary


async def get_summary_for_generation(user_id: str) -> str | None:
    """Récupère uniquement le résumé stocké avant une génération."""
    try:
        return await get_context_summary(user_id)
    except Exception:
        logger.exception("Impossible de récupérer le résumé | user=%s", user_id)
        return None


def schedule_context_summary_refresh(user_id: str) -> None:
    """Déclenche l'actualisation du résumé en arrière-plan sans bloquer l'interface."""
    task = asyncio.create_task(refresh_context_summary(user_id))

    def report_failure(completed_task: asyncio.Task) -> None:
        if completed_task.cancelled():
            return
        error = completed_task.exception()
        if error:
            logger.error(
                "Mise à jour asynchrone du résumé échouée | user=%s : %s",
                user_id,
                error,
            )

    task.add_done_callback(report_failure)
