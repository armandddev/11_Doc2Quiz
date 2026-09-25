import gradio as gr


def render_quiz_result():
    with gr.Column(visible=False) as result_container:
        # En-tête DOC2QUIZ + profil
        with gr.Row():
            gr.HTML('''
                <div style="width: 100%; text-align: center; margin: 0px auto 20px auto;">
                    <h1 style="font-size: 3rem; font-weight: 800; letter-spacing: 0.35em; color: #000000; margin: 0; text-align: center;">
                        DOC<span style="color: #1B57A1">2</span>QUIZ
                    </h1>
                </div>
            ''')
            btn_profil_result = gr.Button("👤 Mon profil", elem_id="btn_profil")

        # Bloc récapitulatif dynamique
        result_details_html = gr.HTML(
            '''
            <div class="result-recap-box">
                <h2 class="result-congrats">Félicitations, vous avez terminé le QCM</h2>
                <div class="result-info">
                    <p>Matière : <span>Mathématiques</span></p>
                    <p>Sujet : <span>Dérivation</span></p>
                    <p>Niveau : <span>Secondes</span></p>
                    <p>Score : <span class="result-score">3/5</span></p>
                </div>
            </div>
            ''',
            elem_id="result_summary_card"
        )

        # Boutons d'action (Enregistrer / Ne pas sauvegarder)
        with gr.Row(elem_id="result_actions_row"):
            btn_save = gr.Button(
                "Enregistrer dans mon profil",
                elem_id="btn_save_result"
            )
            btn_discard = gr.Button(
                "Ne pas sauvegarder",
                elem_id="btn_discard_result"
            )

    return result_container, result_details_html, btn_save, btn_discard, btn_profil_result