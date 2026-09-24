from Doc2Quiz.service.anti_verbatim import is_too_similar
from Doc2Quiz.config import settings
from shared.logging import get_logger
from shared.document import extractFromPdf, extractFromMd

logger = get_logger("core")

def extraire_notions(file_path: str) -> list[dict]:
    return [{"nom": "Photosynthèse", "resume": "..."}]

def process_uploaded_pdf(file) -> str:
    filepath = file.name
    return extractFromPdf(filepath)

def process_uploaded_md(file) -> str:
    filepath = file.name
    return extractFromMd(filepath)

def generate_question(source_text: str, llm_client) -> str:
    prompt_initial = (
        f"Génère une question de compréhension sur ce texte :\n{source_text}"
    )
    prompt_rephrase = (
        f"Ta question précédente était trop proche du texte source mot pour mot. "
        f"Reformule-la avec des mots et une structure de phrase complètement différents.\n"
        f"Texte source : {source_text}"
    )

    question = None
    for attempt in range(settings.anti_verbatim_max_retries + 1):
        prompt = prompt_initial if attempt == 0 else prompt_rephrase
        question = llm_client.generate(prompt)

        if not is_too_similar(question, source_text):
            logger.info("Question acceptée à la tentative %d", attempt + 1)
            return question

        logger.warning("Tentative %d rejetée — trop similaire au source", attempt + 1)

    logger.error(
        "Échec anti-verbatim après %d tentatives — question retournée telle quelle",
        settings.anti_verbatim_max_retries + 1
    )
    return question
