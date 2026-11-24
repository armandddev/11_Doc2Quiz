from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

MAX_OPTIONS = 26  # une lettre par option (A..Z)


class QcmImportError(Exception):
    """Fichier illisible ou ne contenant aucune question importable."""


class _SkipQuestion(Exception):
    """Question non convertible : ignorée avec un avertissement."""


@dataclass
class ParseResult:
    questions: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class _Answer:
    text: str
    correct: bool
    feedback: str = ""

def _build_question(text: str, answers: list[_Answer]) -> dict:
    text = text.strip()
    if not text:
        raise _SkipQuestion("énoncé vide")
    if len(answers) < 2:
        raise _SkipQuestion("moins de 2 réponses")
    if len(answers) > MAX_OPTIONS:
        raise _SkipQuestion(f"plus de {MAX_OPTIONS} réponses")
    if any(not a.text.strip() for a in answers):
        raise _SkipQuestion("réponse vide")

    n_correct = sum(a.correct for a in answers)
    if n_correct == 0:
        raise _SkipQuestion("aucune bonne réponse")
    if n_correct > 1:
        raise _SkipQuestion("plusieurs bonnes réponses (non supporté)")

    letters = [chr(65 + i) for i in range(len(answers))]
    return {
        "question": text,
        "options": [f"{l}. {a.text.strip()}" for l, a in zip(letters, answers)],
        "correct": next(l for l, a in zip(letters, answers) if a.correct),
        "feedbacks": [a.feedback.strip() for a in answers],
        "type": "qcm",
    }


def _label(index: int, text: str) -> str:
    short = " ".join(text.split())
    short = short[:40] + "…" if len(short) > 40 else short
    return f"Question {index}" + (f" (« {short} »)" if short else "")


def _finish(result: ParseResult) -> ParseResult:
    if not result.questions:
        detail = " " + " ".join(result.warnings) if result.warnings else ""
        raise QcmImportError("Aucune question importable dans le fichier." + detail)
    return result


_GIFT_ESCAPES = {"~": "~", "=": "=", "#": "#", "{": "{", "}": "}", ":": ":", "\\": "\\", "n": "\n"}


def _gift_unescape(text: str) -> str:
    out, i = [], 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text) and text[i + 1] in _GIFT_ESCAPES:
            out.append(_GIFT_ESCAPES[text[i + 1]])
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _find_unescaped(text: str, char: str, start: int = 0) -> int:
    """Position du premier `char` non précédé d'un backslash, ou -1."""
    i = start
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text.startswith(char, i):
            return i
        i += 1
    return -1


def _split_unescaped(text: str, seps: str) -> list[str]:
    """Découpe avant chaque séparateur non échappé (le séparateur reste en tête du morceau)."""
    parts, buf, i = [], "", 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text):
            buf += text[i:i + 2]
            i += 2
            continue
        if c in seps:
            if buf.strip():
                parts.append(buf)
            buf = c
        else:
            buf += c
        i += 1
    if buf.strip():
        parts.append(buf)
    return parts


def _strip_gift_format(text: str) -> str:
    """Retire un éventuel préfixe [html] / [moodle] / [plain] / [markdown]."""
    m = re.match(r"^\s*\[(html|moodle|plain|markdown)\]", text, re.I)
    if not m:
        return text
    text = text[m.end():]
    return _html_to_text(text) if m.group(1).lower() == "html" else text


