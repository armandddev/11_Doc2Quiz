from pathlib import Path
import gradio as gr

from context import AppContext, Role, UserContext

from pages.page_register import render_register_page
from pages.page_sign_in import render_sign_in_page
from pages.page_homePage import render_homePage
from pages.page_choiceStudent import render_choiceEtudiant
from pages.page_QCM import render_QCM
from pages.page_choiceTeacher import render_choiceTeacher
from pages.page_exportQCM import render_exportQCM
from pages.page_trainingQuiz import render_training_quiz
from pages.page_quizResult import render_quiz_result

# Remplace 'mock_profil' par le fichier exact contenant ton get_template_quiz
from Template.MOCK_Question import get_template_quiz

css_file = Path(__file__).resolve().parent / "style.css"
custom_css = css_file.read_text(encoding="utf-8") if css_file.exists() else ""

global_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.blue,
    font=[gr.themes.GoogleFont("Roboto"), "sans-serif"],
)

def route_after_generate(app_context: AppContext):
    if not app_context or not app_context.is_authenticated:
        return (
            gr.update(visible=False),  
            gr.update(visible=False),  
            gr.update(visible=False),  
            gr.update(visible=False),  
            gr.update(visible=True)    
        )

    if not app_context.is_teacher:
        return (
            gr.update(visible=False),  
            gr.update(visible=False),  
            gr.update(visible=True),   
            gr.update(visible=False),  
            gr.update(visible=False)   
        )

    return (
        gr.update(visible=False),      
        gr.update(visible=False),      
        gr.update(visible=False),      
        gr.update(visible=True),       
        gr.update(visible=False)       
    )

def load_question_view(questions: list, current_index: int):
    """
    Met à jour dynamiquement l'interface selon le type de question :
    - qcm : active les options A/B/C/D et masque la saisie libre.
    - exercice / cours_libre : masque le QCM et affiche la grande zone de texte.
    """
    # Cas où le quiz est fini ou vide
    if not questions or current_index >= len(questions):
        end_html = """
            <div class="question-header-card">
                <div class="question-title">Quiz terminé !</div>
            </div>
        """
        return (
            gr.update(value=end_html),
            gr.update(visible=False),  # qcm_block
            gr.update(choices=[], value=None),  # qcm_radio
            gr.update(visible=False),  # free_text_block
            gr.update(value=""),  # free_text_input
        )

    q = questions[current_index]
    num_str = f"Question {current_index + 1} -"

    # Remplacement des sauts de ligne pour un affichage propre en HTML
    question_text = q.get("question", "").replace("\n", "<br>")

    header_html = f"""
        <div class="question-header-card">
            <div class="question-step">{num_str}</div>
            <div class="question-title">{question_text}</div>
        </div>
    """

    # Mode 1 : Question QCM
    if q.get("type") == "qcm":
        return (
            gr.update(value=header_html),
            gr.update(visible=True),  # Affiche le conteneur QCM
            gr.update(
                choices=q.get("options", []), value=None
            ),  # Remplit les options
            gr.update(visible=False),  # Masque la zone de saisie libre
            gr.update(value=""),
        )

    # Mode 2 : Exercice ou Réponse libre
    default_placeholder = (
        "Rédigez votre démarche, calculs intermédiaires et résultat final ici..."
    )
    return (
        gr.update(value=header_html),
        gr.update(visible=False),  # Masque le conteneur QCM
        gr.update(choices=[], value=None),
        gr.update(visible=True),  # Affiche la zone de saisie libre
        gr.update(
            value="",
            placeholder=q.get("placeholder", default_placeholder),
            lines=q.get("lignes", 10),
        ),
    )


