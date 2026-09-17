"""
test_ollama_wrapper.py
======================
Tests unitaires pour OllamaWrapper (mock — pas de serveur requis).

    pytest test_ollama_wrapper.py -v

Tests d'intégration (serveur IUT requis) :
    pytest test_ollama_wrapper.py -v --run-integration
"""
from __future__ import annotations

import base64
import io
import json
import urllib.error
from unittest.mock import MagicMock, patch
import pytest

from Doc2Quiz.ollama_client.ollama_wrapper import (
    OllamaWrapper, OllamaConnectionError, OllamaHTTPError,
    OllamaResponseError, OllamaGenerateResult, OllamaChatResult,
    OllamaChatMessage, OllamaStreamChunk,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
)

MODEL = "gemma4:26b"


def _resp(payload: dict) -> MagicMock:
    """Simule un urllib response renvoyant du JSON."""
    mock = MagicMock()
    mock.read.return_value = json.dumps(payload).encode()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    return mock


def _http_err(code: int, msg: str = "") -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x", code, msg, None, io.BytesIO(msg.encode()))  # type: ignore


def _url_err() -> urllib.error.URLError:
    return urllib.error.URLError("Connection refused")


def _ndjson_resp(chunks: list[dict]) -> MagicMock:
    """Simule une réponse NDJSON streaming."""
    lines = [json.dumps(c).encode() + b"\n" for c in chunks]
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.__iter__ = lambda s: iter(lines)
    return mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return OllamaWrapper(max_retries=1, retry_backoff_s=0.0)


# ---------------------------------------------------------------------------
# Marqueur intégration
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption("--run-integration", action="store_true", default=False)


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: nécessite le serveur Ollama IUT")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        skip = pytest.mark.skip(reason="Passer --run-integration pour activer")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)


# ===========================================================================
# 1. is_server_running
# ===========================================================================

class TestIsServerRunning:
    @patch("urllib.request.urlopen")
    def test_true_quand_version_ok(self, mock, client):
        mock.return_value = _resp({"version": "0.33.3"})
        assert client.is_server_running() is True

    @patch("urllib.request.urlopen", side_effect=_url_err())
    def test_false_quand_connexion_impossible(self, _, client):
        assert client.is_server_running() is False


# ===========================================================================
# 2. generate_text
# ===========================================================================

GENERATE_OK = {
    "response": "L'IA c'est bien.",
    "model": MODEL,
    "done": True,
    "total_duration": 1_000_000_000,
    "load_duration": 50_000,
    "prompt_eval_count": 8,
    "eval_count": 12,
}


class TestGenerateText:
    @patch("urllib.request.urlopen")
    def test_retourne_un_result(self, mock, client):
        mock.return_value = _resp(GENERATE_OK)
        r = client.generate_text(model=MODEL, prompt="Qu'est-ce que l'IA ?")
        assert isinstance(r, OllamaGenerateResult)
        assert r.response == "L'IA c'est bien."
        assert r.done is True

    @patch("urllib.request.urlopen")
    def test_stream_false_dans_le_body(self, mock, client):
        mock.return_value = _resp(GENERATE_OK)
        client.generate_text(model=MODEL, prompt="test")
        body = json.loads(mock.call_args[0][0].data.decode())
        assert body["stream"] is False

    @patch("urllib.request.urlopen")
    def test_system_transmis(self, mock, client):
        mock.return_value = _resp(GENERATE_OK)
        client.generate_text(model=MODEL, prompt="test", system="Tu es un assistant.")
        body = json.loads(mock.call_args[0][0].data.decode())
        assert body["system"] == "Tu es un assistant."

    @patch("urllib.request.urlopen")
    def test_options_transmises(self, mock, client):
        mock.return_value = _resp(GENERATE_OK)
        client.generate_text(model=MODEL, prompt="test", options={"temperature": 0.5})
        body = json.loads(mock.call_args[0][0].data.decode())
        assert body["options"] == {"temperature": 0.5}

    @patch("urllib.request.urlopen")
    def test_champ_response_manquant_leve_erreur(self, mock, client):
        mock.return_value = _resp({"done": True})
        with pytest.raises(OllamaResponseError):
            client.generate_text(model=MODEL, prompt="test")

    @patch("urllib.request.urlopen", side_effect=_http_err(404, '{"error":"model not found"}'))
    def test_404_leve_http_error(self, _, client):
        with pytest.raises(OllamaHTTPError) as exc:
            client.generate_text(model="inconnu", prompt="test")
        assert exc.value.status == 404


