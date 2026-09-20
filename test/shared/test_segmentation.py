from shared.document.extraction import extractFromPdf

def test_pdf_is_segmented():
    document = extractFromPdf("docs/cahier_des_charges.pdf")

    assert document["text"]
    assert document["pages"] > 0
    assert isinstance(document["sections"], list)
    assert len(document["sections"]) > 0

    first_section = document["sections"][0]
    assert "id" in first_section
    assert "title" in first_section
    assert "summary" in first_section
    assert "notion_ids" in first_section
    assert first_section["notion_ids"] is None
    assert len(first_section["summary"]) > 10

    assert document["section_notion_links"] == []

    for section in document["sections"]:
        assert section["id"].startswith("section-")
        assert section["summary"]
