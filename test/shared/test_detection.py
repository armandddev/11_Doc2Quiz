import pytest
from shared.document.extraction import extractFromPdf

def test_detection_section() :
    document = extractFromPdf("docs/cahier_des_charges.pdf")
    for section in document["sections"]:
        assert section["discipline"]
        assert section["content_type"]
