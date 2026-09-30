import base64
from pathlib import Path
import gradio as gr

def render_register_page():
    img_data = (Path(__file__).parent / "assets" / "logo.png").read_bytes()
    b64 = base64.b64encode(img_data).decode()

    with gr.Column(visible=True) as register_container:
        gr.HTML(f'<div class="logo-styles"><img src="data:image/png;base64,{b64}"></div>')

        with gr.Row(elem_id="widthPage"):
            reg_name = gr.Textbox(
                label = "Nom* : ",
                placeholder = "Ex : Dupont", 
                elem_id="labelName"
            )

        with gr.Row(elem_id="widthPage"):
            reg_fname = gr.Textbox(
                label = "Prénom* : ",
                placeholder = "Ex : Jean", 
                elem_id="labelName"
            )

        with gr.Row(elem_id="widthPage"):
            reg_email = gr.Textbox(
                label = "Adresse e-mail* :",
                placeholder = "jean.dupont@mail.com",
                type="email",
                elem_id="labelName"
            )

        with gr.Row(elem_id="widthPage"):
            reg_pwd = gr.Textbox(
                label = "Mot de passe* :",
                placeholder = "Entrer votre mot de passe..",
                type="password",
                elem_id="labelName"
            )

        with gr.Row(elem_id="widthPage"):
            btn_register = gr.Button(
                "Créer mon profil",
                variant="secondary",
                elem_id="buttonCreateAccount",
                interactive= True,
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

    return register_container,reg_name, reg_fname, reg_email, reg_pwd, btn_register, btn_goto_login