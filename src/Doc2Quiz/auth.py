from context import Role, UserContext
from db import get_cursor, get_connection
import bcrypt
import psycopg



def sign_in(email: str, password: str) -> UserContext:
  with get_connection() as conn:
    with conn.cursor() as cur:
      cur.execute(
          """
                SELECT id, email, first_name, last_name, password_hash, role
                FROM users 
                WHERE email = %s
            """,
          (email.strip(),),
      )
      row = cur.fetchone()

  if not row:
    raise ValueError("Identifiants incorrects.")

  # Gestion tuple ou dict selon la factory du curseur
  if isinstance(row, dict):
    user_id = row["id"]
    user_email = row["email"]
    first_name = row["first_name"]
    last_name = row["last_name"]
    pwd_hash = row["password_hash"]
    role_val = row["role"]
  else:
    user_id, user_email, first_name, last_name, pwd_hash, role_val = row

  if isinstance(pwd_hash, memoryview):
    pwd_hash_bytes = pwd_hash.tobytes()
  elif isinstance(pwd_hash, str):
    if pwd_hash.startswith("b'") and pwd_hash.endswith("'"):
      pwd_hash = pwd_hash[2:-1]
    pwd_hash_bytes = pwd_hash.encode("utf-8")
  else:
    pwd_hash_bytes = bytes(pwd_hash)

  if not pwd_hash_bytes.startswith(
      (b"$2a$", b"$2b$", b"$2y$")
  ) or len(pwd_hash_bytes) < 59:
    raise ValueError(
        "Format de mot de passe invalide en base (hash corrompu ou tronqué)."
    )

  if not bcrypt.checkpw(password.encode("utf-8"), pwd_hash_bytes):
    raise ValueError("Identifiants incorrects.")

  full_name = f"{first_name} {last_name}".strip()
  user_role = (
      Role(role_val)
      if isinstance(role_val, str)
      else (Role.TEACHER if role_val == Role.TEACHER else Role.STUDENT)
  )

  return UserContext(
      user_id=user_id, email=user_email, name=full_name, role=user_role
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


def update_user_profile(
    user_id: int,
    first_name: str,
    last_name: str,
    email: str,
    new_password: str = None,
) -> UserContext:
  if not first_name or not last_name or not email:
    raise ValueError("Le nom, prénom et email sont obligatoires.")

  with get_connection() as conn:
    with conn.cursor() as cur:
      # Si l'utilisateur a tapé un nouveau mot de passe
      if new_password and new_password.strip():
        if len(new_password) < 8:
          raise ValueError(
              "Le nouveau mot de passe doit contenir au moins 8 caractères."
          )
        pwd_hash = bcrypt.hashpw(
            new_password.encode(), bcrypt.gensalt()
        ).decode()
        cur.execute(
            """
                    UPDATE users 
                    SET first_name = %s, last_name = %s, email = %s, password_hash = %s
                    WHERE id = %s
                    RETURNING id, first_name, last_name, email, role
                """,
            (first_name.strip(), last_name.strip(), email.strip(), pwd_hash, user_id),
        )
      else:
        # Mise à jour sans toucher au mot de passe existant
        cur.execute(
            """
                    UPDATE users 
                    SET first_name = %s, last_name = %s, email = %s
                    WHERE id = %s
                    RETURNING id, first_name, last_name, email, role
                """,
            (first_name.strip(), last_name.strip(), email.strip(), user_id),
        )
      row = cur.fetchone()

  if not row:
    raise ValueError("Utilisateur introuvable.")

  if isinstance(row, dict):
    u_id, f_name, l_name, u_email, u_role = (
        row["id"],
        row["first_name"],
        row["last_name"],
        row["email"],
        row["role"],
    )
  else:
    u_id, f_name, l_name, u_email, u_role = row

  full_name = f"{f_name} {l_name}".strip()
  role_enum = Role(u_role) if isinstance(u_role, str) else u_role

  return UserContext(
      user_id=u_id, email=u_email, name=full_name, role=role_enum
  )

def delete_user_account(user_id: int) -> bool:
  with get_connection() as conn:
    with conn.cursor() as cur:
      # Si les quiz/sessions sont liés sans ON DELETE CASCADE, supprime-les d'abord :
      # cur.execute("DELETE FROM quiz_sessions WHERE user_id = %s", (user_id,))
      # cur.execute("DELETE FROM documents WHERE user_id = %s", (user_id,))

      cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
      return cur.rowcount > 0