"""Template pour la génération de QCM axés sur les questions de cours théoriques."""


def get_prompt_questions_cours(
    sujet: str, difficulte: str, contenu_doc: str
) -> str:
    return f"""Tu es un enseignant universitaire expert en {sujet}.
Génère un QCM de révision basé EXCLUSIVEMENT sur les notions théoriques, cours et définitions du document.
Niveau ciblé : {difficulte}

CONSIGNES :
1. Génère 3 questions de cours.
2. Pour chaque question, 4 choix possibles (1 seule bonne réponse).
3. Réponds UNIQUEMENT avec un JSON valide, sans balises de code Markdown.

FORMAT ATTENDU :
[
  {{
    "id": 1,
    "question": "Énoncé",
    "options": ["A", "B", "C", "D"],
    "bonne_reponse": "A",
    "explication": "Explication brève"
  }}
]

DOCUMENT :
\"\"\"
{contenu_doc}
\"\"\"
"""