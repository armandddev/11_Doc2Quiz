from __future__ import annotations

import base64
import pytest

from Doc2Quiz.ollama_client.ollama_wrapper import (
    OllamaWrapper,
    OllamaGenerateResult,
    OllamaChatResult,
    OllamaChatMessage,
    OllamaStreamChunk,
    _MODEL_VLM,
    _MODEL_EMBED,
)

# ---------------------------------------------------------------------------
# Image de test (1x1 pixel PNG)
# ---------------------------------------------------------------------------

TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    """Instance OllamaWrapper — URL et modèles depuis le .env."""
    return OllamaWrapper(timeout_s=120.0, max_retries=2)


@pytest.fixture(autouse=True)
def skip_if_unreachable(client):
    """Skippe tous les tests si le serveur IUT est inaccessible."""
    if not client.is_server_running():
        pytest.skip("Serveur Ollama IUT inaccessible — vérifier OLLAMA_BASE_URL dans le .env")


# ===========================================================================
# 1. Santé serveur
# ===========================================================================

class TestServeur:
    def test_serveur_accessible(self, client):
        assert client.is_server_running() is True


# ===========================================================================
# 2. generate_text
# ===========================================================================

class TestGenerateText:
    def test_retourne_un_result(self, client):
        r = client.generate_text(
            prompt="Réponds uniquement par le chiffre 42.",
            options={"temperature": 0.0, "num_predict": 20},
        )
        assert isinstance(r, OllamaGenerateResult)
        assert isinstance(r.response, str)
        assert len(r.response) > 0

    def test_avec_system_prompt(self, client):
        r = client.generate_text(
            prompt="Qui es-tu ?",
            system="Tu es un assistant pédagogique.",
            options={"temperature": 0.0, "num_predict": 30},
        )
        assert isinstance(r.response, str)
        assert len(r.response) > 0

    def test_champs_metadonnees(self, client):
        r = client.generate_text(
            prompt="Dis bonjour.",
            options={"temperature": 0.0, "num_predict": 10},
        )
        assert r.done is True
        assert r.model is not None
        assert r.eval_count is not None and r.eval_count > 0


# ===========================================================================
# 3. generate_stream
# ===========================================================================

class TestGenerateStream:
    def test_yield_des_chunks(self, client):
        chunks = list(client.generate_stream(
            prompt="Dis bonjour.",
            options={"temperature": 0.0, "num_predict": 10},
        ))
        assert len(chunks) > 0
        assert all(isinstance(c, OllamaStreamChunk) for c in chunks)

    def test_dernier_chunk_done(self, client):
        chunks = list(client.generate_stream(
            prompt="Dis OK.",
            options={"temperature": 0.0, "num_predict": 5},
        ))
        assert chunks[-1].done is True

    def test_tokens_forment_une_reponse(self, client):
        chunks = list(client.generate_stream(
            prompt="Dis uniquement le mot BONJOUR en majuscules.",
            options={"temperature": 0.0, "num_predict": 10},
        ))
        full = "".join(c.token for c in chunks)
        assert len(full) > 0


# ===========================================================================
# 4. generate_with_image
# ===========================================================================

class TestGenerateWithImage:
    def test_image_bytes(self, client):
        r = client.generate_with_image(
            prompt="Que vois-tu sur cette image ? Réponds en une phrase.",
            image=TINY_PNG,
            model=_MODEL_VLM,
            options={"temperature": 0.0, "num_predict": 30},
        )
        assert isinstance(r, OllamaGenerateResult)
        assert len(r.response) > 0

    def test_image_depuis_fichier(self, client, tmp_path):
        f = tmp_path / "img.png"
        f.write_bytes(TINY_PNG)
        r = client.generate_with_image(
            prompt="Décris cette image en une phrase.",
            image=f,
            model=_MODEL_VLM,
            options={"temperature": 0.0, "num_predict": 30},
        )
        assert isinstance(r, OllamaGenerateResult)
        assert len(r.response) > 0


# ===========================================================================
# 5. chat
# ===========================================================================

class TestChat:
    def test_reponse_assistant(self, client):
        r = client.chat(
            messages=[OllamaChatMessage(role="user", content="Dis uniquement OK.")],
            options={"temperature": 0.0, "num_predict": 5},
        )
        assert isinstance(r, OllamaChatResult)
        assert r.message.role == "assistant"
        assert len(r.message.content) > 0

    def test_conversation_multi_tours(self, client):
        r = client.chat(
            messages=[
                OllamaChatMessage(role="system",    content="Tu es un assistant pédagogique."),
                OllamaChatMessage(role="user",      content="Bonjour."),
                OllamaChatMessage(role="assistant", content="Bonjour ! Comment puis-je aider ?"),
                OllamaChatMessage(role="user",      content="Dis uniquement MERCI."),
            ],
            options={"temperature": 0.0, "num_predict": 10},
        )
        assert isinstance(r.message.content, str)
        assert len(r.message.content) > 0

    def test_champs_metadonnees(self, client):
        r = client.chat(
            messages=[OllamaChatMessage(role="user", content="Dis OK.")],
            options={"temperature": 0.0, "num_predict": 5},
        )
        assert r.done is True
        assert r.model is not None


# ===========================================================================
# 6. embed
# ===========================================================================

class TestEmbed:
    def test_retourne_une_liste_de_floats(self, client):
        v = client.embed(text="intelligence artificielle", model=_MODEL_EMBED)
        assert isinstance(v, list)
        assert len(v) > 0
        assert all(isinstance(x, float) for x in v)

    def test_vecteurs_differents_pour_textes_differents(self, client):
        v1 = client.embed(text="photosynthèse",        model=_MODEL_EMBED)
        v2 = client.embed(text="intégrale de Riemann", model=_MODEL_EMBED)
        assert v1 != v2

    def test_meme_texte_meme_vecteur(self, client):
        v1 = client.embed(text="bonjour", model=_MODEL_EMBED)
        v2 = client.embed(text="bonjour", model=_MODEL_EMBED)
        assert v1 == v2