# ===========================================================================
# 3. generate_stream
# ===========================================================================

class TestGenerateStream:
    @patch("urllib.request.urlopen")
    def test_yield_des_chunks(self, mock, client):
        mock.return_value = _ndjson_resp([
            {"response": "Bon",  "done": False},
            {"response": "jour", "done": False},
            {"response": "",     "done": True},
        ])
        chunks = list(client.generate_stream(model=MODEL, prompt="test"))
        assert all(isinstance(c, OllamaStreamChunk) for c in chunks)
        assert "".join(c.token for c in chunks) == "Bonjour"
        assert chunks[-1].done is True


# ===========================================================================
# 4. generate_with_image
# ===========================================================================

class TestGenerateWithImage:
    @patch("urllib.request.urlopen")
    def test_image_bytes_encodee_en_base64(self, mock, client):
        mock.return_value = _resp({**GENERATE_OK, "response": "Je vois un pixel."})
        client.generate_with_image(model="qwen3-vl:8b", prompt="Que vois-tu ?", image=TINY_PNG)
        body = json.loads(mock.call_args[0][0].data.decode())
        assert body["images"] == [base64.b64encode(TINY_PNG).decode("ascii")]

    @patch("urllib.request.urlopen")
    def test_image_depuis_fichier(self, mock, client, tmp_path):
        f = tmp_path / "img.png"
        f.write_bytes(TINY_PNG)
        mock.return_value = _resp({**GENERATE_OK, "response": "Une image."})
        r = client.generate_with_image(model="qwen3-vl:8b", prompt="test", image=f)
        assert isinstance(r, OllamaGenerateResult)

    def test_type_invalide_leve_erreur(self, client):
        with pytest.raises(TypeError):
            client.generate_with_image(model="qwen3-vl:8b", prompt="test", image=42)  # type: ignore


# ===========================================================================
# 5. chat
# ===========================================================================

CHAT_OK = {
    "message": {"role": "assistant", "content": "Bonjour !"},
    "model": MODEL,
    "done": True,
    "total_duration": 500_000_000,
    "eval_count": 10,
}


class TestChat:
    @patch("urllib.request.urlopen")
    def test_retourne_un_result(self, mock, client):
        mock.return_value = _resp(CHAT_OK)
        r = client.chat(
            model=MODEL,
            messages=[OllamaChatMessage(role="user", content="Bonjour")],
        )
        assert isinstance(r, OllamaChatResult)
        assert r.message.role == "assistant"
        assert r.message.content == "Bonjour !"

    @patch("urllib.request.urlopen")
    def test_messages_serialises(self, mock, client):
        mock.return_value = _resp(CHAT_OK)
        client.chat(
            model=MODEL,
            messages=[
                OllamaChatMessage(role="system", content="Tu es un assistant."),
                OllamaChatMessage(role="user",   content="Salut"),
            ],
        )
        body = json.loads(mock.call_args[0][0].data.decode())
        assert body["messages"][0] == {"role": "system", "content": "Tu es un assistant."}
        assert body["stream"] is False

    @patch("urllib.request.urlopen")
    def test_champ_message_manquant_leve_erreur(self, mock, client):
        mock.return_value = _resp({"done": True})
        with pytest.raises(OllamaResponseError):
            client.chat(model=MODEL, messages=[OllamaChatMessage(role="user", content="test")])


# ===========================================================================
# 6. embed
# ===========================================================================

