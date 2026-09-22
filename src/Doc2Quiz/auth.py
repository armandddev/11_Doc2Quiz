from Doc2Quiz.context import UserContext, Role
from Doc2Quiz.db import get_cursor
import bcrypt

def sign_in(email: str, password: str) -> UserContext:
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, email, name, password_hash, role FROM users WHERE email = %s",
            (email,),
        )
        row = cur.fetchone()

    if row is None:
        raise ValueError("Email ou mot de passe incorrect.")

    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        raise ValueError("Email ou mot de passe incorrect.")

    return UserContext(
        user_id=row["id"],
        email=row["email"],
        name=row["name"],
        role=Role(row["role"]),
    )

def sign_up(email: str, password: str, name: str, role: Role = Role.TEACHER) -> UserContext:
    if not email or not password or not name:
        raise ValueError("Email, nom et mot de passe obligatoires.")

    if len(password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO users (email, password_hash, name, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id, email, name, role
                """,
                (email, password_hash, name, role.value),
            )
            row = cur.fetchone()
    except Exception:
        raise ValueError("Cet email est déjà utilisé.")

    return UserContext(
        user_id=row["id"],
        email=row["email"],
        name=row["name"],
        role=Role(row["role"]),
    )