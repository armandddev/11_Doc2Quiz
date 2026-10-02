from pathlib import Path
import gradio as gr
from service.auth_service import handle_login, handle_register
from context import AppContext, Role, UserContext

from pages.page_register import render_register_page
from pages.page_sign_in import render_sign_in_page
from pages.page_homePage import render_homePage
from pages.page_choiceStudent import render_choiceEtudiant
from pages.page_QCM import render_QCM, render_qcm_html
from pages.page_choiceTeacher import render_choiceTeacher, enregistrer_modification
from pages.page_exportQCM import render_exportQCM
from pages.page_trainingQuiz import render_training_quiz
from pages.page_quizResult import render_quiz_result
from pages.page_profil import render_profil

from Template.MOCK_Question import get_template_quiz

css_file = Path(__file__).resolve().parent / "style.css"
custom_css = css_file.read_text(encoding="utf-8") if css_file.exists() else ""

global_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.blue,
    font=[gr.themes.GoogleFont("Roboto"), "sans-serif"],
)

def on_go_to_qcm(file, revision, difficulty, app_context):
    if file is None:
        return gr.update(), gr.update(), gr.update(), gr.update(), app_context
    app_context.pending_file       = file
    app_context.pending_revision   = revision
    app_context.pending_difficulty = difficulty
    return (
        gr.update(visible=False),   # homepage
        gr.update(visible=True),    # generateQCM_container
        gr.update(visible=True),    # loading_section → spinner ON
        gr.update(visible=False),   # qcm_section → masqué
        app_context,
    )

def on_generate_qcm_and_display(app_context):
    try:
        questions = app_context.generate_qcm(
            app_context.pending_file,
            revision=app_context.pending_revision,
        )
        app_context.sections = questions
        html = render_qcm_html(questions)
    except Exception as e:
        print(f"[ERREUR] Génération QCM : {e}", flush=True)
        html = (
            f"<p style='color:red;text-align:center;padding:30px'>"
            f"❌ Erreur lors de la génération : {e}</p>"
        )
        questions = []
        app_context.sections = []

    return (
        gr.update(visible=False),   # loading_section → spinner OFF
        gr.update(visible=True),    # qcm_section → contenu visible
        gr.update(value=html),      # qcm_html_out → HTML du QCM
        questions,                  # quiz_questions_state → alimente l'éditeur du collègue
        app_context,
    )

def route_after_generate(app_context: AppContext):
    if not app_context or not app_context.is_authenticated:
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
        )
    if not app_context.is_teacher:
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        )
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
    )

def load_question_view(questions: list, current_index: int):
    if not questions or current_index >= len(questions):
        end_html = """
            <div class="question-header-card">
                <div class="question-title">Quiz terminé !</div>
            </div>
        """
        return (
            gr.update(value=end_html),
            gr.update(visible=False),
            gr.update(choices=[], value=None),
            gr.update(visible=False),
            gr.update(value=""),
        )

    q = questions[current_index]
    num_str = f"Question {current_index + 1} -"
    question_text = q.get("question", "").replace("\n", "<br>")

    header_html = f"""
        <div class="question-header-card">
            <div class="question-step">{num_str}</div>
            <div class="question-title">{question_text}</div>
        </div>
    """

    if q.get("type") == "qcm":
        return (
            gr.update(value=header_html),
            gr.update(visible=True),
            gr.update(choices=q.get("options", []), value=None),
            gr.update(visible=False),
            gr.update(value=""),
        )

    default_placeholder = (
        "Rédigez votre démarche, calculs intermédiaires et résultat final ici..."
    )
    return (
        gr.update(value=header_html),
        gr.update(visible=False),
        gr.update(choices=[], value=None),
        gr.update(visible=True),
        gr.update(
            value="",
            placeholder=q.get("placeholder", default_placeholder),
            lines=q.get("lignes", 10),
        ),
    )


def charger_question_editeur(questions: list[dict], question_index: int):
    if not questions or question_index is None:
        return "", "", ""
    item = questions[int(question_index)]
    options = item.get("options", [])
    return (
        item.get("question", ""),
        "\n".join(options),
        item.get("bonne_reponse", ""),
    )


