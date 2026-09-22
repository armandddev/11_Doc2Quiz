from Doc2Quiz.context import AppContext
from Doc2Quiz.profil import get_user_stats
from Template.TemplateProfil import TEMPLATE_ENTETE


def render_profil(ctx: AppContext) -> str:
    stats = get_user_stats(ctx)
    initiales = "".join(stats["email"].split("@")[0].split(".")[:2]).upper()[:2]

    return TEMPLATE_ENTETE.format(
        initiales=initiales,
        nom=stats["email"],
        formation=stats["role"],
        etablissement="",
        date_inscription=stats["created_at"].strftime("%d/%m/%Y"),
        nb_sessions=stats["nb_sessions"],
    )