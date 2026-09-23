# tests/test_anti_verbatim.py
from Doc2Quiz.service.anti_verbatim import get_ngrams, similarity_ratio, is_too_similar
from unittest.mock import patch
import pytest


# Test que les n-grammes sont bien générés depuis un texte
def test_get_ngrams_basic():
    ngrams = get_ngrams("le chat mange la souris", n=4)
    assert isinstance(ngrams, set)
    assert len(ngrams) > 0
    assert ("le", "chat", "mange", "la") in ngrams


# Test que les n-grammes sont vides si le texte est trop court
def test_get_ngrams_too_short():
    ngrams = get_ngrams("trop court", n=4)
    assert ngrams == set()


# Test que deux textes identiques ont un ratio de 1.0
def test_similarity_ratio_identical():
    text = "la photosynthèse est un processus biologique fondamental"
    assert similarity_ratio(text, text) == 1.0


# Test que deux textes complètement différents ont un ratio proche de 0
def test_similarity_ratio_different():
    text_a = "la photosynthèse est un processus biologique fondamental"
    text_b = "le volcan entre en éruption pendant la nuit froide"
    ratio = similarity_ratio(text_a, text_b)
    assert ratio < 0.1


# Test que deux textes vides retournent 0.0 sans erreur
def test_similarity_ratio_empty():
    assert similarity_ratio("", "") == 0.0


# Test qu'une question verbatim est bien rejetée (similarité trop haute)
def test_is_too_similar_verbatim():
    source = "la photosynthèse est le processus par lequel les plantes produisent de l'énergie"
    question = "la photosynthèse est le processus par lequel les plantes produisent de l'énergie ?"
    assert is_too_similar(question, source) is True


# Test qu'une question reformulée est bien acceptée (similarité basse)
def test_is_too_similar_reformulated():
    source = "la photosynthèse est le processus par lequel les plantes produisent de l'énergie"
    question = "comment les végétaux fabriquent-ils leur nourriture grâce à la lumière solaire ?"
    assert is_too_similar(question, source) is False


# Test que le seuil est bien lu depuis la config et non en dur
def test_is_too_similar_custom_threshold():
    source = "la photosynthèse convertit la lumière en énergie chimique utilisable"
    question = "la photosynthèse convertit la lumière en énergie chimique utilisable ?"

    # Seuil très haut → même un verbatim passe
    with patch("Doc2Quiz.service.anti_verbatim.settings") as mock_settings:
        mock_settings.anti_verbatim_threshold = 0.99
        assert is_too_similar(question, source) is False

    # Seuil très bas → tout est rejeté
    with patch("Doc2Quiz.service.anti_verbatim.settings") as mock_settings:
        mock_settings.anti_verbatim_threshold = 0.01
        assert is_too_similar(question, source) is True