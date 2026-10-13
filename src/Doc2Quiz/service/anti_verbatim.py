from typing import Set
from Doc2Quiz.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)

def get_ngrams(text: str, n: int = 4) -> Set[tuple]:
    """Génère des shingles de n mots."""
    words = text.lower().split()
    return set(zip(*[words[i:] for i in range(n)]))


def similarity_ratio(text_a: str, text_b: str, n: int = 4) -> float:
    """Part des n-grammes de text_a retrouvés dans text_b."""
    ngrams_a = get_ngrams(text_a, n)
    ngrams_b = get_ngrams(text_b, n)

    if not ngrams_a or not ngrams_b:
        return 0.0

    return len(ngrams_a & ngrams_b) / len(ngrams_a)


def is_too_similar(question: str, source_text: str) -> bool:
    threshold = settings.anti_verbatim_threshold

    for n in (4, 2):
        ratio = similarity_ratio(question, source_text, n=n)
        if ratio > threshold:
            logger.warning(
                "Question rejetée (similarité %d-grammes=%.2f > seuil=%.2f) | question=%r",
                n, ratio, threshold, question[:80]
            )
            return True
    return False