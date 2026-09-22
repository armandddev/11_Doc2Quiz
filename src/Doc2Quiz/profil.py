from Doc2Quiz.db import get_cursor
from Doc2Quiz.context import AppContext
from Template.TemplateProfil import TEMPLATE_ENTETE

def get_user_stats(ctx: AppContext) -> dict:
    if not ctx.is_authenticated:
        raise ValueError("Utilisateur non connecté.")

    with get_cursor() as cur:
        cur.execute(
            "SELECT created_at FROM users WHERE id = %s",
            (ctx.user.user_id,)
        )
        user_row = cur.fetchone()

        cur.execute(
            "SELECT COUNT(*) as nb FROM generations WHERE user_id = %s",
            (ctx.user.user_id,)
        )
        nb_sessions = cur.fetchone()["nb"]

    return {
        "email": ctx.user.email,
        "name": ctx.user.name,
        "role": ctx.user.role.value,
        "created_at": user_row["created_at"],
        "nb_sessions": nb_sessions,
    }

def render_profil(ctx: AppContext) -> str:
    stats = get_user_stats(ctx)
    initiales = "".join([n[0] for n in stats["name"].split()[:2]]).upper()

    return TEMPLATE_ENTETE.format(
        initiales=initiales,
        nom=stats["name"],
        formation=stats["role"],
        etablissement="",
        date_inscription=stats["created_at"].strftime("%d/%m/%Y"),
        nb_sessions=stats["nb_sessions"],
    )