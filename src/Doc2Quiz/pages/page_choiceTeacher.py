import base64
from pathlib import Path
import gradio as gr

from shared.qcm import enregistrer_modification


def render_choiceTeacher():
    """Construit la page enseignant et renvoie ses composants interactifs."""
    with gr.Column(visible=False) as choiceTeacher_container:
        with gr.Row():
            ## Titre DOC2QUIZ + bouton "Mon profil"
            gr.HTML('''
                <div style="width: 100%; text-align: center; margin: 0px auto 20px auto;">
                    <h1 style="font-size: 3rem; font-weight: 800; letter-spacing: 0.35em; color: #000000; margin: 0; text-align: center;">
                        DOC<span style="color: #1B57A1">2</span>QUIZ
                    </h1>
                </div>
            ''')
            btn_profil_ChoiceTeacher = gr.Button("👤 Mon profil", elem_id="btn_profil")

        # Titre de la page
        gr.HTML('''
            <div style="width: 100%; text-align: center; margin: 20px auto;">
                <h2 style="font-size: 2rem; font-weight: 600; color: #000000; margin: 0;">
                    Choix pour votre QCM
                </h2>
            </div>
        ''')

        ## Visualisation du QCM via l'application web
        pdf_path = Path("storage/CV-BONNIER_Gabin.pdf").resolve()

        if pdf_path.exists():
            encoded_pdf = base64.b64encode(pdf_path.read_bytes()).decode("utf-8")
            html_viewer = f'''
                <div style="width: 80%; margin: 20px auto; border: 2px solid #000000; border-radius: 8px; overflow: hidden; background: #FFFFFF;">
                    <iframe src="data:application/pdf;base64,{encoded_pdf}" width="100%" height="500px" style="border: none;"></iframe>
                </div>
            '''
        else:
            html_viewer = f"<p style='color: red; text-align: center;'>Introuvable : {pdf_path}</p>"

        gr.HTML(html_viewer)

        gr.Markdown("### Modifier le QCM")
        question_selector = gr.Dropdown(
            choices=[],
            label="Question à corriger",
            interactive=True,
        )
        question_input = gr.Textbox(label="Énoncé", lines=3, interactive=True)
        options_input = gr.Textbox(
            label="Options (une par ligne)",
            lines=4,
            interactive=True,
        )
        answer_input = gr.Textbox(label="Bonne réponse proposée par l'IA", interactive=False)
        error_input = gr.Textbox(
            label="Décrivez l'erreur",
            placeholder="Exemple : la bonne réponse devrait être...",
            lines=3,
        )
        with gr.Row():
            save_question_button = gr.Button(
                "Corriger avec l'IA", variant="primary"
            )
            modification_status = gr.Markdown()

        with gr.Row(elem_id="student_actions"):
            btn_export = gr.Button(
                            "Exporter le QCM",
                            variant="secondary",
                            elem_id="buttonExport"
                        )

    return (
        choiceTeacher_container,
        btn_export,
        btn_profil_ChoiceTeacher,
        question_selector,
        question_input,
        options_input,
        answer_input,
        error_input,
        save_question_button,
        modification_status,
    )
