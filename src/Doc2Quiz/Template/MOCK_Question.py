'''
Fichier "fils" : contient les modèles de question selon le choix.
Il reçoit le type de révision de la part de "ui_gradio" et renvoie le modèle des questions correspondant.
'''

########################
## Questions de cours ##
########################
# pour les QCM ont a utilisation de QCM et réponse libre.
MOCK = [
    {
        "id": 1,
        "type": "qcm",
        "question": "Quelle est la formule du déterminant (delta) ?",
        "options": ["(a+b)(a-b)", "b² - 4ac", "a² - b²", "a² + b²"],
        "bonne_reponse": "b² - 4ac",
    },
    {
        "id": 2,
        "type": "cours_libre",
        "question": "Définissez brièvement le rôle du déterminant delta pour une équation du second degré :",
        "placeholder": "Rédigez votre définition ici...",
        "lignes": 3,
        "bonne_reponse": "Il indique le nombre et la nature des solutions réelles (2 si >0, 1 si =0, 0 si <0).",
    },
]


###############
## Exercices ##
###############
# pour les exercices, ont a utilisation de réponse libre avec grande zone de texte.
GABARIT_EXERCICES = [
    {
        "id": 1,
        "type": "exercice",
        "question": (
            "Exercice 1 - Résolution d'équation :\n"
            "Soit l'équation suivante : 2x² - 4x - 6 = 0.\n"
            "1. Calculez le discriminant delta.\n"
            "2. Déterminez les racines réelles x1 et x2.\n"
            "Détaillez l'ensemble de vos calculs et étapes."
        ),
        "placeholder": "Rédigez votre démarche, calculs intermédiaires et résultat final ici...",
        "lignes": 40, 
        "bonne_reponse": "delta = 64. Racines : x1 = -1 et x2 = 3.",
    },
    {
        "id": 2,
        "type": "exercice",
        "question": (
            "Exercice 2 - Étude de fonction :\n"
            "Soit f(x) = x³ - 3x + 2.\n"
            "1. Calculez f'(x).\n"
            "2. Déterminez les variations de f sur [-2; 2]."
        ),
        "placeholder": "Écrivez les étapes de votre raisonnement...",
        "lignes": 8,
        "bonne_reponse": "f'(x) = 3x² - 3. Croissante sur [-2; -1], décroissante sur [-1; 1], croissante sur [1; 2].",
    },
]

###################################
## Question de cours & Exercices ##
###################################
# pour ce type de révision, nous allons combinés les trois types de questions/réponses (QCM, réponse libre et exercices).
GABARIT_MIXTE = [
    {
        "id": 1,
        "type": "qcm",
        "question": "Quelle est la dérivée de f(x) = x² ?",
        "options": ["2x", "x", "2", "x² / 2"],
        "bonne_reponse": "2x",
    },
    {
        "id": 2,
        "type": "cours_libre",
        "question": "Quelle est la condition nécessaire pour qu'une fonction admette un extremum local en un point x0 ?",
        "placeholder": "Votre réponse théorique...",
        "lignes": 3,
        "bonne_reponse": "Sa dérivée première s'annule et change de signe en ce point.",
    },
    {
        "id": 3,
        "type": "exercice",
        "question": (
            "Exercice d'application :\n"
            "Calculez la dérivée de g(x) = (3x + 1)(x² - 2) et simplifiez l'expression."
        ),
        "placeholder": "Détaillez vos calculs ici...",
        "lignes": 8,
        "bonne_reponse": "g'(x) = 9x² + 2x - 6.",
    },
]


def get_template_quiz(type_revision: str) -> list[dict]:
    '''
    Reçoit le type de révision choisi par l'utilisateur et renvoie le modèle que l'utilisateur veut pour réviser
    '''
    if type_revision == "Questions de cours":
        return MOCK
    elif type_revision == "Exercices":
        return GABARIT_EXERCICES
    elif type_revision in [
        "Questions de cours & Exercices",
        "Questions de cours & exercices",
    ]:
        return GABARIT_MIXTE
    else:
        return MOCK