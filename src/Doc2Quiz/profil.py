from context import AppContext
from db import get_cursor


def get_user_stats(ctx: AppContext) -> dict:
  if not ctx.is_authenticated:
    raise ValueError("Utilisateur non connecté.")

  with get_cursor() as cur:
    # Récupération de l'utilisateur complet
    cur.execute(
        """
            SELECT id, first_name, last_name, email, role, created_at 
            FROM users 
            WHERE id = %s
            """,
        (ctx.user.user_id,),
    )
    user_row = cur.fetchone()

    # Total des sessions / générations
    cur.execute(
        "SELECT COUNT(*) AS nb FROM generations WHERE user_id = %s",
        (ctx.user.user_id,),
    )
    gen_row = cur.fetchone()
    nb_sessions = gen_row["nb"] if gen_row else 0

  if not user_row:
    raise ValueError("Utilisateur introuvable en base de données.")

  return {
      "user_id": user_row["id"],
      "first_name": user_row["first_name"],
      "last_name": user_row["last_name"],
      "full_name": f"{user_row['first_name']} {user_row['last_name']}",
      "email": user_row["email"],
      "role": user_row["role"],
      "created_at": user_row["created_at"],
      "nb_sessions": nb_sessions,
  }