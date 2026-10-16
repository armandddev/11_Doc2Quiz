import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        user = os.environ["MONGO_USER"]
        password = os.environ["MONGO_PASSWORD"]
        host = os.environ["MONGO_HOST"]
        port = os.environ["MONGO_PORT"]
        _client = AsyncIOMotorClient(
            f"mongodb://{user}:{password}@{host}:{port}/"
        )
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[os.environ["MONGO_DB"]]


async def init_indexes() -> None:
    """Crée les index sur les champs filtrés fréquemment."""
    db = get_db()
    await db.users.create_index("email", unique=True)
    await db.documents.create_index("user_id")
    await db.generations.create_index("user_id")
    await db.generations.create_index("document_id")
    await db.questions.create_index("generation_id")
    await db.feedbacks.create_index("user_id")
    await db.feedbacks.create_index("generation_id")
    await db.feedbacks.create_index([("user_id", 1), ("generation_id", 1)])
    await db.context_summaries.create_index("user_id", unique=True)