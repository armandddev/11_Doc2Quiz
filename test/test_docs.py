"""
Test d'extraction PDF et prompts au LLM via ollama_wrapper.
"""

import logging
import sys
from pathlib import Path
from typing import Dict

import pdfplumber
import pytest

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
DOCUMENTS_DIR = ROOT / "test" / "documents_test"
SRC_DIR = ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

# Import du wrapper Ollama
try:
    from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper
except ImportError as e:
    print(f"❌ Erreur: impossible d'importer ollama_wrapper depuis {SRC_DIR}")
    print(f"   {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Extensions supportées
SUPPORTED_EXTENSIONS = {".pdf"}


# ---------------------------------------------------------------------------
# Extracteurs
# ---------------------------------------------------------------------------

def extract_pdf(path: Path) -> str:
    """Extrait le texte d'un PDF page par page via pdfplumber."""
    with pdfplumber.open(path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages).strip()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_documents() -> list[Path]:
    """Liste tous les fichiers PDF dans documents_test/."""
    if not DOCUMENTS_DIR.exists():
        logger.warning("Dossier %s n'existe pas, création en cours...", DOCUMENTS_DIR)
        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        return []
    
    return sorted(
        p for p in DOCUMENTS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


# ---------------------------------------------------------------------------
# Tests pytest
# ---------------------------------------------------------------------------

def test_documents_dir_exists():
    """Le dossier documents_test/ doit exister."""
    assert DOCUMENTS_DIR.exists(), f"Dossier introuvable: {DOCUMENTS_DIR}"
    logger.info("✅ Dossier documents_test trouvé: %s", DOCUMENTS_DIR)


def test_documents_available():
    """Au moins un PDF doit être disponible dans documents_test/."""
    docs = get_documents()
    assert docs, (
        f"Aucun fichier PDF trouvé dans {DOCUMENTS_DIR}\n"
        f"Ajoute des fichiers .pdf dans {DOCUMENTS_DIR} pour ce test."
    )
    logger.info("✅ %d fichier(s) PDF trouvé(s)", len(docs))
    for doc in docs:
        logger.info("   - %s (%d octets)", doc.name, doc.stat().st_size)


def test_llm_server_reachable():
    """Le serveur Ollama doit être accessible."""
    wrapper = OllamaWrapper()
    is_running = wrapper.is_server_running()
    assert is_running, "❌ Serveur Ollama inaccessible. Vérifie qu'Ollama est lancé."
    logger.info("✅ Serveur Ollama accessible (modèle: %s)", wrapper.default_model)


@pytest.mark.parametrize("doc_path", get_documents())
def test_pdf_extraction(doc_path: Path):
    """Chaque PDF doit être extractible et contenir du texte."""
    try:
        text = extract_pdf(doc_path)
        assert text, f"Extraction vide pour {doc_path.name}"
        logger.info(
            "✅ [PDF] %s — %d caractères extraits, %d lignes",
            doc_path.name,
            len(text),
            len(text.split("\n"))
        )
    except Exception as e:
        pytest.fail(f"Erreur lors de l'extraction de {doc_path.name}: {e}")


@pytest.mark.parametrize("doc_path", get_documents())
def test_llm_prompt_from_pdf(doc_path: Path):
    """
    Pour chaque PDF extrait:
    1. Extraire le texte
    2. Envoyer un prompt au LLM via ollama_wrapper
    3. Vérifier que le LLM retourne une réponse non-vide
    """
    # Extraction
    try:
        text = extract_pdf(doc_path)
    except Exception as e:
        pytest.fail(f"Erreur lors de l'extraction de {doc_path.name}: {e}")
    
    if not text:
        pytest.skip(f"Texte vide pour {doc_path.name}")

    # Préparation du prompt
    preview = text[:2000]  # Premiers 2000 caractères
    prompt = (
        f"Voici le début du document '{doc_path.name}' (format PDF):\n\n"
        f"{preview}\n\n"
        f"En une ou deux phrases, de quoi parle ce document?"
    )

    # Requête au LLM
    wrapper = OllamaWrapper()
    try:
        result = wrapper.generate_text(prompt)
    except Exception as e:
        pytest.fail(f"Erreur lors de l'appel au LLM pour {doc_path.name}: {e}")

    # Vérification
    assert result.response.strip(), f"Réponse vide du LLM pour {doc_path.name}"
    
    response_preview = result.response.strip()[:150]
    logger.info(
        "🤖 [PDF] %s\n   → Réponse: %s...",
        doc_path.name,
        response_preview
    )


# ---------------------------------------------------------------------------
# Exécution directe
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    docs = get_documents()
    
    if not docs:
        logger.error("❌ Aucun fichier PDF trouvé dans %s", DOCUMENTS_DIR)
        logger.info("💡 Ajoute des fichiers .pdf dans ce dossier et réessaie.")
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("🔍 EXTRACTION PDF + PROMPT LLM")
    logger.info("=" * 70)
    logger.info("📁 Dossier: %s", DOCUMENTS_DIR)
    logger.info("📄 Fichiers trouvés: %d\n", len(docs))

    # Initialisation du wrapper
    wrapper = OllamaWrapper()
    logger.info("🔗 URL Ollama: %s", wrapper.base_url)
    logger.info("🤖 Modèle par défaut: %s\n", wrapper.default_model)

    if not wrapper.is_server_running():
        logger.error("❌ Serveur Ollama inaccessible")
        sys.exit(1)
    logger.info("✅ Serveur Ollama accessible\n")

    # Traitement des documents
    results: Dict[str, Dict] = {}
    
    for doc_path in docs:
        logger.info("─" * 70)
        logger.info("📄 Traitement: %s", doc_path.name)
        logger.info("─" * 70)
        
        # Extraction
        try:
            text = extract_pdf(doc_path)
            logger.info("✅ Extraction réussie: %d caractères", len(text))
        except Exception as e:
            logger.error("❌ Erreur extraction: %s", e)
            results[doc_path.name] = {"status": "extraction_failed", "error": str(e)}
            continue

        if not text:
            logger.warning("⚠️  Texte vide après extraction")
            results[doc_path.name] = {"status": "empty_text"}
            continue

        # Prompt au LLM
        preview = text[:2000]
        prompt = (
            f"Voici le début du document '{doc_path.name}' (format PDF):\n\n"
            f"{preview}\n\n"
            f"En une ou deux phrases, de quoi parle ce document?"
        )

        try:
            result = wrapper.generate_text(prompt)
            logger.info("✅ Réponse LLM reçue")
            logger.info("📝 Réponse: %s", result.response.strip())
            results[doc_path.name] = {
                "status": "success",
                "text_length": len(text),
                "response": result.response.strip(),
                "model": result.model,
                "eval_count": result.eval_count,
            }
        except Exception as e:
            logger.error("❌ Erreur LLM: %s", e)
            results[doc_path.name] = {"status": "llm_failed", "error": str(e)}

    # Résumé final
    logger.info("\n" + "=" * 70)
    logger.info("📊 RÉSUMÉ FINAL")
    logger.info("=" * 70)
    
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    logger.info("✅ Succès: %d/%d", success_count, len(results))
    
    for filename, result in results.items():
        if result["status"] == "success":
            logger.info(
                "  ✓ %s (%d chars) → LLM OK",
                filename,
                result.get("text_length", 0)
            )
        else:
            logger.info("  ✗ %s → %s", filename, result["status"])
    
    logger.info("=" * 70)