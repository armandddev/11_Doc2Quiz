from context import Role, UserContext
from db import get_cursor
import bcrypt
import psycopg


def sign_in(email: str, password: str) -> UserContext:
  with get_cursor() as cur:
    cur.execute(
        """
            SELECT id, first_name, last_name, email, password_hash, role 
            FROM users 
            WHERE email = %s
            """,
        (email,),
    )
    row = cur.fetchone()

  if row is None or not bcrypt.checkpw(
      password.encode(), row["password_hash"].encode()
  ):
    raise ValueError("Email ou mot de passe incorrect.")

  full_name = f"{row['first_name']} {row['last_name']}"

  return UserContext(
      user_id=row["id"],
      email=row["email"],
      name=full_name,
      role=Role(row["role"]),
  )


def sign_up(
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

  try:
    with get_cursor(commit=True) as cur:
      cur.execute(
          """
                INSERT INTO users (first_name, last_name, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, first_name, last_name, email, role
                """,
          (first_name, last_name, email, password_hash, role.value),
      )
      row = cur.fetchone()
  except psycopg.errors.UniqueViolation as e:
    raise ValueError("Cet email est déjà utilisé.") from e

  full_name = f"{row['first_name']} {row['last_name']}"

  return UserContext(
      user_id=row["id"],
      email=row["email"],
      name=full_name,
      role=Role(row["role"]),
  )