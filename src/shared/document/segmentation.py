import json
from .models import Section
from .summary import summarize_text


def segment_text(text: str, titles: list[dict], summary_generator=None, llm_client=None) -> list[dict]:
    if not text.strip():
        return []

    if llm_client is not None:
        sections = _segment_with_llm(text, llm_client, summary_generator)
        if sections:
            return sections

    return []


def _segment_with_llm(text: str, llm_client, summary_generator) -> list[dict]:
    CHUNK_SIZE = 6000
    OVERLAP    = 200

    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + CHUNK_SIZE])
        i += CHUNK_SIZE - OVERLAP

    all_items = []
    for chunk in chunks:
        prompt = (
            "Tu es un enseignant. Découpe ce texte de cours en sections fines.\n"
            "Chaque concept, chaque notion, chaque point numéroté doit être une section séparée.\n"
            "Une page peut contenir plusieurs sections.\n"
            "Réponds UNIQUEMENT avec un tableau JSON, sans markdown :\n"
            '[{"titre": "...", "contenu": "..."}]\n\n'
            "Règles :\n"
            "- Une section = un seul concept ou notion\n"
            "- Le contenu doit être le texte original, pas un résumé\n"
            "- Minimum 3 mots par section\n\n"
            f"{chunk}"
        )
        try:
            res = llm_client.generate_text(prompt)
            raw = res.response if hasattr(res, "response") else str(res)

            start = raw.find("[")
            if start == -1:
                continue
            fragment = raw[start:].rstrip()
            if not fragment.endswith("]"):
                last = fragment.rfind("},")
                fragment = (fragment[:last + 1] if last != -1 else fragment) + "]"
            items = json.loads(fragment)
            all_items.extend(items)
        except Exception:
            continue

    sections = []
    for idx, item in enumerate(all_items, start=1):
        contenu = item.get("contenu", "").strip()
        if not contenu:
            continue
        sections.append(_make_section(
            idx, item.get("titre") or f"Section {idx}",
            None, contenu, summary_generator, [], []
        ))
    return sections


def _make_section(index, title, level, text, summary_generator, notion_ids, pages) -> dict:
    section = Section(
        id=f"section-{index:03d}",
        title=title,
        level=level,
        text=text,
        summary=summarize_text(text, summary_generator),
        notion_ids=notion_ids,
        pages=pages,
    )
    return section.to_dict()