## Interface
with gr.Blocks(title="11_Doc2Quiz") as demo:
    current_session = AppContext(
        user=UserContext(
            user_id=1,
            email="etudiant@univ.fr",
            name="Gabin",
            role=Role.STUDENT  # Role.TEACHER | Role.STUDENT
        )
    )
    app_state = gr.State(value=current_session)

    # États pour mémoriser les questions du quiz et l'étape actuelle
    quiz_questions_state = gr.State(value=[])
    quiz_index_state = gr.State(value=0)

    # 1. Déballage avec les containers EN PREMIER et les boutons profil EN DERNIER
    result_container, result_details_html, btn_save, btn_discard, btn_profil_result = render_quiz_result()
    homepage_container, upload_zone, difficulty_dropdown, revision_choice, btn_to_generate, btn_profil_homePage = render_homePage()
    generateQCM_container, btn_generate_ok, btn_submit_correction, correction_input, btn_profil_QCM = render_QCM()    
    register_view, btn_to_login = render_register_page()
    sign_in_view, btn_to_register = render_sign_in_page()
    revisionEtudiant_container, btn_export_student, btn_training, btn_profil_ChoiceEtudiant = render_choiceEtudiant()
    choiceTeacher_container, btn_export_teacher, btn_profil_ChoiceTeacher = render_choiceTeacher()
    exportQCM_container, btn_exportPDF, btn_confirm_export, btn_profil_exportQCM = render_exportQCM()
    (
        training_quiz_container,
        btn_quit,
        question_header_html,
        qcm_block,
        qcm_radio,
        free_text_block,
        free_text_input,
        btn_validate,
        feedback_html,
        btn_profil_trainingQuiz
    ) = render_training_quiz()

    # 2. Navigation Register / Login
    btn_to_login.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[register_view, sign_in_view]
    )

    btn_to_register.click(
        fn=lambda: (gr.update(visible=True), gr.update(visible=False)),
        inputs=None,
        outputs=[register_view, sign_in_view]
    )

    btn_to_generate.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[homepage_container, generateQCM_container]
    )

    btn_export_student.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[revisionEtudiant_container, exportQCM_container]
    )

    btn_export_teacher.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[choiceTeacher_container, exportQCM_container]
    )

    # 3. Redirection propre vers le profil (ferme la page actuelle et ouvre le profil)
    target_profil_view = sign_in_view  # Remplace par profil_container si tu as créé la page profil

    profil_navigation = [
        (btn_profil_result, result_container),
        (btn_profil_homePage, homepage_container),
        (btn_profil_QCM, generateQCM_container),  
        (btn_profil_ChoiceEtudiant, revisionEtudiant_container),
        (btn_profil_ChoiceTeacher, choiceTeacher_container),
        (btn_profil_exportQCM, exportQCM_container),
        (btn_profil_trainingQuiz, training_quiz_container),
    ]

    for btn, current_page in profil_navigation:
        btn.click(
            fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
            inputs=None,
            outputs=[current_page, target_profil_view]
        )


    # Démarrage du quiz avec chargement de la première question
    def on_start_training(type_rev):
        data = get_template_quiz(type_rev or "Questions de cours")
        idx = 0
        h_up, qcm_v, radio_u, free_v, text_u = load_question_view(data, idx)
        return (
            gr.update(visible=False),  # masque page de choix étudiant
            gr.update(visible=True),   # affiche quiz
            data,
            idx,
            h_up,
            qcm_v,
            radio_u,
            free_v,
            text_u
        )

    def display_final_result(subject: str, topic: str, level: str, score: int, total: int):
        html_content = f'''
            <div class="result-recap-box">
                <h2 class="result-congrats">Félicitations, vous avez terminé le QCM</h2>
                <div class="result-info">
                    <p>Matière : <span>{subject}</span></p>
                    <p>Sujet : <span>{topic}</span></p>
                    <p>Niveau : <span>{level}</span></p>
                    <p>Score : <span class="result-score">{score}/{total}</span></p>
                </div>
            </div>
        '''
        return (
            gr.update(visible=False),  # masque training_quiz_container
            gr.update(visible=True),   # affiche result_container
            html_content
        )

    btn_training.click(
        fn=on_start_training,
        inputs=[revision_choice],
        outputs=[
            revisionEtudiant_container,
            training_quiz_container,
            quiz_questions_state,
            quiz_index_state,
            question_header_html,
            qcm_block,
            qcm_radio,
            free_text_block,
            free_text_input
        ]
    )

    # Bouton retour "← Quitter"
    btn_quit.click(
        fn=lambda: (gr.update(visible=True), gr.update(visible=False)),
        inputs=None,
        outputs=[revisionEtudiant_container, training_quiz_container]
    )

    btn_generate_ok.click(
        fn=route_after_generate,
        inputs=[app_state],
        outputs=[
            homepage_container,
            generateQCM_container,
            revisionEtudiant_container,
            choiceTeacher_container,
            sign_in_view
        ]
    )

    btn_discard.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[result_container, homepage_container]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=global_theme,
        css=custom_css,
        share=False,
    )