class TestEmbed:
    @patch("urllib.request.urlopen")
    def test_format_embedding(self, mock, client):
        mock.return_value = _resp({"embedding": [0.1, 0.2, 0.3]})
        assert client.embed(model="qwen3-embedding:0.6b", text="bonjour") == pytest.approx([0.1, 0.2, 0.3])

    @patch("urllib.request.urlopen")
    def test_format_embeddings_nested(self, mock, client):
        mock.return_value = _resp({"embeddings": [[0.4, 0.5]]})
        assert client.embed(model="qwen3-embedding:0.6b", text="monde") == pytest.approx([0.4, 0.5])

    @patch("urllib.request.urlopen")
    def test_retourne_des_floats(self, mock, client):
        mock.return_value = _resp({"embedding": [1, 2, 3]})
        result = client.embed(model="qwen3-embedding:0.6b", text="test")
        assert all(isinstance(x, float) for x in result)

    @patch("urllib.request.urlopen")
    def test_format_inconnu_leve_erreur(self, mock, client):
        mock.return_value = _resp({"oops": "wrong"})
        with pytest.raises(OllamaResponseError):
            client.embed(model="qwen3-embedding:0.6b", text="test")


# ===========================================================================
# 7. Retry
# ===========================================================================

class TestRetry:
    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_3_tentatives_puis_erreur(self, mock, mock_sleep):
        mock.side_effect = _url_err()
        c = OllamaWrapper(max_retries=3, retry_backoff_s=0.01)
        with pytest.raises(OllamaConnectionError):
            c.generate_text(model=MODEL, prompt="test")
        assert mock.call_count == 3

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_succes_au_2e_essai(self, mock, mock_sleep):
        mock.side_effect = [_url_err(), _resp(GENERATE_OK)]
        c = OllamaWrapper(max_retries=3, retry_backoff_s=0.0)
        r = c.generate_text(model=MODEL, prompt="test")
        assert r.response == "L'IA c'est bien."
        assert mock.call_count == 2

    @patch("urllib.request.urlopen")
    def test_http_error_pas_retente(self, mock):
        mock.side_effect = _http_err(500, "Internal Server Error")
        c = OllamaWrapper(max_retries=3)
        with pytest.raises(OllamaHTTPError):
            c.generate_text(model=MODEL, prompt="test")
        assert mock.call_count == 1   # 1 seul appel, pas de retry


# ===========================================================================
# 8. Tests d'intégration (serveur IUT requis)
# ===========================================================================

@pytest.mark.integration
class TestIntegration:
    """pytest test_ollama_wrapper.py -v --run-integration"""

    @pytest.fixture
    def real(self):
        return OllamaWrapper(timeout_s=120.0, max_retries=2)

    @pytest.fixture(autouse=True)
    def check(self, real):
        if not real.is_server_running():
            pytest.skip("Serveur IUT inaccessible")

    def test_serveur_accessible(self, real):
        assert real.is_server_running() is True

    def test_generate_text(self, real):
        r = real.generate_text(
            model=MODEL,
            prompt="Réponds uniquement par le chiffre 42.",
            options={"temperature": 0.0, "num_predict": 100, "think": False},
        )
        assert isinstance(r.response, str) and len(r.response) > 0

    def test_chat(self, real):
        r = real.chat(
            model=MODEL,
            messages=[OllamaChatMessage(role="user", content="Dis juste OK.")],
            options={"temperature": 0.0, "num_predict": 5},
        )
        assert isinstance(r.message.content, str)

    def test_stream(self, real):
        chunks = list(real.generate_stream(
            model=MODEL,
            prompt="Dis bonjour.",
            options={"temperature": 0.0, "num_predict": 5},
        ))
        assert len(chunks) > 0
        assert chunks[-1].done is True

    def test_embed(self, real):
        v = real.embed(model="qwen3-embedding:0.6b", text="intelligence artificielle")
        assert isinstance(v, list) and len(v) > 0
        assert all(isinstance(x, float) for x in v)