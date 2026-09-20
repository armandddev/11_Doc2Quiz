from .models import Section
import json

def detection_section_displine(section : Section) :
    # Check if the section is not empty
    if len(section.pages) == 0 or not section.text.strip():
        raise Exception("Section empty")
    try :
        from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper
        # Appel Ollama
        wrapper = OllamaWrapper()
        prompt = (
            "Tu es un assistant pédagogique. Analyse le texte suivant extrait d'un cours et réponds uniquement en JSON.\n\n"
            f"Texte :\n{section.text[:3000]}\n\n"
            "Réponds avec ce format exact :\n"
            '{"discipline": "la matière du texte en un mot", '
            '"content_type": "une seule valeur parmi : théorique, calcul"\n\n}'
            "Aucun texte avant ou après le JSON."
        )
        result = wrapper.generate_text(prompt).response
        # Parse the result in section
        if result :
            data = json.loads(result.strip())
            section.discipline = data["discipline"]
            section.content_type = data["content_type"]
            return section
    except Exception:
        raise Exception("Problem of connection")