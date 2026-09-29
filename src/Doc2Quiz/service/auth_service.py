from context import AppContext
from auth import sign_in, sign_up

def handle_login(ctx: AppContext, email: str, password: str) -> tuple[AppContext, str]:
    if not email or not password:
        raise ValueError("Tous les champs sont obligatoires.")
    ctx.user = sign_in(email, password)
    return ctx, f"Bienvenue {ctx.user.email} !"


def handle_register(ctx: AppContext, email: str, password: str, name: str) -> tuple[AppContext, str]:
    if not email or not password or not name:
        raise ValueError("Tous les champs sont obligatoires.")
    ctx.user = sign_up(email, password, name)
    return ctx, f"Compte créé : {ctx.user.email}"
        

def handle_logout(ctx: AppContext) -> tuple[AppContext, str]:
    ctx.logout()
    return ctx, "Déconnecté."