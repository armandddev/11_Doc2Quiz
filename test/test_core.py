# tests/test_core.py
from unittest.mock import MagicMock, patch
import pytest
from Doc2Quiz.service.core import generate_question


def test_generate_question_accepted_first_try():
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "comment les végétaux fabriquent-ils leur nourriture ?"

    source = "la photosynthèse est le processus par lequel les plantes produisent de l'énergie"

    with patch("Doc2Quiz.service.core.is_too_similar", return_value=False):
        result = generate_question(source, mock_llm)

    assert result == "comment les végétaux fabriquent-ils leur nourriture ?"
    assert mock_llm.generate.call_count == 1


def test_generate_question_retry_on_similar():
    mock_llm = MagicMock()
    mock_llm.generate.side_effect = [
        "la photosynthèse est le processus par lequel les plantes produisent de l'énergie ?",
        "comment les végétaux fabriquent-ils leur nourriture grâce à la lumière ?",
    ]

    source = "la photosynthèse est le processus par lequel les plantes produisent de l'énergie"

    with patch("Doc2Quiz.service.core.is_too_similar", side_effect=[True, False]):
        result = generate_question(source, mock_llm)

    assert result == "comment les végétaux fabriquent-ils leur nourriture grâce à la lumière ?"
    assert mock_llm.generate.call_count == 2


def test_generate_question_rephrase_prompt_is_different():
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "une question quelconque"

    source = "la photosynthèse est le processus par lequel les plantes produisent de l'énergie"

    with patch("Doc2Quiz.service.core.is_too_similar", side_effect=[True, False]):
        generate_question(source, mock_llm)

    prompt_initial = mock_llm.generate.call_args_list[0][0][0]
    prompt_rephrase = mock_llm.generate.call_args_list[1][0][0]
    assert prompt_initial != prompt_rephrase


def test_generate_question_fail_safe_after_max_retries():
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "question trop similaire au source"

    source = "la photosynthèse est le processus par lequel les plantes produisent de l'énergie"

    with patch("Doc2Quiz.service.core.is_too_similar", return_value=True):
        with patch("Doc2Quiz.service.core.settings") as mock_settings:
            mock_settings.anti_verbatim_max_retries = 2
            result = generate_question(source, mock_llm)

    assert result is not None
    assert mock_llm.generate.call_count == 3  # 1 initial + 2 retries