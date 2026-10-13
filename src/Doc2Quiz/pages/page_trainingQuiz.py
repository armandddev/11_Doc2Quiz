import gradio as gr


def format_qcm_choice(letter: str, text: str) -> str:
    return f"""<span class="qcm-badge">{letter}</span><span class="qcm-text">{text}</span>"""


def render_training_quiz():
    with gr.Column(visible=False) as training_quiz_container:
        
        # En-tête : Bouton "← Quitter", Titre DOC2QUIZ, Bouton profil
        with gr.Row(elem_id="training_header_row"):
            gr.HTML(
                """
                <div style="width: 100%; text-align: center;">
                    <h1 style="font-size: 3rem; font-weight: 800; letter-spacing: 0.35em; color: #000000; margin: 0;">
                        DOC<span style="color: #1B57A1">2</span>QUIZ
                    </h1>
                </div>
            """
            )
            btn_profil_trainingQuiz = gr.Button("👤 Mon profil", elem_id="btn_profil")

        btn_quit = gr.Button("← Quitter", elem_id="btn_quit_quiz")

        # Cartouche bleu de la question (titre + intitulé)
        question_header_html = gr.HTML(
            """
            <div class="question-header-card">
                <div class="question-step">Question 1 -</div>
                <div class="question-title">Quelle est la formule du déterminant (delta) ?</div>
            </div>
            """,
            elem_id="quiz_question_card",
        )

        # 1. Vue QCM (Radio customisé avec A, B, C, D)
        with gr.Column(visible=True) as qcm_block:
            qcm_radio = gr.Radio(
                choices=[],
                value=None,
                show_label=False,
                container=False,
                interactive=True,
                elem_id="qcm_custom_radio",
            )

        # 2. Vue Réponse libre / Exercice
        with gr.Column(visible=False) as free_text_block:
            free_text_input = gr.Textbox(
                placeholder="Rédigez votre réponse ici...",
                lines=5,
                show_label=False,
                elem_id="quiz_free_text",
            )

        # Message de feedback après validation
        feedback_html = gr.HTML("", visible=False)



        # Vue Réponse libre / Exercice
        with gr.Column(visible=False) as free_text_block:
            free_text_input = gr.Textbox(
                placeholder="Rédigez votre démarche, calculs intermédiaires et résultat final ici...",
                lines=5,
                show_label=False,
                container=False, 
                interactive=True,
                elem_id="quiz_exercise_input"
            )


        # Bouton d'action "Valider mon choix"
        with gr.Row(elem_id="quiz_action_row"):
            btn_validate = gr.Button(
                "Valider mon choix", elem_id="btn_validate_choice"
            )


    return (
        training_quiz_container,
        btn_quit,
        question_header_html,
        qcm_block,
        qcm_radio,
        free_text_block,
        free_text_input,
        btn_validate,
        feedback_html,
        btn_profil_trainingQuiz,
    )