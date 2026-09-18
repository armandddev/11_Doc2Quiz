import gradio as gr
from Template.TemplateQuiz import *
from Template.TemplateProfil import *
from mock_profil import *

####################
## STYLES GÉNÉRAL ##
####################

global_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.blue,
    font=[gr.themes.GoogleFont("Roboto"), "ui-sans-serif", "sans-serif"],
).set(
    input_border_color="black",
    input_border_width="1px",
)

custom_css = """
/* PAGE 1 : Page d'accueil */
.zone-matiere {
    width: 60% !important;
    margin-left: 15% !important;
    background: transparent !important;
    box-shadow: none !important;
}

.zone-matiere textarea,
.zone-matiere input,
.zone-matiere > .block,
.zone-matiere .wrap {
    border: 1px solid #000000 !important;
    background-color: #ffffff !important;
}

.zone-matiere ul {
    z-index: 9999 !important;
}

.document_uploadSujet {
    width: 60% !important;
    margin-left: 15% !important;
    background: transparent !important;
    border: 2px dashed #000000 !important;
}

.document_uploadSujet > .block,
.document_uploadSujet .file-preview-holder,
.document_uploadSujet [data-testid="file-upload"] {
    border-radius: 4px !important;
    background-color: #ffffff !important;
}

.gradio-container .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

.ButtonSuivante {
    width: 20% !important;
    align-items: center !important;
    margin-left: 34% !important;
    background-color: green !important;
    color: white !important;
}

.ButtonRetour {
    width: 20% !important;
    align-items: center !important;
    margin-left: 31% !important;
    background-color: green !important;
    color: white !important;
}

/* PAGE 2 : Choix du mode de révision */
.select-mode .wrap {
    display: flex !important;
    flex-direction: column !important;
    padding-left: 20% !important;
    gap: 16px !important;
}

.select-mode label {
    width: 50% !important;
    min-height: 55px !important;
    background-color: #d9d9d9 !important;
    border: 1.5px solid #000000 !important;
    border-radius: 4px !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    cursor: pointer !important;
    transition: background-color 0.2s ease !important;
}

.select-mode label span {
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    color: #000000 !important;
}

.select-mode input[type="radio"] {
    display: none !important;
}

.select-mode label:has(input:checked),
.select-mode label.selected {
    background-color: #e8f0a0 !important;
}

.btn-generer {
    width: 50% !important;
    margin-left: 15% !important;
    height: 55px !important;
    background-color: #6ee787 !important;
    color: #000000 !important;
    border: 1.5px solid #000000 !important;
    border-radius: 4px !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
}

/* PAGE 3 : Questionnaire QCM & Exercices */
.btn-quitter {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    font-size: 1rem !important;
    color: #4b5563 !important;
    cursor: pointer !important;
    width: auto !important;
    text-align: left !important;
    padding: 0 !important;
    margin-left: 15% !important;
    margin-bottom: 10px !important;
}

.bandeau-question {
    width: 50% !important;
    margin-left: 15% !important;
    background-color: #8195cf !important;
    border-radius: 4px !important;
    padding: 20px 24px !important;
    text-align: center !important;
    box-sizing: border-box !important;
    margin-bottom: 30px !important;
}

.bandeau-question .num-q {
    color: #4a5d91;
    font-size: 1rem;
    font-weight: 500;
    margin-bottom: 6px;
}

.bandeau-question .texte-q {
    color: #000000;
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
    white-space: pre-line;
}

.qcm-options .wrap {
    display: flex !important;
    flex-direction: column !important;
    padding-left: 20% !important;
    gap: 16px !important;
}

.qcm-options label {
    width: 50% !important;
    min-height: 58px !important;
    background-color: #d9d9d9 !important;
    border: 1.5px solid #000000 !important;
    border-radius: 0px !important;
    display: flex !important;
    align-items: center !important;
    padding: 0 20px !important;
    cursor: pointer !important;
    box-sizing: border-box !important;
    transition: background-color 0.15s ease !important;
}

.qcm-options input[type="radio"] {
    display: none !important;
}

.qcm-options label span {
    font-size: 1.15rem !important;
    font-weight: 500 !important;
    color: #000000 !important;
    width: 100% !important;
    text-align: center !important;
}

.qcm-options label:has(input:checked),
.qcm-options label.selected {
    background-color: #cbd5e1 !important;
    border: 2px solid #1e3a8a !important;
}

.btn-valider {
    width: 50% !important;
    margin-left: 15% !important;
    height: 52px !important;
    background-color: #6ee787 !important;
    color: #000000 !important;
    border: 1.5px solid #000000 !important;
    border-radius: 2px !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    margin-top: 25px !important;
}

.champ-redaction {
    width: 50% !important;
    margin-left: 15% !important;
    background: transparent !important;
}

.champ-redaction textarea {
    border: 1.5px solid #000000 !important;
    border-radius: 4px !important;
    background-color: #ffffff !important;
    font-size: 1.05rem !important;
    padding: 12px !important;
}


/* PAGE 4 : Consultation du profil */
.profil-wrapper {
    width: 65% !important;
    margin: 0 auto !important;
}

.titre-page-profil {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    color: #111827 !important;
    margin-bottom: 24px !important;
}

.card-profil {
    background-color: #d9d9d9 !important;
    border: 1.5px solid #000000 !important;
    padding: 24px 30px !important;
    margin-bottom: 24px !important;
    box-sizing: border-box !important;
}

.entete-profil {
    display: flex !important;
    align-items: center !important;
    gap: 20px !important;
}

.avatar-profil {
    width: 62px !important;
    height: 62px !important;
    background-color: #8db5e2 !important;
    border: 1.5px solid #000000 !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    color: #1e3a8a !important;
    flex-shrink: 0 !important;
}

.infos-utilisateur {
    flex-grow: 1 !important;
}

.nom-user {
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    color: #000000 !important;
}

.filiere-user {
    font-size: 1rem !important;
    color: #111827 !important;
    margin: 3px 0 !important;
}

.meta-user {
    font-size: 0.95rem !important;
    color: #4b5563 !important;
}

.btn-modifier-profil {
    background-color: #b5b5b5 !important;
    border: 1.5px solid #000000 !important;
    padding: 12px 30px !important;
    font-size: 1.1rem !important;
    font-weight: 500 !important;
    cursor: default !important;
}

.titre-section {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #000000 !important;
    margin-bottom: 20px !important;
}

.liste-competences {
    display: flex !important;
    flex-direction: column !important;
    gap: 20px !important;
}

.header-competence {
    display: flex !important;
    justify-content: space-between !important;
    margin-bottom: 6px !important;
}

.titre-domaine {
    font-size: 1.05rem !important;
    color: #000000 !important;
}

.pct-domaine {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
}

.barre-fond {
    width: 100% !important;
    height: 12px !important;
    background-color: #8b95a5 !important;
    border: 1px solid #4b5563 !important;
}

.barre-progression {
    height: 100% !important;
}

.zone-danger-cadre {
    border: 1.5px solid #f87171 !important;
    background-color: #e5e5e5 !important;
    padding: 24px 30px !important;
    box-sizing: border-box !important;
}

.titre-danger {
    color: #ef4444 !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    margin-bottom: 16px !important;
}

.ligne-suppression {
    background-color: #d9d9d9 !important;
    border: 1px solid #737373 !important;
    padding: 12px 20px !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-bottom: 14px !important;
}

.ligne-suppression:last-child {
    margin-bottom: 0 !important;
}

.texte-action {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: #000000 !important;
}

.texte-desc {
    font-size: 0.9rem !important;
    color: #525252 !important;
}

.btn-suppr-contour {
    background: transparent !important;
    border: 1.5px solid #ef4444 !important;
    color: #ef4444 !important;
    font-weight: 600 !important;
    padding: 8px 18px !important;
    cursor: default !important;
}

.btn-suppr-plein {
    background-color: #ef4444 !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    padding: 9px 18px !important;
    cursor: default !important;
}

.btn-vers-profil {
    max-width: 140px !important;
    height: 42px !important;
    margin-top: 10px !important;
    background-color: #e5e7eb !important;
    border: 1px solid #000000 !important;
    font-weight: 600 !important;
}
"""

