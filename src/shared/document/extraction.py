import pymupdf
from datetime import datetime, timezone
import mistune

from .segmentation import segment_text

def extractFromMd(file_input) -> dict:
    if isinstance(file_input, str):
        with open(file_input, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        raw_text = file_input.read()
        if isinstance(raw_text, bytes):
            raw_text = raw_text.decode("utf-8")
    if not raw_text.strip():
        raise Exception("MD file is empty")
    markdown_parser = mistune.create_markdown(renderer=None)
    tree = markdown_parser(raw_text)
    titles = extractTitlesFromTree(tree)
    text = extractPlainTextFromTree(tree)
    sections = segment_text(text, titles)

    return {
        "title": titles,
        "text": text.strip(),
        "sections": sections,
        "section_notion_links": [],
        "pages": 1,
        "upload_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
def extractTitlesFromTree(tree: list) -> list:
    titles = []
    for node in tree:
        if node.get("type") == "heading":
            level = f"H{node.get('attrs', {}).get('level', 1)}"
            clean_title = get_node_text(node).strip()
            if clean_title:
                titles.append({"level": level, "text": clean_title, "page": 1})
    return titles

def extractPlainTextFromTree(tree: list) -> str:
    text_parts = []
    for node in tree:
        node_text = get_node_text(node)
        if node_text:
            text_parts.append(node_text)
    return "\n\n".join(text_parts)

def extractTitlesFromMd(md_text: str) -> list:
    titles = []
    markdown_parser = mistune.create_markdown(renderer=None)
    tree = markdown_parser(md_text)
    for node in tree:
        if node.get("type") == "heading":
            level = f"H{node.get('attrs', {}).get('level', 1)}"
            raw_text = ""
            for child in node.get("children", []):
                if "raw" in child:
                    raw_text += child["raw"]
            clean_text = raw_text.strip()
            if clean_text:
                titles.append(
                    {
                        "level": level,
                        "text": clean_text,
                        "page": 1,
                    }
                )

    return titles

def get_node_text(node: dict) -> str:
    if "raw" in node:
        return node["raw"]
    text = ""
    for child in node.get("children", []):
        text += get_node_text(child)
    return text

def extractFromPdf(file: str) -> dict:
    # Open file
    try:
        doc = pymupdf.open(file)
    except Exception:
        raise Exception("File PDF not valid")
    full_text = ""
    count_page = 0
    titles = extractTitles(doc)
    # Extrait le texte de la page et l'ajoute au résultat
    for page in doc:
        count_page += 1
        full_text += page.get_text()
    
    # Détection PDF scanné
    if len(full_text.strip()) < 20 or doc.page_count < 1:
        doc.close()
        raise Exception("PDF not exploitable")
    
    doc.close()
    sections = segment_text(full_text, titles)
    return {
        "title": titles,
        "text": full_text,
        "sections": sections,
        "section_notion_links": [],
        "pages": count_page,
        "upload_timestamp": datetime.now(timezone.utc).isoformat(),
    }

def extractTitles(doc) -> list:
    titles = []
    for i in range(len(doc)):
        page = doc[i]
        page_num = i + 1
        # Divide the doc in block
        text_blocks = [
            block
            for block in page.get_text("dict")["blocks"] if "lines" in block
            for line in block["lines"]
            for block in line["spans"]
        ]
        # Analyse each block
        for block in text_blocks:
            text = block["text"].strip()
            size = block["size"]
            bold = block["flags"] & 16
            if not text:
                continue
            # Class with the size
            if size >= 20:
                level = "H1"
            elif size >= 16:
                level = "H2"
            elif bold:
                level = "H3"
            else:
                continue
            titles.append({"level": level, "text": text, "page": page_num})
    return titles