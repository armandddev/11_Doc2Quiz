from __future__ import annotations

import json
from shared.logging import get_logger
from typing import Any

logger = get_logger("segmentation")
_CHUNK_SIZE    = 3000
_CHUNK_OVERLAP = 100
MAX_RETRIES    = 3

_SYSTEM_PROMPTS = {
    "Questions de cours": (
        "Tu es un assistant pédagogique. "
        "Ton rôle est de segmenter un texte en sections de cours théoriques "
        "(définitions, concepts, mécanismes). "
        "Ignore les exercices, calculs et mises en application."
    ),
    "Exercices": (
        "Tu es un assistant pédagogique. "
        "Ton rôle est de segmenter un texte en sections d'exercices pratiques "
        "(calculs, démarches, cas concrets, applications numériques). "
        "Ignore les parties purement théoriques."
    ),
    "Les deux": (
        "Tu es un assistant pédagogique. "
        "Ton rôle est de segmenter un texte en sections exploitables, "
        "qu'elles soient théoriques ou pratiques."
    ),
}

_PROMPT_FOCUS = {
    "Questions de cours": "notions de cours théoriques (définitions, propriétés, concepts)",
    "Exercices":          "exercices pratiques et applications numériques",
    "Les deux":           "notions de cours ET exercices pratiques",
}


def _build_prompt(chunk: str, titles: list, revision: str) -> str:
    focus = _PROMPT_FOCUS.get(revision, _PROMPT_FOCUS["Les deux"])
    titles_str = ", ".join(t.get("text", "") for t in titles[:10]) if titles else "aucun"

    return (
        f"Voici un extrait de document universitaire.\n"
        f"Titres détectés : {titles_str}\n\n"
        f"Texte :\n{chunk}\n\n"
        f"Identifie les sections portant sur {focus}.\n"
        f"Pour chaque section, retourne UNIQUEMENT son titre court.\n"
        f"Retourne UNIQUEMENT un tableau JSON de strings, sans markdown :\n"
        f'["Titre section 1", "Titre section 2", ...]'
    )


def _chunk_text(text: str) -> list[str]:
    """Découpe le texte en chunks avec chevauchement."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - _CHUNK_OVERLAP
        if start >= len(text):
            break
    return chunks


def _segment_with_llm(
    chunk: str, titles: list, llm_client: Any, chunk_idx: int, revision: str = "Les deux"
) -> list[dict]:
    system_prompt = _SYSTEM_PROMPTS.get(revision, _SYSTEM_PROMPTS["Les deux"])
    prompt = _build_prompt(chunk, titles, revision)
    options = {"num_ctx": 8192, "num_predict": -1}

    for attempt in range(MAX_RETRIES):
        raw = ""
        try:
            res = llm_client.generate_text(prompt, system=system_prompt, options=options)
            raw = res.response if hasattr(res, "response") else str(res)
        except Exception as exc:
            logger.warning("Erreur LLM chunk %d (tentative %d/%d) : %s",
                           chunk_idx, attempt + 1, MAX_RETRIES, exc)
            continue

        if raw.strip().lower() == "inutile":
            logger.info("Chunk %d ignoré (contenu non exploitable)", chunk_idx)
            return []

        if not raw.strip():
            logger.warning("Réponse vide chunk %d (tentative %d/%d), retry...",
                           chunk_idx, attempt + 1, MAX_RETRIES)
            continue

        section_titles = _parse_titles(raw, chunk_idx)
        if section_titles is not None:
            sections = _split_chunk_by_titles(chunk, section_titles, chunk_idx)
            return sections

        logger.warning("JSON invalide chunk %d (tentative %d/%d) : %r",
                       chunk_idx, attempt + 1, MAX_RETRIES, raw[:150])

    logger.error("Échec segmentation chunk %d après %d tentatives — section brute conservée",
                 chunk_idx, MAX_RETRIES)
    return [{"title": f"Section {chunk_idx + 1}", "text": chunk}]


def _parse_titles(raw: str, chunk_idx: int) -> list[str] | None:
    """Parse la liste de titres retournée par le LLM."""
    text = raw.strip()
    if text.startswith("```"):
        lines = [l for l in text.splitlines() if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Cherche le tableau JSON
    start = text.find("[")
    end   = text.rfind("]") + 1
    if start == -1 or end <= start:
        return None

    try:
        parsed = json.loads(text[start:end])
        if isinstance(parsed, list) and all(isinstance(t, str) for t in parsed):
            return [t.strip() for t in parsed if t.strip()]
    except json.JSONDecodeError:
        pass
    return None


def _split_chunk_by_titles(chunk: str, section_titles: list[str], chunk_idx: int) -> list[dict]:
    """
    Découpe le chunk en sections en cherchant les titres dans le texte.
    Si un titre n'est pas trouvé, on garde quand même la section suivante.
    """
    if not section_titles:
        return [{"title": f"Section {chunk_idx + 1}", "text": chunk}]

    # Cherche la position de chaque titre dans le chunk
    positions = []
    for title in section_titles:
        # Cherche le titre ou une version courte (premiers 30 chars)
        key = title[:30]
        pos = chunk.find(key)
        if pos != -1:
            positions.append((pos, title))

    if not positions:
        # Aucun titre trouvé → section unique
        return [{"title": section_titles[0] if section_titles else f"Section {chunk_idx + 1}",
                 "text": chunk}]

    positions.sort(key=lambda x: x[0])

    sections = []
    for i, (pos, title) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(chunk)
        text = chunk[pos:end].strip()
        if text:
            sections.append({"title": title, "text": text})

    return sections if sections else [{"title": f"Section {chunk_idx + 1}", "text": chunk}]

def segment_text(
    text: str,
    titles: list,
    llm_client: Any,
    revision: str = "Les deux",
) -> list[dict]:
    """
    Segmente un texte complet en sections exploitables via LLM.

    Args:
        text:       Texte extrait du document
        titles:     Titres détectés (pour contexte)
        llm_client: Instance OllamaWrapper
        revision:   "Questions de cours" | "Exercices" | "Les deux"

    Returns:
        Liste de dicts {"title": ..., "text": ...}
    """
    if not text.strip():
        logger.warning("Texte vide — segmentation ignorée")
        return []

    chunks = _chunk_text(text)
    logger.info(
        "Segmentation démarrée — %d chunk(s), revision=%r", len(chunks), revision
    )

    all_sections: list[dict] = []
    for idx, chunk in enumerate(chunks):
        sections = _segment_with_llm(chunk, titles, llm_client, chunk_idx=idx, revision=revision)
        all_sections.extend(sections)
        logger.info("Chunk %d/%d → %d section(s)", idx + 1, len(chunks), len(sections))

    logger.info("Segmentation terminée — %d section(s) au total", len(all_sections))
    return all_sections