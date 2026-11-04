from datetime import datetime, timezone
from typing import Literal

from bson import ObjectId

from db import get_db

FeedbackType = Literal["correction", "rejet", "notation"]


async def save_feedback(
    user_id: str,
    generation_id: str,
    feedback_type: FeedbackType,
    contenu: str,
    question_id: str | None = None,
) -> str:
    """Insère un nouveau feedback et retourne son _id (str)."""
    doc = {
        "user_id": user_id,
        "generation_id": generation_id,
        "question_id": question_id,
        "type": feedback_type,
        "contenu": contenu,
        "date": datetime.now(timezone.utc),
    }
    db = get_db()
    result = await db.feedbacks.insert_one(doc)
    return str(result.inserted_id)


async def upsert_rating(
    user_id: str,
    generation_id: str,
    question_id: str,
    contenu: Literal["thumbs_up", "thumbs_down"],
) -> str:
    """
    Upsert d'une notation sur une question donnée.
    Si l'utilisateur avait déjà noté cette question, la valeur est écrasée
    (pas de doublon). Retourne le _id du document (nouveau ou existant).
    """
    db = get_db()
    result = await db.feedbacks.find_one_and_update(
        filter={
            "user_id": user_id,
            "generation_id": generation_id,
            "question_id": question_id,
            "type": "notation",
        },
        update={
            "$set": {
                "contenu": contenu,
                "date": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "user_id": user_id,
                "generation_id": generation_id,
                "question_id": question_id,
                "type": "notation",
            },
        },
        upsert=True,
        return_document=True,
    )
    return str(result["_id"]) if result else ""


async def get_feedbacks_for_generation(
    user_id: str,
    generation_id: str,
) -> list[dict]:
    """
    Retourne tous les feedbacks d'une génération pour un utilisateur donné.
    Isolation stricte : le filtre user_id garantit qu'aucun retour d'un autre
    profil n'est accessible.
    """
    db = get_db()
    cursor = db.feedbacks.find(
        {"user_id": user_id, "generation_id": generation_id}
    ).sort("date", 1)
    return [doc async for doc in cursor]


async def get_feedbacks_for_user(user_id: str) -> list[dict]:
    """Retourne tous les feedbacks d'un utilisateur, du plus récent au plus ancien."""
    db = get_db()
    cursor = db.feedbacks.find({"user_id": user_id}).sort("date", -1)
    return [doc async for doc in cursor]