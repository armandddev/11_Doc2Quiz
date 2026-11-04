import base64
from datetime import datetime, timezone
import os
import pymupdf
import mistune

from .segmentation import segment_text
from .detection import detection_section_displine
from .models import Section
from Doc2Quiz.ollama_client import OllamaWrapper
from Doc2Quiz.service.vlm_service import VLMService


def extractFromMd(file_input, revision: str = "Les deux", vlm_service: VLMService = None) -> dict:
    if vlm_service is None:
        vlm_service = VLMService()

    base_dir = None
    if isinstance(file_input, str):
        base_dir = os.path.dirname(os.path.abspath(file_input))
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

    # Extraction du texte en interceptant les balises images pour le VLM
    text = extractPlainTextFromTreeWithVLM(tree, vlm_service=vlm_service, base_dir=base_dir)

    sections = segment_text(text, titles, llm_client=OllamaWrapper(), revision=revision)
    sections = _detect_sections(sections)

    return {
        "title": titles,
        "text": text.strip(),
        "sections": sections,
        "section_notion_links": [],
        "pages": 1,
        "upload_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def extractPlainTextFromTreeWithVLM(tree: list, vlm_service: VLMService, base_dir: str = None) -> str:
    """Parcourt l'arbre AST Mistune et remplace les nœuds images par leur résumé VLM."""
    text_parts = []
    for node in tree:
        node_text = _process_node_with_vlm(node, vlm_service, base_dir)
        if node_text:
            text_parts.append(node_text)
    return "\n\n".join(text_parts)


def _process_node_with_vlm(node: dict, vlm_service: VLMService, base_dir: str = None) -> str:
    node_type = node.get("type")

    # Détection d'un élément non-textuel (image) dans le Markdown
    if node_type == "image":
        src = node.get("attrs", {}).get("url", "")
        alt = get_node_text(node)
        summary = "[Illustration non textuelle]"

        try:
            # Cas 1 : image en Data URI Base64
            if src.startswith("data:image"):
                base64_data = src.split(",", 1)[1]
                image_bytes = base64.b64decode(base64_data)
                summary = vlm_service.describe_image(image_bytes, context=alt)
            # Cas 2 : fichier local sur le disque
            elif base_dir and os.path.exists(os.path.join(base_dir, src)):
                summary = vlm_service.describe_image(os.path.join(base_dir, src), context=alt)
            elif os.path.exists(src):
                summary = vlm_service.describe_image(src, context=alt)
            else:
                summary = f"[Image non résolue : {alt or src}]"
        except Exception:
            summary = f"[Image : {alt}]"

        return f"\n\n[Élément non textuel analysé par VLM : {summary}]\n\n"

    # Nœuds texte standard
    if "raw" in node:
        return node["raw"]

    text = ""
    for child in node.get("children", []):
        text += _process_node_with_vlm(child, vlm_service, base_dir)
    return text


def extractFromPdf(file: str, revision: str = "Les deux", vlm_service: VLMService = None) -> dict:
    if vlm_service is None:
        vlm_service = VLMService()

    try:
        doc = pymupdf.open(file)
    except Exception:
        raise Exception("File PDF not valid")

    full_text = ""
    count_page = 0
    titles = extractTitles(doc)

    for page in doc:
        count_page += 1
        page_dict = page.get_text("dict")
        page_parts = []

        # Parcourt les blocs de la page dans l'ordre d'apparition
        for block in page_dict.get("blocks", []):
            # 1. Bloc de texte standard
            if block.get("type") == 0:
                block_lines = []
                for line in block.get("lines", []):
                    line_text = "".join(span.get("text", "") for span in line.get("spans", ""))
                    if line_text.strip():
                        block_lines.append(line_text)
                if block_lines:
                    page_parts.append("\n".join(block_lines))

            # 2. Bloc non textuel (image) intercepté avant la clôture du segment
            elif block.get("type") == 1:
                image_bytes = block.get("image")
                width = block.get("width", 0)
                height = block.get("height", 0)

                # Filtrer les puces ou petits artefacts
                if image_bytes and (width >= 80 or height >= 80):
                    summary = vlm_service.describe_image(image_bytes, context=full_text[-300:])
                    page_parts.append(f"\n\n[Élément non textuel analysé par VLM : {summary}]\n\n")

        full_text += "\n".join(page_parts) + "\n\n"

    if len(full_text.strip()) < 20 or doc.page_count < 1:
        doc.close()
        raise Exception("PDF not exploitable")

    doc.close()

    # Le texte contient déjà les résumés d'images injectés aux bons endroits
    sections = segment_text(full_text, titles, llm_client=OllamaWrapper(), revision=revision)
    sections = _detect_sections(sections)

    return {
        "title": titles,
        "text": full_text,
        "sections": sections,
        "section_notion_links": [],
        "pages": count_page,
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


def extractTitles(doc) -> list:
    titles = []
    for i in range(len(doc)):
        page = doc[i]
        page_num = i + 1
        text_blocks = [
            block
            for block in page.get_text("dict")["blocks"] if "lines" in block
            for line in block["lines"]
            for block in line["spans"]
        ]
        for block in text_blocks:
            text = block["text"].strip()
            size = block["size"]
            bold = block["flags"] & 16
            if not text:
                continue
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


def _detect_sections(sections: list) -> list:
    """Détecte la discipline et le content_type pour chaque section."""
    detected_sections = []
    for section in sections:
        try:
            detected = detection_section_displine(Section(**section))
            detected_sections.append(detected.to_dict())
        except Exception:
            detected_sections.append(section)
    return detected_sections