#######################
## Fonctions BackEnd ##
#######################
def chooseDifficulte(choix):
    if choix == "Autres":
        return gr.update(visible=True)
    return gr.update(visible=False, value="")

def navigate_to_page_2(document_upload, difficulte, custom_level_input):
    if document_upload is None:
        gr.Warning("Veuillez déposer un fichier.")
        return gr.update(), gr.update(), gr.update()

    if difficulte == "--Choisir la difficulté--":
        gr.Warning("Veuillez choisir la difficulté.")
        return gr.update(), gr.update(), gr.update()

    if difficulte == "Autres" and (not custom_level_input or custom_level_input.strip() == ""):
        gr.Warning("Veuillez préciser votre niveau.")
        return gr.update(), gr.update(), gr.update()

    return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)

def navigate_to_home():
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)

def format_question_html(num, enonce):
    return f"""
    <div class="bandeau-question">
        <div class="num-q">Question {num} -</div>
        <div class="texte-q">{enonce}</div>
    </div>
    """

def format_radio_choices(options_texte):
    lettres = ["A", "B", "C", "D"]
    return [f"{lettres[i]}. {opt}" for i, opt in enumerate(options_texte)]

def build_question_view(q, num):
    html_q = format_question_html(num, q["question"])

    if q["type"] == "qcm":
        choix = format_radio_choices(q["options"])
        return (
            html_q,
            gr.update(choices=choix, value=None, visible=True),
            gr.update(value="", visible=False),
        )
    else:
        nb_lignes = q.get("lignes", 4)
        ph = q.get("placeholder", "Écrivez votre réponse ici...")
        return (
            html_q,
            gr.update(choices=[], value=None, visible=False),
            gr.update(value="", placeholder=ph, lines=nb_lignes, visible=True),
        )

