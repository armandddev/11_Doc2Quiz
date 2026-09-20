# service/core.py
def extraire_notions(file_path: str) -> list[dict]:
    return [{"nom": "Photosynthèse", "resume": "..."}]
from shared.document import extractFromPdf, extractFromMd

def process_uploaded_pdf(file) -> str:
    filepath = file.name
    return extractFromPdf(filepath)

def process_uploaded_md(file) -> str:
    filepath = file.name
    return extractFromMd(filepath)
