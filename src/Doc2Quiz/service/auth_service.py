from Doc2Quiz.context import AppContext
from Doc2Quiz.auth import sign_in, sign_up

def handle_login(ctx: AppContext, email: str, password: str) -> tuple[AppContext, str]:
    ctx.user = sign_in(email, password)
    return ctx, f"Bienvenue {ctx.user.email} !"

def handle_register(ctx: AppContext, email: str, password: str) -> tuple[AppContext, str]:
    ctx.user = sign_up(email, password)
    return ctx, f"Compte créé : {ctx.user.email}"

def handle_logout(ctx: AppContext) -> tuple[AppContext, str]:
    ctx.logout()
    return ctx, "Déconnecté."