def start_quiz_session(type_revision):
    questions = get_template_quiz(type_revision)

    premiere_q = questions[0]
    html_q, maj_qcm, maj_redaction = build_question_view(premiere_q, 1)

    return (
        gr.update(visible=False),  # page_1
        gr.update(visible=False),  # page_2
        gr.update(visible=True),   # page_3
        questions,                 # questions_state
        0,                         # current_index_state
        0,                         # current_score_state
        html_q,                    # question_display
        maj_qcm,                   # qcm_radio_choices
        maj_redaction,             # free_text_response
        gr.update(value="Valider mon choix", visible=True),
        gr.update(visible=False),  # final_score_display
    )

def submit_and_next_question(liste_questions, idx_actuel, score_actuel, rep_qcm, rep_redaction):
    q_actuelle = liste_questions[idx_actuel]
    est_qcm = q_actuelle["type"] == "qcm"

    rep = rep_qcm if est_qcm else rep_redaction
    if not rep or str(rep).strip() == "":
        gr.Warning("Veuillez renseigner une réponse avant de continuer !")
        return idx_actuel, score_actuel, gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    nouveau_score = score_actuel
    if est_qcm:
        texte_choisi = rep_qcm.split(". ", 1)[1] if ". " in rep_qcm else rep_qcm
        if texte_choisi == q_actuelle["bonne_reponse"]:
            nouveau_score += 1
    else:
        nouveau_score += 1

    prochain_idx = idx_actuel + 1

    if prochain_idx < len(liste_questions):
        suivante = liste_questions[prochain_idx]
        html_s, maj_qcm, maj_redaction = build_question_view(suivante, prochain_idx + 1)
        return (
            prochain_idx,
            nouveau_score,
            html_s,
            maj_qcm,
            maj_redaction,
            gr.update(value="Valider mon choix", visible=True),
            gr.update(visible=False),
        )

    bilan = f"""
    <div style="padding-left: 31%;">
        <h2>Session terminée !</h2>
        <p style="font-size: 1.4rem; font-weight: 600;">
            Score obtenu : {nouveau_score} / {len(liste_questions)}
        </p>
    </div>
    """
    return (
        prochain_idx,
        nouveau_score,
        "",
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(value=bilan, visible=True),
    )


