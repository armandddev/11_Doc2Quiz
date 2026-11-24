from datetime import datetime, timezone
from math import ceil
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
ALL = "tous"
PAGE_SIZE = 20
HISTORY_HEADERS = ["Date", "Support", "Origine", "Questions"]
SOURCE_LABELS = {"generation": "Généré", "import": "Importé"}


def _as_paris(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(PARIS)


def parse_day(value):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Date invalide : « {value} » (format JJ/MM/AAAA).")


def document_choices(generations):
    names = sorted({g.get("document_name") or "" for g in generations} - {""})
    return [("Tous les supports", ALL)] + [(n, n) for n in names]


def filter_generations(generations, document=ALL, date_from="", date_to=""):
    start, end = parse_day(date_from), parse_day(date_to)
    if start and end and start > end:
        raise ValueError("La date de début est après la date de fin.")
    out = []
    for g in generations:
        if document not in (None, "", ALL) and g.get("document_name") != document:
            continue
        d = _as_paris(g.get("created_at"))
        day = d.date() if d else None
        if start and (day is None or day < start):
            continue
        if end and (day is None or day > end):
            continue
        out.append(g)
    return out


def format_row(g):
    d = _as_paris(g.get("created_at"))
    return [
        d.strftime("%d/%m/%Y %H:%M") if d else "",
        g.get("document_name") or "—",
        SOURCE_LABELS.get(g.get("source"), "Généré"),
        g.get("question_count", 0),
    ]


def build_page(generations, page=1):
    total = len(generations)
    pages = max(1, ceil(total / PAGE_SIZE))
    page = max(1, min(page, pages))
    chunk = generations[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]
    rows = [format_row(g) for g in chunk]
    ids = [str(g.get("_id") or g.get("id")) for g in chunk]
    label = f"Page {page}/{pages} — {total} QCM" if total else "Aucun QCM enregistré."
    return rows, ids, page, label, page > 1, page < pages