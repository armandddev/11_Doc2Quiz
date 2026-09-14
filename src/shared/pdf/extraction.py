import pymupdf
from datetime import datetime, timezone

def extractFromPdf(file: str) -> str:
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
    return {
        "title" : titles,
        "text" : full_text,
        "pages" : count_page,
        "upload_timestamp": datetime.now(timezone.utc).isoformat()
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