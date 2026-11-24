from datetime import datetime, timezone

from Doc2Quiz.db import get_db


async def get_context_summary(user_id: str) -> str | None:
    """Retourne le résumé courant d'un profil."""
    document = await get_db().context_summaries.find_one(
        {"user_id": user_id},
        {"résumé": 1},
    )
    summary = document.get("résumé") if document else None
    return summary.strip() if isinstance(summary, str) and summary.strip() else None


async def save_context_summary(
    user_id: str,
    summary: str,
    feedback_count: int,
) -> None:
    """Crée ou remplace le résumé d'un profil."""
    await get_db().context_summaries.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "résumé": summary,
                "date_maj": datetime.now(timezone.utc),
                "nb_retours_utilisés": feedback_count,
            }
        },
        upsert=True,
    )


async def delete_context_summary(user_id: str) -> None:
    await get_db().context_summaries.delete_one({"user_id": user_id})
