from typing import Set
from Doc2Quiz.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)

def get_ngrams(text: str, n: int = 4) -> Set[tuple]:
    """Génère des shingles de n mots."""
    words = text.lower().split()
    return set(zip(*[words[i:] for i in range(n)]))


def similarity_ratio(text_a: str, text_b: str, n: int = 4) -> float:
    """Ratio de Jaccard sur les n-grammes communs."""
    ngrams_a = get_ngrams(text_a, n)
    ngrams_b = get_ngrams(text_b, n)

    if not ngrams_a or not ngrams_b:
        return 0.0

    intersection = ngrams_a & ngrams_b
    union = ngrams_a | ngrams_b
    return len(intersection) / len(union)


def is_too_similar(question: str, source_text: str) -> bool:
    ratio = similarity_ratio(question, source_text)
    threshold = settings.anti_verbatim_threshold

    if ratio > threshold:
        logger.warning(
            "Question rejetée (similarité=%.2f > seuil=%.2f) | question=%r",
            ratio, threshold, question[:80]
        )
        return True
    return False