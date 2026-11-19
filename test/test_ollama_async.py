import asyncio

import pytest

from Doc2Quiz.ollama_client.ollama_wrapper import (
    OllamaGenerateResult,
    OllamaWrapper,
)


pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    client = OllamaWrapper(timeout_s=600.0, max_retries=1)
    if not client.is_server_running():
        pytest.skip("Serveur Ollama inaccessible")
    return client


def test_generate_texts_async_utilise_ollama_et_conserve_l_ordre(client):
    prompts = [
        "Réponds uniquement par le mot PREMIER.",
        "Réponds uniquement par le mot DEUXIEME.",
        "Réponds uniquement par le mot TROISIEME.",
    ]

    results = asyncio.run(
        client.generate_texts_async(prompts, max_concurrency=2)
    )

    assert len(results) == len(prompts)
    assert all(isinstance(result, OllamaGenerateResult) for result in results)
    assert all(result.response.strip() for result in results)