def charger_editeur_qcm(questions: list[dict]):
    if not questions:
        return (
            gr.update(choices=[], value=None),
            *charger_question_editeur([], None),
            "",
            "Aucun QCM à modifier.",
        )
    choices = [(f"Question {index + 1}", index) for index in range(len(questions))]
    return (
        gr.update(choices=choices, value=0),
        *charger_question_editeur(questions, 0),
        "",
        "",
    )


## Interface
with gr.Blocks(title="11_Doc2Quiz") as demo:
    current_session = AppContext(user=None)
    app_state = gr.State(value=current_session)
    status = gr.Markdown()

    quiz_questions_state = gr.State(value=[])
    quiz_index_state = gr.State(value=0)

    result_container, result_details_html, btn_save, btn_discard, btn_profil_result = render_quiz_result()
    homepage_container, upload_zone, difficulty_dropdown, revision_choice, btn_to_generate, btn_profil_homePage = render_homePage()

    (
        generateQCM_container,
        loading_section,
        qcm_section,
        qcm_html_out,
        btn_generate_ok,
        btn_submit_correction,
        correction_input,
        btn_back_QCM,
        btn_profil_QCM,
    ) = render_QCM()

    register_view, reg_name, reg_fname, reg_email, reg_pwd, btn_register, btn_to_login = render_register_page()
    sign_in_container, si_email, si_pwd, btn_login, btn_goto_register = render_sign_in_page()
    revisionEtudiant_container, btn_export_student, btn_training, btn_profil_ChoiceEtudiant = render_choiceEtudiant()
    (
        choiceTeacher_container,
        btn_export_teacher,
        btn_profil_ChoiceTeacher,
        question_selector,
        question_input,
        options_input,
        answer_input,
        error_input,
        save_question_button,
        modification_status,
    ) = render_choiceTeacher()
    exportQCM_container, btn_exportPDF, btn_confirm_export, btn_profil_exportQCM = render_exportQCM()
    training_quiz_container, btn_quit, question_header_html, qcm_block, qcm_radio, free_text_block, free_text_input, btn_validate, feedback_html, btn_profil_trainingQuiz = render_training_quiz()
    profil_container, btn_quit_profil, profil_title_html, user_info_html, btn_edit_profile, history_info_html, btn_delete_history, btn_delete_profile = render_profil()

    btn_to_login.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[register_view, sign_in_container]
    )

    btn_goto_register.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[sign_in_container, register_view]
    )

    btn_to_generate.click(
        fn=on_go_to_qcm,
        inputs=[upload_zone, revision_choice, difficulty_dropdown, app_state],
        outputs=[
            homepage_container,
            generateQCM_container,
            loading_section,
            qcm_section,
            app_state,
        ],
    ).then(
        fn=on_generate_qcm_and_display,
        inputs=[app_state],
        outputs=[
            loading_section,            # spinner OFF
            qcm_section,                # contenu ON
            qcm_html_out,               # HTML QCM
            quiz_questions_state,       # ← alimente l'éditeur du collègue
            app_state,
        ],
    )
    
    btn_back_QCM.click(
        fn=lambda: (
            gr.update(visible=True),    # homepage
            gr.update(visible=False),   # cache QCM container
            gr.update(visible=True),    # remet spinner pour prochaine visite
            gr.update(visible=False),   # cache section contenu
        ),
        inputs=None,
        outputs=[homepage_container, generateQCM_container, loading_section, qcm_section],
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

    btn_login.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[sign_in_container, homepage_container]
    )

    target_profil_view = profil_container
    profil_navigation = [
        (btn_profil_result,         result_container),
        (btn_profil_homePage,       homepage_container),
        (btn_profil_QCM,            generateQCM_container),
        (btn_profil_ChoiceEtudiant, revisionEtudiant_container),
        (btn_profil_ChoiceTeacher,  choiceTeacher_container),
        (btn_profil_exportQCM,      exportQCM_container),
        (btn_profil_trainingQuiz,   training_quiz_container),
    ]

    for btn, current_page in profil_navigation:
        btn.click(
            fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
            inputs=None,
            outputs=[current_page, target_profil_view]
        )

    def on_start_training(type_rev):
        data = get_template_quiz(type_rev or "Questions de cours")
        idx = 0
        h_up, qcm_v, radio_u, free_v, text_u = load_question_view(data, idx)
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            data, idx,
            h_up, qcm_v, radio_u, free_v, text_u,
        )

    btn_training.click(
        fn=on_start_training,
        inputs=[revision_choice],
        outputs=[
            revisionEtudiant_container, training_quiz_container,
            quiz_questions_state, quiz_index_state,
            question_header_html, qcm_block, qcm_radio, free_text_block, free_text_input,
        ]
    )

    def check_register_fields(n, fn, e, p):
        return gr.update(interactive=bool(n and fn and e and p))

    gr.on(
        triggers=[reg_name.change, reg_fname.change, reg_email.change, reg_pwd.change],
        fn=check_register_fields,
        inputs=[reg_name, reg_fname, reg_email, reg_pwd],
        outputs=[btn_register]
    )

    def check_login_fields(e, p):
        return gr.update(interactive=bool(e and p))

    gr.on(
        triggers=[si_email.change, si_pwd.change],
        fn=check_login_fields,
        inputs=[si_email, si_pwd],
        outputs=[btn_login]
    )

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
            sign_in_container,
        ],
    )

    btn_generate_ok.click(
        fn=charger_editeur_qcm,
        inputs=[quiz_questions_state],
        outputs=[
            question_selector,
            question_input,
            options_input,
            answer_input,
            error_input,
            modification_status,
        ],
    )

    question_selector.change(
        fn=charger_question_editeur,
        inputs=[quiz_questions_state, question_selector],
        outputs=[question_input, options_input, answer_input],
    )

    save_question_button.click(
        fn=enregistrer_modification,
        inputs=[quiz_questions_state, question_selector, error_input],
        outputs=[
            quiz_questions_state,
            question_input,
            options_input,
            answer_input,
            modification_status,
        ],
    )

    btn_discard.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[result_container, homepage_container]
    )

    def on_login_submit(ctx, email, pwd):
        print(f"--> [LOGIN] Tentative pour : {email}", flush=True)
        try:
            updated_ctx, msg = handle_login(ctx, email, pwd)
            print(f"--> [LOGIN OK] Connecté : {updated_ctx.user.name}", flush=True)
            return (
                updated_ctx,
                gr.update(value=f"✅ {msg}", visible=True),
                gr.update(visible=False),
                gr.update(visible=True),
            )
        except Exception as e:
            print(f"--> [LOGIN ERREUR] {e}", flush=True)
            return (
                ctx,
                gr.update(value=f"❌ Erreur : {e}", visible=True),
                gr.update(visible=True),
                gr.update(visible=False),
            )

    btn_login.click(
        fn=on_login_submit,
        inputs=[app_state, si_email, si_pwd],
        outputs=[app_state, status, sign_in_container, homepage_container]
    )

    def on_register_submit(ctx, email, pwd, name, fname):
        print(f"--> [REGISTER] Création pour : {email} ({fname} {name})", flush=True)
        try:
            updated_ctx, msg = handle_register(ctx, email, pwd, name, fname)
            print(f"--> [REGISTER OK] !", flush=True)
            return (
                updated_ctx,
                gr.update(value=f"{msg}", visible=True),
                gr.update(visible=False),
                gr.update(visible=True),
            )
        except Exception as e:
            print(f"--> [REGISTER ERREUR] {e}", flush=True)
            return (
                ctx,
                gr.update(value=f"❌ Erreur : {e}", visible=True),
                gr.update(visible=True),
                gr.update(visible=False),
            )

    btn_register.click(
        fn=on_register_submit,
        inputs=[app_state, reg_email, reg_pwd, reg_name, reg_fname],
        outputs=[app_state, status, register_view, sign_in_container],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=global_theme,
        css=custom_css,
        share=False,
    )