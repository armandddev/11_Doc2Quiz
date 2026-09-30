from auth import sign_in, sign_up
from context import AppContext


def handle_login(
    ctx: AppContext, email: str, password: str
) -> tuple[AppContext, str]:
  if not email or not password:
    raise ValueError("Tous les champs sont obligatoires.")
  ctx.user = sign_in(email, password)
  return ctx, f"Bienvenue {ctx.user.name} !"


def handle_register(
    ctx: AppContext, email: str, password: str, name: str, fname: str
) -> tuple[AppContext, str]:
  if not email or not password or not name or not fname:
    raise ValueError("Tous les champs sont obligatoires.")

  # Utilise les noms de paramètres explicitement pour éviter tout décalage
  ctx.user = sign_up(
      first_name=fname.strip(),
      last_name=name.strip(),
      email=email.strip(),
      password=password,
  )
  return ctx, f"Compte créé avec succès pour {ctx.user.email}"


def handle_logout(ctx: AppContext) -> tuple[AppContext, str]:
  ctx.logout()
  return ctx, "Déconnecté."