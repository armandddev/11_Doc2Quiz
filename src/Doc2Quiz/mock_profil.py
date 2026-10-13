"""mock_profil.py
Données mockées à injecter dans les templates pour les tests front.
"""

MOCK_UTILISATEUR = {
    "nom": "Alice Laurent",
    "formation": "BUT2 Informatique",
    "etablissement": "IUT de Lyon",
    "date_inscription": "août 2026",
    "nb_sessions": 18,
}

MOCK_COMPETENCES = [
    {
        "domaine": "Probabilités",
        "score": 72,
        "couleur": "#3b82f6",  # Bleu
    },
    {
        "domaine": "Algèbre",
        "score": 88,
        "couleur": "#22c55e",  # Vert
    },
    {
        "domaine": "Statistiques",
        "score": 54,
        "couleur": "#ef4444",  # Rouge
    },
]