# Prépare les templates avec les mocks.
user_initials = "".join(
    [m[0] for m in MOCK_UTILISATEUR["nom"].split()[:2]]
).upper()

rendered_header_html = TEMPLATE_ENTETE.format(
    initiales=user_initials,
    nom=MOCK_UTILISATEUR["nom"],
    formation=MOCK_UTILISATEUR["formation"],
    etablissement=MOCK_UTILISATEUR["etablissement"],
    date_inscription=MOCK_UTILISATEUR["date_inscription"],
    nb_sessions=MOCK_UTILISATEUR["nb_sessions"],
)

rendered_skills_html = "".join(
    [
        TEMPLATE_LIGNE_COMPETENCE.format(
            domaine=comp["domaine"],
            score=comp["score"],
            couleur=comp["couleur"],
        )
        for comp in MOCK_COMPETENCES
    ]
)
rendered_skills_wrapper_html = TEMPLATE_COMPETENCES_WRAPPER.format(
    lignes_competences=rendered_skills_html
)

STATIC_DANGER_ZONE_HTML = """
<div class="zone-danger-cadre">
    <div class="titre-danger">Zone de suppression</div>
    <div class="ligne-suppression">
        <div>
            <div class="texte-action">Supprimer l'historique</div>
            <div class="texte-desc">Supprimes toutes vos sessions précédentes (18 sessions)</div>
        </div>
        <button class="btn-suppr-contour">Supprimer</button>
    </div>
    <div class="ligne-suppression">
        <div>
            <div class="texte-action">Supprimer mon profil</div>
            <div class="texte-desc">Supprime définitivement le profil, les données et l'histoirique</div>
        </div>
        <button class="btn-suppr-plein">Supprimer le profil</button>
    </div>
</div>
"""

