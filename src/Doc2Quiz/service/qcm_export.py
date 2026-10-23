from __future__ import annotations

import html
import re
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

QUESTIONS_KEYS = ("questions",)
ENONCE_KEYS = ("enonce", "question", "texte", "text")
REPONSES_KEYS = ("reponses", "answers", "choix")   
OPTIONS_KEYS = ("options",)  
BONNE_REPONSE_KEYS = ("bonne_reponse", "bonne_réponse", "reponse_correcte", "correct_answer", "correct")
FEEDBACKS_KEYS = ("feedbacks", "explications_options")  
EXPLICATION_KEYS = ("explication", "explanation", "justification", "feedback")  
TEXTE_KEYS = ("texte", "text", "reponse", "label")
CORRECT_KEYS = ("correcte", "correct", "est_correcte", "is_correct")
FEEDBACK_KEYS = ("feedback", "explication", "commentaire")


class ExportError(Exception):
    """Erreur de données d'entrée ou fichier généré invalide."""


@dataclass
class Answer:
    text: str
    correct: bool
    feedback: str = ""


@dataclass
class Question:
    text: str
    answers: list[Answer] = field(default_factory=list)


def _pick(d: dict, keys: tuple[str, ...], default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


_LETTER_PREFIX = re.compile(r"^\s*[A-Za-z][\)\.\:\-]\s+")


def _strip_letter_prefixes(options: list[str]) -> list[str]:
    """Retire « A) », « B. »… uniquement si TOUTES les options suivent A, B, C… dans l'ordre."""
    ms = [_LETTER_PREFIX.match(o) for o in options]
    if all(ms) and [m.group().strip()[0].upper() for m in ms] == [chr(65 + i) for i in range(len(options))]:
        return [o[m.end():].strip() for o, m in zip(options, ms)]
    return [o.strip() for o in options]


def _resolve_correct(raw: list[str], clean: list[str], bonne) -> set[int]:
    """bonne_reponse peut être : une lettre (« A », « B) »), le texte de l'option
    (avec ou sans préfixe), un index 0-based, ou une liste de ces valeurs."""
    items = bonne if isinstance(bonne, (list, tuple, set)) else [bonne]
    found: set[int] = set()
    for item in items:
        if isinstance(item, int) and not isinstance(item, bool) and 0 <= item < len(clean):
            found.add(item)
            continue
        s = str(item if item is not None else "").strip()
        key = s.casefold()
        idx = next((i for i, (r, c) in enumerate(zip(raw, clean))
                    if key in (r.strip().casefold(), c.casefold())), None)
        if idx is None:
            m = re.match(r"^([A-Za-z])(?:[\)\.\:\-].*|)$", s, re.S)
            if m and ord(m.group(1).upper()) - 65 < len(clean):
                idx = ord(m.group(1).upper()) - 65
        if idx is None:
            raise ValueError(f"bonne réponse {s!r} introuvable parmi les options")
        found.add(idx)
    return found


def _resolve_feedbacks(rq: dict, raw: list[str], clean: list[str], correct: set[int]) -> list[str]:
    fb = [""] * len(clean)
    per = _pick(rq, FEEDBACKS_KEYS)
    if isinstance(per, (list, tuple)) and len(per) == len(clean):
        fb = [str(x or "").strip() for x in per]
    elif isinstance(per, dict):
        for i, (r, c) in enumerate(zip(raw, clean)):
            for key in (chr(65 + i), chr(97 + i), r.strip(), c, i, str(i)):
                if key in per:
                    fb[i] = str(per[key] or "").strip()
                    break

    expl = str(_pick(rq, EXPLICATION_KEYS, "") or "").strip()
    if expl:
        for i in correct:
            fb[i] = fb[i] or expl
    return fb


def _normalize_question(i: int, rq) -> Question | None:
    """Renvoie None pour les questions non exportables par nature (exercice, cours libre)."""
    if not isinstance(rq, dict):
        raise ExportError(f"Question {i} : format inattendu.")
    if rq.get("type") not in (None, "qcm"):
        return None
    enonce = str(_pick(rq, ENONCE_KEYS, "")).strip()
    if not enonce:
        raise ExportError(f"Question {i} : énoncé vide.")

    detailed = _pick(rq, REPONSES_KEYS)
    if detailed:
        answers = [
            Answer(
                text=str(_pick(ra, TEXTE_KEYS, "")).strip(),
                correct=bool(_pick(ra, CORRECT_KEYS, False)),
                feedback=str(_pick(ra, FEEDBACK_KEYS, "") or "").strip(),
            )
            for ra in detailed
        ]
    else:
        raw = [str(o) for o in (_pick(rq, OPTIONS_KEYS, []) or [])]
        clean = _strip_letter_prefixes(raw)
        try:
            correct = _resolve_correct(raw, clean, _pick(rq, BONNE_REPONSE_KEYS, ""))
        except ValueError as exc:
            raise ExportError(f"Question {i} : {exc}.") from exc
        fbs = _resolve_feedbacks(rq, raw, clean, correct)
        answers = [Answer(c, j in correct, fbs[j]) for j, c in enumerate(clean)]

    if len(answers) < 2:
        raise ExportError(f"Question {i} : au moins 2 réponses requises.")
    if any(not a.text for a in answers):
        raise ExportError(f"Question {i} : réponse vide.")
    if not any(a.correct for a in answers):
        raise ExportError(f"Question {i} : aucune bonne réponse.")
    return Question(enonce, answers)


def _normalize(qcm, skipped: list[str] | None = None) -> list[Question]:
    """Mode strict par défaut (la 1re question invalide lève ExportError).
    Si `skipped` est fourni : les questions invalides sont ignorées et leur motif y est ajouté."""
    raw_questions = _pick(qcm, QUESTIONS_KEYS) if isinstance(qcm, dict) else qcm
    if not raw_questions:
        raise ExportError("Le QCM ne contient aucune question.")

    questions: list[Question] = []
    for i, rq in enumerate(raw_questions, 1):
        try:
            q = _normalize_question(i, rq)
        except ExportError as exc:
            if skipped is None:
                raise
            skipped.append(str(exc))
            continue
        if q is not None:
            questions.append(q)

    if not questions:
        detail = f" ({' '.join(skipped)})" if skipped else ""
        raise ExportError("Aucune question à choix multiples exportable" + detail + ".")
    return questions


def _as_questions(qcm) -> list[Question]:
    """Accepte un QCM brut OU une liste de Question déjà normalisée."""
    if isinstance(qcm, list) and qcm and isinstance(qcm[0], Question):
        return qcm
    return _normalize(qcm)


_XML_ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")


def _clean(text: str) -> str:
    return _XML_ILLEGAL.sub("", text).replace("\r\n", "\n").replace("\r", "\n").strip()


def _fmt_number(x: float) -> str:
    return f"{x:.5f}".rstrip("0").rstrip(".")


def _fractions(q: Question) -> list[float]:
    """Pondérations Moodle : 100/0 si une seule bonne réponse,
    sinon +100/n_ok pour les bonnes et -100/n_ko pour les mauvaises."""
    n_ok = sum(a.correct for a in q.answers)
    n_ko = len(q.answers) - n_ok
    if n_ok == 1:
        return [100.0 if a.correct else 0.0 for a in q.answers]
    return [
        round(100 / n_ok, 5) if a.correct else -round(100 / n_ko, 5)
        for a in q.answers
    ]


# GIFT

_GIFT_SPECIAL = re.compile(r"([\\~=#{}:])")


def gift_escape(text: str) -> str:
    text = _GIFT_SPECIAL.sub(r"\\\1", _clean(text))
    return text.replace("\n", "\\n")


def build_gift(qcm: dict) -> str:
    questions = _as_questions(qcm)
    blocks: list[str] = []
    for i, q in enumerate(questions, 1):
        title = f"Q{i} - {q.text[:50]}"
        lines = [f"::{gift_escape(title)}:: {gift_escape(q.text)} {{"]
        fractions = _fractions(q)
        single = sum(a.correct for a in q.answers) == 1
        for a, frac in zip(q.answers, fractions):
            if single:
                prefix = "=" if a.correct else "~"
            else:
                prefix = f"~%{_fmt_number(frac)}%"
            line = f"{prefix}{gift_escape(a.text)}"
            if a.feedback:
                line += f"#{gift_escape(a.feedback)}"
            lines.append(line)
        lines.append("}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


# XML Moodle (multichoice)

def _html(text: str) -> str:
    """Les champs Moodle en format="html" sont interprétés comme du HTML :
    on échappe donc & < > (puis ElementTree échappe une 2e fois pour le XML)."""
    return html.escape(_clean(text), quote=False).replace("\n", "<br>")


def _text_node(parent: ET.Element, tag: str, text: str, fmt: str | None = "html") -> ET.Element:
    el = ET.SubElement(parent, tag, {"format": fmt} if fmt else {})
    ET.SubElement(el, "text").text = text
    return el


def build_moodle_xml(qcm: dict) -> bytes:
    questions = _as_questions(qcm)
    root = ET.Element("quiz")
    for i, q in enumerate(questions, 1):
        n_ok = sum(a.correct for a in q.answers)
        qe = ET.SubElement(root, "question", {"type": "multichoice"})
        _text_node(qe, "name", _clean(f"Q{i} - {q.text[:50]}"), fmt=None)
        _text_node(qe, "questiontext", _html(q.text))
        _text_node(qe, "generalfeedback", "")
        ET.SubElement(qe, "defaultgrade").text = "1.0000000"
        ET.SubElement(qe, "penalty").text = "0.3333333"
        ET.SubElement(qe, "hidden").text = "0"
        ET.SubElement(qe, "single").text = "true" if n_ok == 1 else "false"
        ET.SubElement(qe, "shuffleanswers").text = "true"
        ET.SubElement(qe, "answernumbering").text = "abc"
        for tag in ("correctfeedback", "partiallycorrectfeedback", "incorrectfeedback"):
            _text_node(qe, tag, "")
        for a, frac in zip(q.answers, _fractions(q)):
            ae = ET.SubElement(qe, "answer", {"fraction": _fmt_number(frac), "format": "html"})
            ET.SubElement(ae, "text").text = _html(a.text)
            _text_node(ae, "feedback", _html(a.feedback))
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


# Validation (fail-safe)

def validate_moodle_xml(data: bytes) -> None:
    """Relit le XML avec le parseur standard + contrôles de structure Moodle.
    Lève ExportError au moindre problème : le fichier ne doit alors PAS être livré."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ExportError(f"XML invalide : {exc}") from exc

    if root.tag != "quiz":
        raise ExportError("Racine XML attendue : <quiz>.")
    questions = root.findall("question")
    if not questions:
        raise ExportError("Aucune <question> dans le XML.")

    for i, q in enumerate(questions, 1):
        if q.get("type") != "multichoice":
            raise ExportError(f"Question {i} : type différent de multichoice.")
        if not (q.findtext("questiontext/text") or "").strip():
            raise ExportError(f"Question {i} : énoncé vide.")
        answers = q.findall("answer")
        if len(answers) < 2:
            raise ExportError(f"Question {i} : moins de 2 réponses.")
        try:
            fractions = [float(a.get("fraction", "")) for a in answers]
        except ValueError as exc:
            raise ExportError(f"Question {i} : fraction non numérique.") from exc
        if abs(sum(f for f in fractions if f > 0) - 100) > 0.01:
            raise ExportError(f"Question {i} : les bonnes réponses ne totalisent pas 100 %.")


# Nom de fichier

_LIGATURES = str.maketrans({"œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE", "ß": "ss", "ø": "o", "Ø": "O"})


def slugify(name: str, max_len: int = 60, default: str = "qcm") -> str:
    s = unicodedata.normalize("NFKD", (name or "").translate(_LIGATURES))
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:max_len].strip("-")
    return s or default


def export_filename(support_name: str, ext: str, today: date | None = None) -> str:
    return f"{slugify(support_name)}_{(today or date.today()).isoformat()}.{ext}"


def support_name_from_file(f) -> str:
    """Nom du support = nom du fichier uploadé (chemin str/Path, objet .name, ou liste), sans extension."""
    if isinstance(f, (list, tuple)):
        f = f[0] if f else None
    if not f:
        return "qcm"
    path = f if isinstance(f, (str, Path)) else getattr(f, "name", None) or str(f)
    return Path(path).stem or "qcm"


# PDF 

PDF_SHOW_ANSWERS = True  


def build_pdf(qcm, title: str = "QCM") -> bytes:
    """QCM -> PDF (A4). Les import reportlab sont locaux : si la bibliothèque manque,
    seul le PDF est indisponible, GIFT et XML continuent de fonctionner."""
    try:
        from io import BytesIO
        from xml.sax.saxutils import escape

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate
    except ImportError as exc:
        raise ExportError("Export PDF indisponible : bibliothèque « reportlab » non installée.") from exc

    def p(text: str) -> str:  
        return escape(_clean(text)).replace("\n", "<br/>")

    base = getSampleStyleSheet()["BodyText"]
    s_title = ParagraphStyle("t", parent=base, fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=6)
    s_sub = ParagraphStyle("s", parent=base, textColor=colors.grey, spaceAfter=14)
    s_q = ParagraphStyle("q", parent=base, fontName="Helvetica-Bold", fontSize=11, leading=14,
                         spaceBefore=10, spaceAfter=4)
    s_opt = ParagraphStyle("o", parent=base, leftIndent=14, leading=14)
    s_ok = ParagraphStyle("ok", parent=s_opt, fontName="Helvetica-Bold", textColor=colors.HexColor("#1B7F3B"))
    s_fb = ParagraphStyle("f", parent=base, leftIndent=28, fontName="Helvetica-Oblique", fontSize=9,
                          leading=12, textColor=colors.HexColor("#555555"))

    questions = _as_questions(qcm)
    story = [Paragraph(p(title) or "QCM", s_title), Paragraph(f"{len(questions)} question(s)", s_sub)]
    for i, q in enumerate(questions, 1):
        block = [Paragraph(f"{i}. {p(q.text)}", s_q)]
        for j, a in enumerate(q.answers):
            letter = chr(65 + j) if j < 26 else str(j + 1)
            show = PDF_SHOW_ANSWERS and a.correct
            label = f"{letter}. {p(a.text)}" + (" &nbsp;(bonne réponse)" if show else "")
            block.append(Paragraph(label, s_ok if show else s_opt))
            if PDF_SHOW_ANSWERS and a.feedback:
                block.append(Paragraph(p(a.feedback), s_fb))
        story.append(KeepTogether(block))

    buf = BytesIO()
    try:
        SimpleDocTemplate(buf, pagesize=A4, title=_clean(title) or "QCM",
                          leftMargin=2 * cm, rightMargin=2 * cm,
                          topMargin=2 * cm, bottomMargin=2 * cm).build(story)
    except Exception as exc:  
        raise ExportError(f"Génération du PDF impossible : {exc}") from exc
    return buf.getvalue()


def validate_pdf(data: bytes) -> None:
    """Fail-safe minimal : un vrai PDF commence par %PDF- et se termine par %%EOF."""
    if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:]:
        raise ExportError("PDF invalide : en-tête ou fin de fichier absent.")


# Orchestration : génération -> validation -> écriture

@dataclass
class ExportResult:
    gift_path: Path | None = None
    xml_path: Path | None = None
    pdf_path: Path | None = None
    errors: dict[str, str] = field(default_factory=dict)  
    warnings: list[str] = field(default_factory=list)     


def export_all(
    qcm,
    support_name: str,
    out_dir: str | Path | None = None,
    today: date | None = None,
    formats: tuple[str, ...] = ("gift", "xml"),
) -> ExportResult:
    result = ExportResult()

    skipped: list[str] = []
    try:
        questions = _normalize(qcm, skipped)
    except ExportError as exc:
        result.errors = {fmt: str(exc) for fmt in formats}
        return result
    result.warnings = [f"{msg} Question ignorée à l'export." for msg in skipped]

    out = Path(out_dir) if out_dir else Path(tempfile.mkdtemp(prefix="qcm_export_"))
    out.mkdir(parents=True, exist_ok=True)

    if "gift" in formats:
        try:
            gift = build_gift(questions)
            if not gift.strip():
                raise ExportError("GIFT vide.")
            path = out / export_filename(support_name, "txt", today)
            path.write_text(gift, encoding="utf-8")
            result.gift_path = path
        except ExportError as exc:
            result.errors["gift"] = str(exc)

    if "xml" in formats:
        try:
            data = build_moodle_xml(questions)
            validate_moodle_xml(data)  
            path = out / export_filename(support_name, "xml", today)
            path.write_bytes(data)
            result.xml_path = path
        except ExportError as exc:
            result.errors["xml"] = str(exc)

    if "pdf" in formats:
        try:
            data = build_pdf(questions, support_name)
            validate_pdf(data)  
            path = out / export_filename(support_name, "pdf", today)
            path.write_bytes(data)
            result.pdf_path = path
        except ExportError as exc:
            result.errors["pdf"] = str(exc)

    return result