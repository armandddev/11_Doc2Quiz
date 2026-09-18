# service/core.py
def extraire_notions(file_path: str) -> list[dict]:
    """Logique pure, pas de Gradio ici."""
    ...
    return [{"nom": "Photosynthèse", "resume": "..."}]
from shared.document import extractFromPdf, extractFromMd

def process_uploaded_pdf(file) -> str:
    filepath = file.name
    return extractFromPdf(filepath)

def process_uploaded_pdf(file) -> str:
    filepath = file.name
    return extractFromMd(filepath)
