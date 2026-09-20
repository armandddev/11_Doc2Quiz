def summarize_text(text: str, summary_generator=None) -> str:
    cleaned_text = " ".join(text.split())
    if not cleaned_text:
        return ""

    if summary_generator is not None:
        try:
            summary = summary_generator(cleaned_text)
            if summary:
                return summary.strip()
        except Exception:
            pass

    try:
        from Doc2Quiz.ollama_client.ollama_wrapper import OllamaWrapper

        wrapper = OllamaWrapper()
        if wrapper.is_server_running():
            prompt = (
                "Résume ce texte en 1 ou 2 phrases très courtes, sans liste ni points.\n\n"
                f"Texte :\n{cleaned_text[:3000]}"
            )
            result = wrapper.generate_text(prompt).response
            if result and result.strip():
                return result.strip()
    except Exception:
        pass

    sentences = []
    for part in cleaned_text.replace("!", ".").replace("?", ".").split("."):
        sentence = part.strip()
        if sentence:
            sentences.append(sentence)
        if len(sentences) == 2:
            break

    if sentences:
        return ". ".join(sentences)

    return cleaned_text[:200]