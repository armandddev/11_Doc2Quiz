from shared.pdf import extractFromPdf, extractTitles
import pymupdf
import pytest

def test_extraction():
    dico = extractFromPdf("docs/cahier_des_charges.pdf")
    assert dico["text"] is not None
    assert len(dico["text"]) > 0
    assert dico["pages"] > 0
    assert isinstance(dico["title"], list)


def test_extractTitles():
    doc = pymupdf.open("docs/cahier_des_charges.pdf")
    try:
        titles = extractTitles(doc)
        assert len(titles) > 0
        assert "level" in titles[0]
        assert "text" in titles[0]
        assert "page" in titles[0]
    finally:
        doc.close()


def test_pdf_corrompu(tmp_path):
    bad_pdf = tmp_path / "bad.pdf"
    bad_pdf.write_bytes(b"Not pdf")

    with pytest.raises(Exception, match="File PDF not valid"):
        extractFromPdf(str(bad_pdf))