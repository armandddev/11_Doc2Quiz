from context import Role, UserContext
from db import get_db
import bcrypt
from pymongo.errors import DuplicateKeyError
from bson import ObjectId


async def sign_in(email: str, password: str) -> UserContext:
    db = get_db()
    row = await db.users.find_one({"email": email.strip()})

    if not row:
        raise ValueError("Identifiants incorrects.")

    pwd_hash = row["password_hash"]
    if isinstance(pwd_hash, str):
        pwd_hash_bytes = pwd_hash.encode("utf-8")
    else:
        pwd_hash_bytes = bytes(pwd_hash)

    if not pwd_hash_bytes.startswith((b"$2a$", b"$2b$", b"$2y$")) or len(pwd_hash_bytes) < 59:
        raise ValueError("Format de mot de passe invalide en base (hash corrompu ou tronqué).")

    if not bcrypt.checkpw(password.encode("utf-8"), pwd_hash_bytes):
        raise ValueError("Identifiants incorrects.")

    full_name = f"{row['first_name']} {row['last_name']}".strip()

    return UserContext(
        user_id=str(row["_id"]),
        email=row["email"],
        name=full_name,
        role=Role(row["role"]),
    )


async def sign_up(
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    role: Role = Role.STUDENT,
) -> UserContext:
    if not first_name or not last_name or not email or not password:
        raise ValueError("Tous les champs sont obligatoires.")

    if len(password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    doc = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password_hash": password_hash,
        "role": role.value,
    }

    try:
        db = get_db()
        result = await db.users.insert_one(doc)
    except DuplicateKeyError as e:
        raise ValueError("Cet email est déjà utilisé.") from e

    full_name = f"{first_name} {last_name}"

    return UserContext(
        user_id=str(result.inserted_id),
        email=email,
        name=full_name,
        role=role,
    )


async def update_user_profile(
    user_id: str,
    first_name: str,
    last_name: str,
    email: str,
    new_password: str = None,
) -> UserContext:
    if not first_name or not last_name or not email:
        raise ValueError("Le nom, prénom et email sont obligatoires.")

    update = {
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "email": email.strip(),
    }

    if new_password and new_password.strip():
        if len(new_password) < 8:
            raise ValueError("Le nouveau mot de passe doit contenir au moins 8 caractères.")
        update["password_hash"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    db = get_db()
    row = await db.users.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": update},
        return_document=True,
    )

    if not row:
        raise ValueError("Utilisateur introuvable.")

    full_name = f"{row['first_name']} {row['last_name']}".strip()

    return UserContext(
        user_id=str(row["_id"]),
        email=row["email"],
        name=full_name,
        role=Role(row["role"]),
    )


async def delete_user_account(user_id: str) -> bool:
    db = get_db()
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0