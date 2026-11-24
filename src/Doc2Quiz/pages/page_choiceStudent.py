import gradio as gr

def render_choiceEtudiant():
    with gr.Column(visible=False) as revisionEtudiant_container:
        with gr.Row():
            ## Titre DOC2QUIZ + bouton "Mon profil"
            gr.HTML('''
                <div style="width: 100%; text-align: center; margin: 0px auto 20px auto;">
                    <h1 style="font-size: 3rem; font-weight: 800; letter-spacing: 0.35em; color: #000000; margin: 0; text-align: center;">
                        DOC<span style="color: #1B57A1">2</span>QUIZ
                    </h1>
                </div>
            ''')
            btn_profil_ChoiceEtudiant = gr.Button("👤 Mon profil", elem_id="btn_profil")

        # Titre de la page
        gr.HTML('''
            <div style="width: 100%; text-align: center; margin: 20px auto;">
                <h2 style="font-size: 2rem; font-weight: 600; color: #000000; margin: 0;">
                    Choix pour votre QCM
                </h2>
            </div>
        ''')



        student_preview_html = gr.HTML(
            "<p style='text-align:center;color:#888'>Aucun QCM à afficher.</p>",
            elem_id="student_preview",
        )

        with gr.Row(elem_id="student_actions"):
            btn_export = gr.Button(
                            "Exporter le QCM",
                            variant="secondary",
                            elem_id="buttonExport"
                        )
            btn_training = gr.Button(
                                        "Entraînement",
                                        variant="secondary",
                                        elem_id="buttonTraining"
                                    )


    return revisionEtudiant_container, btn_export, btn_training, btn_profil_ChoiceEtudiant, student_preview_html