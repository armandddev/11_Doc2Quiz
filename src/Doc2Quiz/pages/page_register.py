import base64
from pathlib import Path
import gradio as gr

def render_register_page():
    img_data = (Path.cwd() / "pages" / "assets" / "logo.png").read_bytes()
    b64 = base64.b64encode(img_data).decode()

    with gr.Column(visible=False) as register_container:
        gr.HTML(f'<div class="logo-styles"><img src="data:image/png;base64,{b64}"></div>')

        with gr.Row(elem_id="widthPage"):
            gr.Textbox(
                label = "Nom* : ",
                placeholder = "Ex : Dupont", 
                elem_id="labelName"
            )

        with gr.Row(elem_id="widthPage"):
            gr.Textbox(
                label = "Prénom* : ",
                placeholder = "Ex : Jean", 
                elem_id="labelName"
            )

        with gr.Row(elem_id="widthPage"):
            gr.Textbox(
                label = "Adresse e-mail* :",
                placeholder = "jean.dupont@mail.com",
                type="email",
                elem_id="labelName"
            )

        with gr.Row(elem_id="widthPage"):
            gr.Textbox(
                label = "Mot de passe* :",
                placeholder = "Entrer votre mot de passe..",
                type="password",
                elem_id="labelName"
            )

        with gr.Row(elem_id="widthPage"):
            gr.Button(
                "Créer mon profil",
                variant="secondary",
                elem_id="buttonCreateAccount"
            )

        with gr.Row(elem_id="widthPage"):
            btn_goto_login = gr.Button(
                "Déjà un compte ? Connectez-vous",
                elem_id="linkAccount"
            )

        with gr.Row(elem_id="widthPage"):
            gr.Markdown(    
                "Les champs mentionnés par (*) sont obligatoires",
            )

    return register_container, btn_goto_login