######################
## Interface Gradio ##
######################
with gr.Blocks(title="11_Doc2Quiz", theme=global_theme, css=custom_css) as demo:
    with gr.Row():
        gr.Markdown(
            """
            <h1 style="text-align: center; font-size: 300%; font-weight: 900; letter-spacing: 2%; margin: 0 auto;">
                D O C <span style="color: #1e3a8a;">2</span> Q U I Z
            </h1>
            """
        )
        btn_goto_profile = gr.Button(
                    "👤 Mon profil", elem_classes=["btn-vers-profil"]
                )

    # PAGE 1 : Formulaire
    with gr.Column(visible=True) as page_1:
        document_upload = gr.File(
            show_label=False,
            file_types=[".md", ".txt", ".pdf", ".docx"],
            elem_classes=["document_uploadSujet"],
        )

        gr.HTML("<br>")

        difficulty_dropdown = gr.Dropdown(
            show_label=False,
            value="--Choisir la difficulté--",
            interactive=True,
            choices=["--Choisir la difficulté--", "BUT", "Licence", "Prépa", "Master", "BTS", "Autres"],
            elem_classes=["zone-matiere"],
        )

        custom_level_input = gr.Textbox(
            placeholder="Précisez votre niveau...",
            visible=False,
            show_label=False,
            interactive=True,
            lines=1,
            elem_classes=["zone-matiere"],
        )

        difficulty_dropdown.change(
            fn=chooseDifficulte,
            inputs=[difficulty_dropdown],
            outputs=[custom_level_input],
        )

        btn_next_step = gr.Button(
            "Passer à l'étape suivante",
            elem_classes=["ButtonSuivante"],
        )

    # PAGE 2 : Choix de révision
    with gr.Column(visible=False) as page_2:
        gr.Markdown("<h2 style='padding-left: 23%'>Comment souhaitez vous réviser ?</h2>")

        quiz_mode_radio = gr.Radio(
            choices=["Questions de cours", "Exercices", "Questions de cours & Exercices"],
            show_label=False,
            value="Questions de cours",
            interactive=True,
            elem_classes=["select-mode"],
        )

        gr.HTML("<div style='height: 1.5rem;'></div>")

        bouton_generer = gr.Button("Générer mon QCM", elem_classes=["btn-generer"])

        gr.HTML("<div style='height: 1rem;'></div>")

        btn_back_p2 = gr.Button("Retour", elem_classes=["ButtonRetour"])

    # PAGE 3 : Questions une par une
    with gr.Column(visible=False) as page_3:
        questions_state = gr.State([])
        current_index_state = gr.State(0)
        current_score_state = gr.State(0)

        btn_quit_quiz = gr.Button("← Quitter", elem_classes=["btn-quitter"])
        question_display = gr.HTML()

        qcm_radio_choices = gr.Radio(
            choices=[],
            show_label=False,
            interactive=True,
            visible=False,
            elem_classes=["qcm-options"],
        )

        free_text_response = gr.Textbox(
            show_label=False,
            placeholder="Écrivez votre réponse ici...",
            lines=3,
            visible=False,
            elem_classes=["champ-redaction"],
        )

        btn_submit_answer = gr.Button(
            "Valider mon choix",
            elem_classes=["btn-valider"],
        )
        final_score_display = gr.Markdown(visible=False)


    # PAGE 4 : Profil
    with gr.Column(
        visible=False, elem_classes=["profil-wrapper"]
    ) as page_profile:
        btn_back_from_profile = gr.Button(
            "← Revenir au générateur", elem_classes=["btn-quitter"]
        )
        gr.HTML('<div class="titre-page-profil">Mon profil</div>')
        gr.HTML(rendered_header_html)
        gr.HTML(rendered_skills_wrapper_html)
        gr.HTML(STATIC_DANGER_ZONE_HTML)
    
    # ==========================================
    # Événements et Navigation
    # ==========================================

    # Navigation entre les étapes du générateur
    btn_next_step.click(
        fn=navigate_to_page_2,
        inputs=[document_upload, difficulty_dropdown, custom_level_input],
        outputs=[page_1, page_2, page_3],
    )

    btn_back_p2.click(
        fn=navigate_to_home,
        inputs=[],
        outputs=[page_1, page_2, page_3],
    )

    btn_quit_quiz.click(
        fn=navigate_to_home,
        inputs=[],
        outputs=[page_1, page_2, page_3],
    )

    # Lancement du quiz avec le type de révision sélectionné
    bouton_generer.click(
        fn=start_quiz_session,
        inputs=[quiz_mode_radio],
        outputs=[
            page_1,
            page_2,
            page_3,
            questions_state,
            current_index_state,
            current_score_state,
            question_display,
            qcm_radio_choices,
            free_text_response,
            btn_submit_answer,
            final_score_display,
        ],
    )

    # Progression dans les questions (QCM ou rédaction)
    btn_submit_answer.click(
        fn=submit_and_next_question,
        inputs=[
            questions_state,
            current_index_state,
            current_score_state,
            qcm_radio_choices,
            free_text_response,
        ],
        outputs=[
            current_index_state,
            current_score_state,
            question_display,
            qcm_radio_choices,
            free_text_response,
            btn_submit_answer,
            final_score_display,
        ],
    )

    # Navigation vers le Profil
    btn_goto_profile.click(
        fn=lambda: (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
        ),
        inputs=[],
        outputs=[page_1, page_2, page_3, page_profile],
    )

    # Retour à l'accueil depuis le Profil
    btn_back_from_profile.click(
        fn=lambda: (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        ),
        inputs=[],
        outputs=[page_1, page_2, page_3, page_profile],
    )

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=3)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )