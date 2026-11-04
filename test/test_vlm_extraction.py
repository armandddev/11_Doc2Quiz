from unittest.mock import MagicMock
import io
import pymupdf
from PIL import Image

from shared.document.extraction import extractFromPdf, extractFromMd
from Doc2Quiz.service.vlm_service import VLMService


def test_pdf_extraction_injects_vlm_summary(tmp_path):
    # 1. Création d'un document PDF avec texte et image
    pdf_path = str(tmp_path / "test_doc.pdf")
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Introduction sur l'architecture réseau.")

    # Image test
    img = Image.new("RGB", (120, 120), color="blue")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    page.insert_image(pymupdf.Rect(50, 100, 170, 220), stream=img_byte_arr.getvalue())
    doc.save(pdf_path)
    doc.close()

    # 2. Mock du service VLM
    mock_vlm = VLMService()
    mock_vlm.describe_image = MagicMock(
        return_value="Schéma illustrant un réseau local en étoile avec un commutateur central."
    )

    # 3. Extraction
    result = extractFromPdf(pdf_path, vlm_service=mock_vlm)

    # 4. Vérifications DoD
    assert mock_vlm.describe_image.called
    assert "Schéma illustrant un réseau local en étoile" in result["text"]
    assert any("Schéma illustrant un réseau local en étoile" in s.get("text", "") for s in result["sections"])