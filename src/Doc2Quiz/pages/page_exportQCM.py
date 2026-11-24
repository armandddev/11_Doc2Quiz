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

        export_preview_html = gr.HTML(
            "<p style='text-align:center;color:#888'>Aucun QCM à afficher.</p>",
            elem_id="export_preview",
        )

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
            btn_confirm_export = gr.DownloadButton(
                "EXPORTER",
                elem_id="btn_confirm_export"
            )



    return exportQCM_container, btn_exportPDF, btn_confirm_export, btn_profil_exportQCM, export_preview_html