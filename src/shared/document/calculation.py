"""Génération et validation d'exercices de calcul."""

from __future__ import annotations

import json
import re
import argparse
from collections.abc import Iterable
from pathlib import Path
from typing import Any


_NUMBER_RE = re.compile(
    r"(?<![A-Za-zÀ-ÿ0-9_])"
    r"[-+]?(?:\d+(?:[.,]\d+)?|\d{1,3}(?:[ .]\d{3})+(?:[.,]\d+)?)"
    r"(?:[eE][-+]?\d+)?"
)
_OPERATOR_RE = re.compile(
    r"(?:[+*/=^×÷]|\s-\s|\b(?:calcul|calculez|résolvez|déterminez)\b)",
    re.IGNORECASE,
)


def extract_numeric_values(text: str) -> set[float]:
    """
    Extrait les valeurs numériques du texte.
    """
    values = set()
    for match in _NUMBER_RE.finditer(text):
        value = match.group().replace(" ", "").replace(",", ".")
        values.add(float(value))
    return values


def contains_calculation(text: str) -> bool:
    """
    Vérifie la présence d'un nombre et d'une opération.
    """
    return bool(extract_numeric_values(text)) and bool(_OPERATOR_RE.search(text))


def is_calculation_content_type(content_type: str) -> bool:
    """
    Vérifie si le type de contenu est « calcul ».
    """
    return content_type.strip().casefold() == "calcul"


def validate_calculation_text(
    text: str,
    source_values: Iterable[float] = (),
) -> tuple[bool, str]:
    """
    Valide les nombres et opérations du texte généré.
    """
    if not isinstance(text, str) or not text.strip():
        return False, "Le texte généré est vide."
    if not extract_numeric_values(text):
        return False, "Le texte généré ne contient aucune valeur numérique."
    if not _OPERATOR_RE.search(text):
        return False, "Le texte généré ne contient aucune opération à résoudre."

    reused_values = (
        extract_numeric_values(text).intersection(set(source_values)) - {0.0}
    )
    if reused_values:
        return False, f"Valeurs du support réutilisées : {sorted(reused_values)}."
    return True, ""


def build_calculation_prompt(source_text: str, discipline: str, count: int = 3) -> str:
    """
    Construit le prompt des exercices de calcul.
    """
    source_values = sorted(extract_numeric_values(source_text))
    return f"""Tu es un enseignant de {discipline}.
Le tag de détection du support est « calcul » : génère exactement {count} exercices
de résolution numérique, jamais une question de définition ou de restitution.
Chaque énoncé doit contenir des valeurs et une opération à effectuer. Donne aussi
la résolution numérique détaillée dans « bonne_reponse ».
Les valeurs des nouveaux exercices doivent être différentes de celles du support,
tout en restant cohérentes avec la notion enseignée.
Réponds uniquement avec ce JSON :
{{"questions": [{{"id": 1, "type": "exercice", "question": "...", "bonne_reponse": "..."}}]}}

Exemples :
- Équation du second degré : « Résolvez 3x² - 5x - 7 = 0 et détaillez le discriminant. »
- Vitesse constante : « Un mobile parcourt 84 m en 7 s. Calculez sa vitesse moyenne. »

Valeurs interdites car présentes dans le support : {source_values}
Support :
{source_text[:6000]}
"""


def _parse_questions(response: str) -> list[dict[str, Any]]:
    """
    Analyse la réponse JSON du modèle.
    """
    if not isinstance(response, str) or not response.strip():
        raise ValueError("Le modèle a renvoyé une réponse vide.")

    cleaned_response = response.strip()
    cleaned_response = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned_response, flags=re.IGNORECASE)
    try:
        payload = json.loads(cleaned_response)
    except (TypeError, json.JSONDecodeError) as error:
        json_start = cleaned_response.find("{")
        json_end = cleaned_response.rfind("}")
        if json_start >= 0 and json_end > json_start:
            try:
                payload = json.loads(cleaned_response[json_start : json_end + 1])
            except json.JSONDecodeError:
                preview = " ".join(cleaned_response.split())[:300]
                raise ValueError(
                    f"La réponse du modèle n'est pas un JSON valide. Réponse : {preview}"
                ) from error
        else:
            preview = " ".join(cleaned_response.split())[:300]
            raise ValueError(
                f"La réponse du modèle ne contient pas de JSON. Réponse : {preview}"
            ) from error

    questions = payload.get("questions") if isinstance(payload, dict) else payload
    if not isinstance(questions, list) or not questions:
        raise ValueError("La réponse du modèle ne contient aucune question.")
    if not all(isinstance(question, dict) for question in questions):
        raise ValueError("Le format des questions est invalide.")
    return questions


def generate_calculation_exercises(
    source_text: str,
    discipline: str,
    *,
    count: int = 3,
    client: Any = None,
    content_type: str = "calcul",
) -> list[dict[str, Any]]:
    """
    Génère et valide des exercices de calcul.
    """
    if not is_calculation_content_type(content_type):
        raise ValueError("La génération est réservée aux sections de type calcul.")
    if count < 1:
        raise ValueError("count doit être supérieur ou égal à 1.")
    if not source_text.strip():
        raise ValueError("Le support est vide.")

    if client is None:
        from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper

        client = OllamaWrapper()

    response = client.generate_text(
        build_calculation_prompt(source_text, discipline, count)
    ).response
    source_values = extract_numeric_values(source_text)
    questions = _parse_questions(response)
    validated = []
    for question in questions[:count]:
        model_text = "\n".join(
            str(question.get(field, "")) for field in ("question", "bonne_reponse")
        )
        valid, reason = validate_calculation_text(model_text, source_values)
        if not valid:
            raise ValueError(f"Question de calcul invalide : {reason}")
        question["type"] = "exercice"
        validated.append(question)

    if len(validated) != count:
        raise ValueError(f"Le modèle a généré {len(validated)} question(s), {count} attendue(s).")
    return validated


def generate_calculation_exercises_from_file(
    file_path: str,
    *,
    count: int = 3,
) -> list[dict[str, Any]]:
    """
    Extrait un support et génère ses exercices de calcul.
    """
    from .extraction import extractFromMd, extractFromPdf

    path = Path(file_path)
    if path.suffix.casefold() == ".pdf":
        document = extractFromPdf(str(path))
    elif path.suffix.casefold() in {".md", ".txt"}:
        document = extractFromMd(str(path))
    else:
        raise ValueError("Format accepté : PDF, Markdown ou TXT.")

    calculation_section = next(
        (
            section
            for section in document["sections"]
            if is_calculation_content_type(str(section.get("content_type", "")))
        ),
        None,
    )
    if calculation_section is None:
        raise ValueError("Aucune section de type calcul détectée par l'US-08.")

    return generate_calculation_exercises(
        document["text"],
        calculation_section.get("discipline", "scientifique"),
        count=count,
        content_type=calculation_section["content_type"],
    )


def main() -> None:
    """
    Lance la génération depuis la ligne de commande.
    """
    parser = argparse.ArgumentParser(
        description="Génère des exercices de calcul depuis un support PDF ou Markdown."
    )
    parser.add_argument("support", help="Chemin du support PDF, MD ou TXT")
    parser.add_argument("-n", "--count", type=int, default=3, help="Nombre d'exercices")
    args = parser.parse_args()
    exercises = generate_calculation_exercises_from_file(args.support, count=args.count)
    print(json.dumps({"questions": exercises}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()