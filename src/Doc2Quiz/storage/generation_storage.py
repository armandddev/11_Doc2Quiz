from datetime import datetime, timezone
 
from bson import ObjectId
 
from db import get_db
 
 
async def save_generation(
    user_id: str,
    document_name: str,
    level: str,
    revision: str,
    questions: list[dict],
) -> tuple[str, list[dict]]:
    """
    Persiste une génération et ses questions.
 
    Retourne (generation_id: str, questions_with_ids: list[dict]).
    Chaque dict de questions_with_ids est une copie enrichie avec '_id' (str).
    """
    db = get_db()
 
    # 1. Insérer la génération
    gen_doc = {
        "user_id": user_id,
        "document_name": document_name,
        "level": level,
        "revision": revision,
        "created_at": datetime.now(timezone.utc),
        "question_count": len(questions),
    }
    gen_result = await db.generations.insert_one(gen_doc)
    generation_id = str(gen_result.inserted_id)
 
    # 2. Insérer les questions avec leur position dans la génération
    questions_with_ids: list[dict] = []
    if questions:
        question_docs = [
            {
                "generation_id": generation_id,
                "user_id": user_id,
                "index": idx,
                "question": q.get("question", ""),
                "options": q.get("options", []),
                "correct": q.get("correct", ""),
                "feedbacks": q.get("feedbacks", []),
                "type": q.get("type", "qcm"),
                "section": q.get("section", {}),
            }
            for idx, q in enumerate(questions)
        ]
        q_result = await db.questions.insert_many(question_docs)
 
        for q, oid in zip(questions, q_result.inserted_ids):
            q_copy = dict(q)
            q_copy["_id"] = str(oid)
            questions_with_ids.append(q_copy)
 
    # 3. Mettre à jour la génération avec la liste des question_ids
    question_ids = [q["_id"] for q in questions_with_ids]
    await db.generations.update_one(
        {"_id": ObjectId(generation_id)},
        {"$set": {"question_ids": question_ids}},
    )
 
    return generation_id, questions_with_ids
 
 
async def append_questions(
    generation_id: str,
    user_id: str,
    new_questions: list[dict],
) -> list[dict]:
    """
    Ajoute des questions à une génération existante (cas expand_qcm).
    Retourne les nouveaux dicts enrichis avec '_id'.
    """
    db = get_db()
 
    # Compter les questions existantes pour calculer l'index de départ
    existing_count = await db.questions.count_documents(
        {"generation_id": generation_id}
    )
 
    question_docs = [
        {
            "generation_id": generation_id,
            "user_id": user_id,
            "index": existing_count + idx,
            "question": q.get("question", ""),
            "options": q.get("options", []),
            "correct": q.get("correct", ""),
            "feedbacks": q.get("feedbacks", []),
            "type": q.get("type", "qcm"),
            "section": q.get("section", {}),
        }
        for idx, q in enumerate(new_questions)
    ]
    q_result = await db.questions.insert_many(question_docs)
 
    enriched = []
    for q, oid in zip(new_questions, q_result.inserted_ids):
        q_copy = dict(q)
        q_copy["_id"] = str(oid)
        enriched.append(q_copy)
 
    # Mettre à jour la liste des question_ids dans la génération
    new_ids = [q["_id"] for q in enriched]
    await db.generations.update_one(
        {"_id": ObjectId(generation_id)},
        {
            "$push": {"question_ids": {"$each": new_ids}},
            "$inc": {"question_count": len(new_ids)},
        },
    )
 
    return enriched