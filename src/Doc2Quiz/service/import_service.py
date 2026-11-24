import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from service.qcm_parser import QcmImportError, parse_gift, parse_moodle_xml
from storage.generation_storage import SOURCE_IMPORT, save_generation
from shared.logging import get_logger

logger = get_logger("import_service")

MAX_IMPORT_SIZE = 2 * 1024 * 1024        # 2 Mo
GIFT_EXTENSIONS = {".txt", ".gift"}
XML_EXTENSIONS = {".xml"}


@dataclass
class ImportResult:
    generation_id: str
    questions: list[dict] = field(default_factory=list)   # avec "_id" (str)
    warnings: list[str] = field(default_factory=list)


def _resolve_path(file) -> Path:
    """Accepte un chemin (str/Path) ou l'objet fichier renvoyé par gr.File (attribut .name)."""
    if isinstance(file, (list, tuple)):
        file = file[0] if file else None
    if not file:
        raise QcmImportError("Aucun fichier fourni.")
    raw = file if isinstance(file, (str, Path)) else getattr(file, "name", None)
    if not raw:
        raise QcmImportError("Fichier illisible.")
    return Path(raw)


def _decode_text(data: bytes) -> str:
    """GIFT : UTF-8 (avec ou sans BOM), sinon Windows-1252 (exports Moodle anciens)."""
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


async def import_qcm_from_file(user_id: str, file) -> ImportResult:
    """
    Importe un QCM GIFT (.txt/.gift) ou XML Moodle (.xml) dans le profil de user_id.
    Lève QcmImportError avec un message affichable si le fichier est refusé.
    """
    if not user_id:
        raise QcmImportError("Vous devez être connecté pour importer un QCM.")

    path = _resolve_path(file)
    ext = path.suffix.lower()
    if ext not in GIFT_EXTENSIONS | XML_EXTENSIONS:
        raise QcmImportError(
            f"Format « {ext or 'sans extension'} » non supporté : utilisez un fichier "
            "GIFT (.txt, .gift) ou XML Moodle (.xml)."
        )

    if not path.is_file():
        raise QcmImportError("Fichier introuvable.")
    if path.stat().st_size > MAX_IMPORT_SIZE:
        raise QcmImportError("Fichier trop volumineux (2 Mo maximum).")

    data = await asyncio.to_thread(path.read_bytes)

    if ext in XML_EXTENSIONS:
        parsed = parse_moodle_xml(data)
    else:
        parsed = parse_gift(_decode_text(data))

    generation_id, questions = await save_generation(
        user_id=user_id,
        document_name=path.name,
        level="",
        revision="",
        questions=parsed.questions,
        source=SOURCE_IMPORT,
    )
    logger.info(
        "QCM importé : user=%s generation=%s questions=%d ignorées=%d",
        user_id, generation_id, len(questions), len(parsed.warnings),
    )
    return ImportResult(generation_id, questions, parsed.warnings)
