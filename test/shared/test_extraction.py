from shared.pdf import (
    extractFromPdf,
    extractTitles,
    extractFromMd,
    extractTitlesFromTree,
    extractPlainTextFromTree,
    get_node_text,
)
import pymupdf
import pytest
import mistune


# Test that PDF extraction correctly returns text, page count, and titles list
def test_extraction():
    dico = extractFromPdf("docs/cahier_des_charges.pdf")
    assert dico["text"] is not None
    assert len(dico["text"]) > 0
    assert dico["pages"] > 0
    assert isinstance(dico["title"], list)


# Test that extractTitles extracts valid title dictionaries from a PDF document
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


# Test that corrupted/invalid PDF files raise the expected exception
def test_pdf_corrompu(tmp_path):
    bad_pdf = tmp_path / "bad.pdf"
    bad_pdf.write_bytes(b"Not pdf")

    with pytest.raises(Exception, match="File PDF not valid"):
        extractFromPdf(str(bad_pdf))


# Test Markdown extraction when given a file path string
def test_extractFromMd_filepath(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Mon Titre\nCeci est du contenu.", encoding="utf-8")
    result = extractFromMd(str(md_file))
    assert isinstance(result, dict)
    assert result["text"] == "Mon Titre\n\nCeci est du contenu."
    assert result["pages"] == 1
    assert len(result["title"]) == 1
    assert result["title"][0] == {"level": "H1", "text": "Mon Titre", "page": 1}
    assert "upload_timestamp" in result


# Test Markdown extraction when given an open file object/buffer
def test_extractFromMd_file_object(tmp_path):
    md_file = tmp_path / "test_obj.md"
    md_file.write_text("## Sous-titre\nTexte du fichier.", encoding="utf-8")

    with open(md_file, "r", encoding="utf-8") as f:
        result = extractFromMd(f)

    assert result["title"][0]["level"] == "H2"
    assert result["title"][0]["text"] == "Sous-titre"
    assert "Texte du fichier." in result["text"]


# Test that processing an empty Markdown file raises an exception
def test_extractFromMd_empty_file(tmp_path):
    empty_file = tmp_path / "empty.md"
    empty_file.write_text("   \n ", encoding="utf-8")

    with pytest.raises(Exception, match="MD file is empty"):
        extractFromMd(str(empty_file))


# Test extraction of title hierarchy (H1, H2, etc.) directly from AST generated inline
def test_extractTitlesFromTree():
    md_content = "# Titre 1\nUn peu de **texte** en gras.\n## Titre 2\nUne liste :\n- Element 1"
    ast = mistune.create_markdown(renderer=None)(md_content)

    titles = extractTitlesFromTree(ast)
    assert len(titles) == 2
    assert titles[0] == {"level": "H1", "text": "Titre 1", "page": 1}
    assert titles[1] == {"level": "H2", "text": "Titre 2", "page": 1}


# Test that an empty list is returned when the AST contains no headings
def test_extractTitlesFromTree_no_titles():
    markdown_parser = mistune.create_markdown(renderer=None)
    ast = markdown_parser("Seulement un paragraphe sans titre.")
    titles = extractTitlesFromTree(ast)
    assert titles == []


# Test plain text extraction from AST generated inline, ensuring formatting symbols are stripped out
def test_extractPlainTextFromTree():
    md_content = "# Titre 1\nUn peu de **texte** en gras.\n## Titre 2\nUne liste :\n- Element 1"
    ast = mistune.create_markdown(renderer=None)(md_content)

    text = extractPlainTextFromTree(ast)
    assert "Titre 1" in text
    assert "Un peu de texte en gras." in text
    assert "Element 1" in text
    assert "**" not in text
    assert "#" not in text


# Test recursive text extraction on a single leaf node
def test_get_node_text_simple_node():
    node = {"type": "text", "raw": "Texte simple"}
    assert get_node_text(node) == "Texte simple"


# Test recursive text extraction on nested AST nodes (e.g. bold text inside inline elements)
def test_get_node_text_nested_node():
    nested_node = {
        "type": "strong",
        "children": [
            {"type": "text", "raw": "Mot "},
            {"type": "text", "raw": "important"},
        ],
    }
    assert get_node_text(nested_node) == "Mot important"