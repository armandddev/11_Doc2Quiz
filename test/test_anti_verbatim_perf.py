from unittest.mock import patch
import pytest
from Doc2Quiz.service.anti_verbatim import is_too_similar, similarity_ratio, settings

MAX_RETRIES = 2
REALISTIC_CHUNK_SENTENCES = 3

TOKENS_PER_CALL = 600
PRICE_PER_1K_TOKENS = 0.003  

THRESHOLDS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]

SENTENCES = [
    "la photosynthèse est le processus par lequel les plantes produisent de l'énergie à partir de la lumière",
    "la mitochondrie produit l'énergie nécessaire au fonctionnement de la cellule",
    "le protocole http fonctionne selon un modèle de requête et de réponse entre un client et un serveur",
    "une clé primaire identifie de manière unique chaque ligne d'une table dans une base de données",
    "la révolution française commence en 1789 avec la prise de la bastille",
    "l'eau bout à cent degrés celsius sous la pression atmosphérique normale",
]

GOOD_PAIRS = [
    (SENTENCES[0], "comment les végétaux fabriquent-ils leur nourriture grâce au soleil ?"),
    (SENTENCES[1], "quel organite fournit de l'énergie aux cellules vivantes ?"),
    (SENTENCES[2], "dans un échange web, qui envoie la requête et qui y répond ?"),
    (SENTENCES[3], "à quoi sert la clé primaire d'une table relationnelle ?"),
    (SENTENCES[4], "quel événement symbolise le début de 1789 en france ?"),
    (SENTENCES[5], "à quelle température l'eau passe-t-elle à l'état gazeux au niveau de la mer ?"),
]

COPY_PAIRS = [
    (SENTENCES[0], "la photosynthèse est le processus par lequel les plantes produisent de l'énergie à partir de quoi ?"),
    (SENTENCES[1], "selon le texte, la mitochondrie produit l'énergie nécessaire au fonctionnement de la cellule ?"),
    (SENTENCES[2], "le protocole http fonctionne selon un modèle de requête et de réponse entre un client et quoi ?"),
    (SENTENCES[3], "une clé primaire identifie de manière unique chaque ligne d'une table dans quoi ?"),
    (SENTENCES[4], "la révolution française commence en 1789 avec la prise de quoi ?"),
    (SENTENCES[5], "l'eau bout à cent degrés celsius sous quelle pression atmosphérique normale ?"),
]

def rejection_rate(pairs, threshold):
    """Part des questions rejetees pour un seuil donne."""
    with patch("Doc2Quiz.service.anti_verbatim.settings") as mock_settings:
        mock_settings.anti_verbatim_threshold = threshold
        rejected = sum(is_too_similar(q, s) for s, q in pairs)
    return rejected / len(pairs)


def expected_calls(p_reject, max_retries=MAX_RETRIES):
    """
    Nombre moyen d'appels LLM par question si chaque tentative est rejetee avec
    la probabilite p_reject, de facon independante, avec au plus max_retries + 1 essais.
    """
    if p_reject >= 1.0:
        return max_retries + 1
    return (1 - p_reject ** (max_retries + 1)) / (1 - p_reject)


def cost_eur(calls):
    return calls * TOKENS_PER_CALL / 1000 * PRICE_PER_1K_TOKENS


def test_current_threshold_rejects_few_good_reformulations():
    """Un seuil trop strict force des retries inutiles sur de bonnes questions."""
    rate = rejection_rate(GOOD_PAIRS, settings.anti_verbatim_threshold)
    assert rate <= 0.2, f"{rate:.0%} des bonnes reformulations sont rejetees"


def test_current_threshold_rejects_most_near_copies():
    """Un seuil trop laxiste laisse passer des quasi-copies."""
    rate = rejection_rate(COPY_PAIRS, settings.anti_verbatim_threshold)
    assert rate >= 0.8, f"seulement {rate:.0%} des quasi-copies sont rejetees"


def test_expected_extra_cost_at_current_threshold():
    """Surcout moyen du a l'anti-verbatim sur de bonnes questions."""
    p = rejection_rate(GOOD_PAIRS, settings.anti_verbatim_threshold)
    calls = expected_calls(p)
    assert calls <= 1.3, f"{calls:.2f} appels par question en moyenne (surcout de {calls - 1:.0%})"


def test_threshold_sweep_report(capsys):
    """Tableau seuil / rejets / appels attendus / cout, et au moins un seuil qui convient."""
    suitable = []
    for t in THRESHOLDS:
        good = rejection_rate(GOOD_PAIRS, t)
        copy = rejection_rate(COPY_PAIRS, t)
        calls = expected_calls(good)
        print(f"seuil={t:.1f} bonnes_rejetees={good:.0%} copies_rejetees={copy:.0%} "
              f"appels_attendus={calls:.2f} cout={cost_eur(calls):.4f}EUR")
        if good <= 0.2 and copy >= 0.8:
            suitable.append(t)
    capsys.readouterr()
    assert suitable, "aucun seuil du balayage ne separe bonnes reformulations et quasi-copies"


def test_ratio_gap_between_good_and_copy():
    """Marge entre les deux groupes : si elle est faible, le seuil est fragile."""
    good_max = max(similarity_ratio(q, s) for s, q in GOOD_PAIRS)
    copy_min = min(similarity_ratio(q, s) for s, q in COPY_PAIRS)
    assert copy_min > good_max, (
        f"les groupes se chevauchent (bonne max={good_max:.2f}, copie min={copy_min:.2f})"
    )


def test_jaccard_dilution_on_longer_source(capsys):
    """
    Le Jaccard divise par l'union avec TOUT le support : une phrase copiee dans un
    morceau de plusieurs phrases a un ratio d'environ 1/k. Au-dela d'une certaine taille,
    une copie n'est plus rejetee.
    """
    verbatim = SENTENCES[0] + " ?"
    last_rejected = 0
    for k in range(1, len(SENTENCES) + 1):
        source = " ".join(SENTENCES[:k])
        ratio = similarity_ratio(verbatim, source)
        print(f"phrases_dans_le_support={k} ratio={ratio:.2f}")
        if ratio > settings.anti_verbatim_threshold:
            last_rejected = k
    capsys.readouterr()
    assert last_rejected >= REALISTIC_CHUNK_SENTENCES, (
        f"une phrase copiee n'est plus rejetee des {last_rejected + 1} phrases dans le support"
    )


def test_one_word_changed_every_fourth_is_rejected():
    """Une question qui garde 75 % des mots du support dans l'ordre doit etre rejetee."""
    words = SENTENCES[0].split()
    disguised = " ".join("x" if i % 4 == 3 else w for i, w in enumerate(words))
    assert is_too_similar(disguised, SENTENCES[0]) is True, (
        "copie deguisee non detectee : verifier que is_too_similar teste aussi les bigrammes "
        "et que le seuil est inferieur a 0.5"
    )


def test_short_copied_question_is_rejected():
    """Moins de 4 mots : les 4-grammes sont vides, les bigrammes doivent prendre le relais."""
    assert is_too_similar("la photosynthèse est", SENTENCES[0]) is True


def test_good_reformulations_not_rejected_on_long_source():
    """Les bigrammes courants ('de la', 'dans une') ne doivent pas faire rejeter une bonne question."""
    long_source = " ".join(SENTENCES)
    pairs = [(long_source, q) for _, q in GOOD_PAIRS]
    rate = rejection_rate(pairs, settings.anti_verbatim_threshold)
    assert rate <= 0.2, f"{rate:.0%} des bonnes reformulations rejetees sur un support long"