import base64
from pathlib import Path
import gradio as gr

def render_exportQCM():
    with gr.Column(visible=False) as exportQCM_container:
        with gr.Row():
            ## Titre DOC2QUIZ + bouton "Mon profil"
            gr.HTML('''
                <div style="width: 100%; text-align: center; margin: 0px auto 20px auto;">
                    <h1 style="font-size: 3rem; font-weight: 800; letter-spacing: 0.35em; color: #000000; margin: 0; text-align: center;">
                        DOC<span style="color: #1B57A1">2</span>QUIZ
                    </h1>
                </div>
            ''')
            btn_profil_exportQCM = gr.Button("👤 Mon profil", elem_id="btn_profil")

        # Titre de la page
        gr.HTML('''
            <div style="width: 100%; text-align: center; margin: 20px auto;">
                <h2 style="font-size: 2rem; font-weight: 600; color: #000000; margin: 0;">
                    Vous avez choisis d'exporter votre QCM
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

        with gr.Row(elem_id="student_actions"):
            btn_exportPDF = gr.Radio(
                            choices=["PDF", "GIFT", "XML"],
                            value="PDF",
                            interactive=True,
                            show_label=False,
                            container=False,
                            elem_id="export_format_selector"
                        )
            
        # Bouton d'action Exporter
        with gr.Row(elem_id="export_action_row"):
            btn_confirm_export = gr.Button(
                "EXPORTER",
                elem_id="btn_confirm_export"
            )



    return exportQCM_container, btn_exportPDF, btn_confirm_export, btn_profil_exportQCM