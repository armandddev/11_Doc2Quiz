from .models import Section
from .summary import summarize_text


def segment_text(text: str, titles: list[dict], summary_generator=None) -> list[dict]:
    # Cas ou il n'y a aucun texte
    if not text.strip():
        return []
    
    # Cas ou il y a des titres 
    if titles:
        sections = _sections_from_titles(text, titles, summary_generator)
        if sections:
            return sections

    return _sections_from_paragraphs(text, summary_generator)

# Fonction qui va découper lorsqu'il y a des titres
def _sections_from_titles(text: str, titles: list[dict], summary_generator) -> list[dict]:
    lines = text.splitlines()
    title_lines = []
    next_line_to_check = 0

    # Trouve chaque titre dans l'ordre où il apparaît dans le texte.
    for title in titles:
        for line_number in range(next_line_to_check, len(lines)):
            if lines[line_number].strip() == title["text"].strip():
                title_lines.append((line_number, title))
                next_line_to_check = line_number + 1
                break

    sections = []
    for index, (title_line, title) in enumerate(title_lines):
        # Détermine la fin de la section en fonction du titre suivant
        if index + 1 < len(title_lines):
            next_title_line = title_lines[index + 1][0]
        else:
            next_title_line = len(lines)

        section_lines = lines[title_line:next_title_line]
        section_text = "\n".join(section_lines).strip()

        sections.append(
            _make_section(
                index + 1,
                title["text"],
                title["level"],
                section_text,
                summary_generator,
                None,
                [title["page"]],
            )
        )

    return sections

# Fonction qui va découper quand il n'y a pas de titre 
def _sections_from_paragraphs(text: str, summary_generator) -> list[dict]:
    paragraphs = []
    for part in text.split("\n\n"):
        cleaned_part = part.strip()
        if cleaned_part:
            # Cas ou il y a du texte -> On ajoute le texte à la liste des paragraphes
            paragraphs.append(cleaned_part)

    sections = []
    current_words = []

    for paragraph in paragraphs:
        # Transformation en liste de mots
        words = paragraph.split()
        # Cas ou n paragraphes font moins de 250 mots -> On les regroupe dans une section
        if current_words and len(current_words) + len(words) > 250:
            section_index = len(sections) + 1
            section = _make_fallback_section(section_index, current_words, summary_generator)
            sections.append(section)
            current_words = []

        current_words.extend(words)
    # Dernière section avec les mots restants 
    if current_words:
        section_index = len(sections) + 1
        section = _make_fallback_section(section_index, current_words, summary_generator)
        sections.append(section)

    return sections


# Fonctions utile dans le cas ou il n'y a pas de titre de type H1, ...
def _make_fallback_section(index: int, words: list[str], summary_generator) -> dict:
    text = " ".join(words)
    return _make_section(
        index,
        f"Section {index}",
        None,
        text,
        summary_generator,
        [],
        [],
    )

# Permet de créer un objet de type Section 
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
    # Convertion de l'objet en un dictionnaire
    return section.to_dict()