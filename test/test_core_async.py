import time

import pytest

from Doc2Quiz.ollama_client import OllamaWrapper
from Doc2Quiz.service import core


pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    client = OllamaWrapper(timeout_s=600.0, max_retries=1)
    if not client.is_server_running():
        pytest.skip("Serveur Ollama inaccessible")
    return client


def test_generation_qcm_lance_les_sections_en_parallele(
    tmp_path, monkeypatch, client
):
    source = tmp_path / "cours.md"
    source.write_text("cours", encoding="utf-8")
    sections = [
        {
            "title": f"Section {index}",
            "text": (
                f"Cette section présente la notion numéro {index}. "
                "Elle explique son principe et son utilisation."
            ),
        }
        for index in range(1, 5)
    ]
    monkeypatch.setattr(
        core,
        "process_uploaded_md",
        lambda *args, **kwargs: {"sections": sections},
    )

    start = time.perf_counter()
    result = core.generation_qcm(str(source), client)
    elapsed = time.perf_counter() - start

    assert len(result) == len(sections)
    assert [question["section"] for question in result] == sections
    assert all(question["question"] for question in result)
    print(f"\nGénération réelle de {len(result)} questions : {elapsed:.2f}s")
