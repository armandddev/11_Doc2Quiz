from context import AppContext
from profil import get_user_stats

MOIS_FR = [
    "",
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]


def get_profile_view_data(ctx: AppContext) -> tuple[str, str, str]:
  """Renvoie (titre_html, user_card_html, history_info_html)."""
  if not ctx or not ctx.is_authenticated:
    return (
        "<p style='color:red;'>Non connecté</p>",
        "<div class='user-id-left'><p>Veuillez vous connecter.</p></div>",
        "<div><p>0 session</p></div>",
    )

  stats = get_user_stats(ctx)

  # 1. Rôle / Statut
  role_label = (
      "Étudiant" if "student" in stats["role"].lower() else "Professeur"
  )
  titre_html = f"""
    <div style="margin: 20px 0 15px 0;">
        <h1 style="font-size: 2.8rem; font-weight: 700; color: #000000; margin: 0; line-height: 1.1;">
            Mon profil
        </h1>
        <p style="font-size: 1.1rem; color: #000000; margin: 6px 0 0 0; font-weight: 400;">
            Statut - {role_label}
        </p>
    </div>
    """

  # 2. Date et Initiales
  created = stats["created_at"]
  date_str = (
      f"{MOIS_FR[created.month]} {created.year}" if created else "récemment"
  )
  initiales = f"{stats['first_name'][0]}{stats['last_name'][0]}".upper()

  # 3. Carte utilisateur
  user_card_html = f"""
    <div class="user-id-left">
        <div class="user-avatar">{initiales}</div>
        <div class="user-details">
            <h2 class="user-fullname">{stats['full_name']}</h2>
            <p class="user-meta">Membre depuis {date_str} - {stats['nb_sessions']} sessions</p>
        </div>
    </div>
    """

  # 4. Encart historique de la zone de suppression
  history_html = f"""
    <div>
        <h4 style="margin: 0; font-size: 1rem; font-weight: 600; color: #1f2937;">Supprimer l'historique</h4>
        <p style="margin: 4px 0 0 0; font-size: 0.875rem; color: #6b7280;">Supprime toutes vos sessions précédentes ({stats['nb_sessions']} sessions)</p>
    </div>
    """

  return titre_html, user_card_html, history_html