import base64
from pathlib import Path
import gradio as gr

def render_QCM():
    with gr.Column(visible=False) as generateQCM_container:
        with gr.Row():
            ## Titre DOC2QUIZ + bouton "Mon profil"
            gr.HTML('''
                <div style="width: 100%; text-align: center; margin: 0px auto 20px auto;">
                    <h1 style="font-size: 3rem; font-weight: 800; letter-spacing: 0.35em; color: #000000; margin: 0; text-align: center;">
                        DOC<span style="color: #1B57A1">2</span>QUIZ
                    </h1>
                </div>
            ''')
            gr.Button("👤 Mon profil", elem_id="btn_profil")

        ## Texte QCM généré
        gr.HTML('''
            <div style="width: 100%; text-align: center; margin: 20px auto 10px auto;">
                <h2 style="font-size: 1.8rem; color: #000000; margin: 0;">
                    Votre QCM est généré
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

        ## envoie de correctif sur le QCM généré en PDF (pour le moment)
        with gr.Row(elem_id="correction_bar"):
            correction_input = gr.Textbox(
                placeholder="Apporter une correction...",
                show_label=False,
                container=False,
                scale=9,
                elem_id="correction_text"
            )
            btn_submit_correction = gr.Button(
                "↑",
                scale=1,
                elem_id="btn_send_correction"
            )

       ## bouton pour passer à la page suivante
        with gr.Row(elem_id="widthPage"):
            btn_generate_ok = gr.Button(
                "Aucune erreur / Correction détectée",
                variant="secondary",
                elem_id="buttonGenerateOK"
            )

    return generateQCM_container, btn_generate_ok, btn_submit_correction, correction_input