def _split_gift_blocks(text: str) -> list[str]:
    """Une question GIFT = un bloc séparé par au moins une ligne vide.
    Les commentaires // et les lignes $CATEGORY sont ignorés."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("$CATEGORY"):
            continue
        lines.append(line)
    return [b.strip() for b in re.split(r"\n\s*\n", "\n".join(lines)) if b.strip()]


def _parse_gift_answers(body: str) -> list[_Answer]:
    # Le feedback général n'est pas conservé.
    general = _find_unescaped(body, "####")
    if general != -1:
        body = body[:general]
    body = body.strip()

    if not body:
        raise _SkipQuestion("question ouverte / description (non supportée)")
    if body.startswith("#"):
        raise _SkipQuestion("question numérique (non supportée)")
    if _find_unescaped(body, "->") != -1:
        raise _SkipQuestion("question d'appariement (non supportée)")

    # Vrai / Faux : {T}, {TRUE}, {F}, {FALSE},
    tf = re.match(r"^(TRUE|FALSE|T|F)\s*(?=#|$)", body, re.I)
    if tf:
        is_true = tf.group(1).upper() in ("T", "TRUE")
        fbs = [_gift_unescape(p[1:]).strip() for p in _split_unescaped(body[tf.end():], "#")]
        fb_wrong = fbs[0] if len(fbs) > 0 else ""
        fb_right = fbs[1] if len(fbs) > 1 else ""
        return [
            _Answer("Vrai", is_true, fb_right if is_true else fb_wrong),
            _Answer("Faux", not is_true, fb_wrong if is_true else fb_right),
        ]

    raw_answers = _split_unescaped(body, "=~")
    if not raw_answers or raw_answers[0][0] not in "=~":
        raise _SkipQuestion("format de réponses GIFT invalide")
    if all(a[0] == "=" for a in raw_answers):
        raise _SkipQuestion("question à réponse courte (non supportée)")

    answers = []
    for raw in raw_answers:
        prefix, rest = raw[0], raw[1:].strip()
        correct = prefix == "="
        weight = re.match(r"^%(-?\d+(?:\.\d+)?)%", rest)
        if weight:
            correct = float(weight.group(1)) > 0
            rest = rest[weight.end():]
        fb_pos = _find_unescaped(rest, "#")
        text, feedback = (rest[:fb_pos], rest[fb_pos + 1:]) if fb_pos != -1 else (rest, "")
        answers.append(_Answer(_gift_unescape(text).strip(), correct, _gift_unescape(feedback).strip()))
    return answers


def _parse_gift_block(block: str) -> tuple[str, dict]:
    # Titre optionnel ::titre::
    if block.startswith("::"):
        end = _find_unescaped(block, "::", 2)
        if end == -1:
            raise _SkipQuestion("titre ::…:: non fermé")
        block = block[end + 2:].strip()

    open_pos = _find_unescaped(block, "{")
    if open_pos == -1:
        raise _SkipQuestion("bloc de réponses {…} absent")
    close_pos = _find_unescaped(block, "}", open_pos + 1)
    if close_pos == -1:
        raise _SkipQuestion("accolade { non fermée")

    before = block[:open_pos].strip()
    after = block[close_pos + 1:].strip()
    # Format « mot manquant » : texte {réponses} suite du texte
    raw_text = f"{before} _____ {after}" if after else before
    text = _gift_unescape(_strip_gift_format(raw_text))

    answers = _parse_gift_answers(block[open_pos + 1:close_pos])
    return text, _build_question(text, answers)


def parse_gift(content: str) -> ParseResult:
    """Parse un fichier GIFT (texte). Lève QcmImportError si rien n'est importable."""
    if not isinstance(content, str) or not content.strip():
        raise QcmImportError("Le fichier GIFT est vide.")

    result = ParseResult()
    blocks = _split_gift_blocks(content.lstrip("﻿"))
    for i, block in enumerate(blocks, 1):
        try:
            _, question = _parse_gift_block(block)
            result.questions.append(question)
        except _SkipQuestion as exc:
            result.warnings.append(f"{_label(i, block)} ignorée : {exc}.")
    return _finish(result)


_TAG = re.compile(r"<[^>]+>")
_BREAK = re.compile(r"<\s*br\s*/?\s*>|</\s*p\s*>", re.I)


def _html_to_text(value: str) -> str:
    text = _BREAK.sub("\n", value or "")
    text = html.unescape(_TAG.sub("", text))
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def _xml_text(element: ET.Element | None, path: str = "text") -> str:
    if element is None:
        return ""
    raw = element.findtext(path) or ""
    return _html_to_text(raw) if element.get("format", "html") != "plain_text" else raw.strip()


def _parse_xml_answers(q: ET.Element, qtype: str) -> list[_Answer]:
    answers = []
    for a in q.findall("answer"):
        try:
            fraction = float(a.get("fraction", "0"))
        except ValueError:
            raise _SkipQuestion("fraction non numérique")
        text = _xml_text(a)
        if qtype == "truefalse":
            text = {"true": "Vrai", "false": "Faux"}.get(text.lower(), text)
        answers.append(_Answer(text, fraction > 0, _xml_text(a.find("feedback"))))
    return answers


def parse_moodle_xml(content: bytes | str) -> ParseResult:
    """Parse un fichier XML Moodle. Lève QcmImportError si rien n'est importable."""
    if not content or not content.strip():
        raise QcmImportError("Le fichier XML est vide.")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise QcmImportError(f"XML invalide : {exc}") from exc
    if root.tag != "quiz":
        raise QcmImportError("Ce n'est pas un fichier XML Moodle (racine <quiz> attendue).")

    result = ParseResult()
    index = 0
    for q in root.findall("question"):
        qtype = q.get("type", "")
        if qtype == "category":
            continue
        index += 1
        text = _xml_text(q.find("questiontext"))
        try:
            if qtype not in ("multichoice", "truefalse"):
                raise _SkipQuestion(f"type « {qtype or 'inconnu'} » non supporté")
            result.questions.append(_build_question(text, _parse_xml_answers(q, qtype)))
        except _SkipQuestion as exc:
            result.warnings.append(f"{_label(index, text)} ignorée : {exc}.")
    return _finish(result)
