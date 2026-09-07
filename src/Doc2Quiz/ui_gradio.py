# src/<subject>/ui_gradio.py
import gradio as gr
from ..service import <service_func>          # fonction pure du sujet
from ..config import Settings                # pydantic Settings
# éventuels imports de storage, ollama_client …

# ----------------------------------------------------
# Wrapper qui sera exposé à Gradio
# ----------------------------------------------------
def expose(input_data, **kw) -> Any:
    """
    Fonction pure qui appelle le service métier.
    - `input_data` provient directement des composants Gradio.
    - Retourne un **objet JSON‑serialisable**.
    """
    result = <service_func>(input_data, **kw)   # <service_func> est pure
    return result                               # Gradio le convertit automatiquement

# ----------------------------------------------------
# Construction du bloc UI
# ----------------------------------------------------
with gr.Blocks() as demo:
    # Exemples génériques (un par sujet)
    txt = gr.Textbox(label="Requête", placeholder="…")
    btn = gr.Button("Envoyer")
    out = gr.Markdown()          # ou Dataframe, Gallery, Image, etc.

    btn.click(fn=expose, inputs=[txt], outputs=out)

    # Optionnel : streaming ou mise à jour progressive
    # btn.click(fn=lambda x: gr.update(value="…"), …)

demo.launch(
    server_name="0.0.0.0",    # indispensable pour Docker
    server_port=7860,
    share=False,              # si vous voulez un partage public, mettez True
    debug=False
)