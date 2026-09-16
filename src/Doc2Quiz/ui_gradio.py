import gradio as gr
from TemplateQuiz import get_template_quiz

####################
## STYLES GÉNÉRAL ##
####################

theme_global = gr.themes.Soft(
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
    margin-left: 25% !important;
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

.upload_docSujet {
    width: 60% !important;
    margin-left: 25% !important;
    background: transparent !important;
}

.upload_docSujet > .block,
.upload_docSujet .file-preview-holder,
.upload_docSujet [data-testid="file-upload"] {
    border: 1px solid #000000 !important;
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
    margin-left: 40% !important;
    background-color: green !important;
    color: white !important;
}

/* PAGE 2 : Choix du mode de révision */
.select-mode .wrap {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
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
    margin-left: 25% !important;
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
    margin-left: 25% !important;
    margin-bottom: 10px !important;
}

.bandeau-question {
    width: 50% !important;
    margin-left: 25% !important;
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
    align-items: center !important;
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
    margin-left: 25% !important;
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
    margin-left: 25% !important;
    background: transparent !important;
}

.champ-redaction textarea {
    border: 1.5px solid #000000 !important;
    border-radius: 4px !important;
    background-color: #ffffff !important;
    font-size: 1.05rem !important;
    padding: 12px !important;
}
"""

#######################
## Fonctions BackEnd ##
#######################
def choixDifficulte(choix):
    if choix == "Autres":
        return gr.update(visible=True)
    return gr.update(visible=False, value="")

def lancer_ChangementPage(matiere, upload_doc, difficulte, autre_precision):
    if not matiere or matiere.strip() == "":
        gr.Warning("Veuillez entrer le thème de votre matière.")
        return gr.update(), gr.update(), gr.update()

    if upload_doc is None:
        gr.Warning("Veuillez déposer un fichier.")
        return gr.update(), gr.update(), gr.update()

    if difficulte == "--Choisir la difficulté--":
        gr.Warning("Veuillez choisir la difficulté.")
        return gr.update(), gr.update(), gr.update()

    if difficulte == "Autres" and (not autre_precision or autre_precision.strip() == ""):
        gr.Warning("Veuillez préciser votre niveau.")
        return gr.update(), gr.update(), gr.update()

    return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)

def retour_PagePrecedente():
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)

def formater_html_question(num, enonce):
    return f"""
    <div class="bandeau-question">
        <div class="num-q">Question {num} -</div>
        <div class="texte-q">{enonce}</div>
    </div>
    """

def formater_choix(options_texte):
    lettres = ["A", "B", "C", "D"]
    return [f"{lettres[i]}. {opt}" for i, opt in enumerate(options_texte)]

def preparer_vue_question(q, num):
    html_q = formater_html_question(num, q["question"])

    if q["type"] == "qcm":
        choix = formater_choix(q["options"])
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

def initialiser_quiz(type_revision):
    questions = get_template_quiz(type_revision)

    premiere_q = questions[0]
    html_q, maj_qcm, maj_redaction = preparer_vue_question(premiere_q, 1)

    return (
        gr.update(visible=False),  # page_1
        gr.update(visible=False),  # page_2
        gr.update(visible=True),   # page_3
        questions,                 # liste_questions_state
        0,                         # idx_question_state
        0,                         # score_state
        html_q,                    # zone_question
        maj_qcm,                   # options_qcm
        maj_redaction,             # zone_redaction
        gr.update(value="Valider mon choix", visible=True),
        gr.update(visible=False),  # zone_resultat_final
    )

def etape_suivante_quiz(liste_questions, idx_actuel, score_actuel, rep_qcm, rep_redaction):
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
        html_s, maj_qcm, maj_redaction = preparer_vue_question(suivante, prochain_idx + 1)
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
    <div style="text-align: center; padding: 40px;">
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

######################
## Interface Gradio ##
######################
with gr.Blocks(title="11_Doc2Quiz", theme=theme_global, css=custom_css) as demo:
    gr.Markdown(
        """
        <h1 style="text-align: center; font-size: 300%; font-weight: 900; letter-spacing: 2%;">
            D O C <span style="color: #1e3a8a;">2</span> Q U I Z
        </h1>
        """
    )

    # PAGE 1 : Formulaire
    with gr.Column(visible=True) as page_1:
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown(
                    """
                    <p style="margin-left: 26%; padding: 0; font-size: 120%; color: gray;">
                        Sujet
                    </p>
                    """
                )
                matiereContent = gr.Textbox(
                    show_label=False,
                    placeholder="Entrer le thème de votre matière (ex: Histoire, Français, Mathématiques, etc.)",
                    lines=1,
                    elem_classes=["zone-matiere"],
                )

        upload_doc = gr.File(
            show_label=False,
            file_types=[".md", ".txt", ".pdf", ".docx"],
            elem_classes=["upload_docSujet"],
        )

        gr.HTML("<br>")

        difficulteContent = gr.Dropdown(
            show_label=False,
            value="--Choisir la difficulté--",
            interactive=True,
            choices=["--Choisir la difficulté--", "BUT", "Licence", "Prépa", "Master", "BTS", "Autres"],
            elem_classes=["zone-matiere"],
        )

        autre_precision = gr.Textbox(
            placeholder="Précisez votre niveau...",
            visible=False,
            show_label=False,
            interactive=True,
            lines=1,
            elem_classes=["zone-matiere"],
        )

        difficulteContent.change(
            fn=choixDifficulte,
            inputs=[difficulteContent],
            outputs=[autre_precision],
        )

        bouton_suivante = gr.Button(
            "Passer à l'étape suivante",
            elem_classes=["ButtonSuivante"],
        )

    # PAGE 2 : Choix de révision
    with gr.Column(visible=False) as page_2:
        gr.Markdown("<h2 style='text-align: center;'>Comment souhaitez vous réviser ?</h2>")

        typeQuiz = gr.Radio(
            choices=["Questions de cours", "Exercices", "Questions de cours & Exercices"],
            show_label=False,
            value="Questions de cours",
            interactive=True,
            elem_classes=["select-mode"],
        )

        gr.HTML("<div style='height: 1.5rem;'></div>")

        bouton_generer = gr.Button("Générer mon QCM", elem_classes=["btn-generer"])

        gr.HTML("<div style='height: 1rem;'></div>")

        bouton_retour_p2 = gr.Button("Retour", elem_classes=["ButtonSuivante"])

    # PAGE 3 : Questions une par une
    with gr.Column(visible=False) as page_3:
        liste_questions_state = gr.State([])
        idx_question_state = gr.State(0)
        score_state = gr.State(0)

        btn_quitter = gr.Button("← Quitter", elem_classes=["btn-quitter"])
        zone_question = gr.HTML()

        options_qcm = gr.Radio(
            choices=[],
            show_label=False,
            interactive=True,
            visible=False,
            elem_classes=["qcm-options"],
        )

        zone_redaction = gr.Textbox(
            show_label=False,
            placeholder="Écrivez votre réponse ici...",
            lines=3,
            visible=False,
            elem_classes=["champ-redaction"],
        )

        btn_valider_reponse = gr.Button(
            "Valider mon choix",
            elem_classes=["btn-valider"],
        )
        zone_resultat_final = gr.Markdown(visible=False)

    
    # Événements et Navigation
    bouton_suivante.click(
        fn=lancer_ChangementPage,
        inputs=[matiereContent, upload_doc, difficulteContent, autre_precision],
        outputs=[page_1, page_2, page_3],
    )

    bouton_retour_p2.click(
        fn=retour_PagePrecedente,
        inputs=[],
        outputs=[page_1, page_2, page_3],
    )

    btn_quitter.click(
        fn=retour_PagePrecedente,
        inputs=[],
        outputs=[page_1, page_2, page_3],
    )

    bouton_generer.click(
        fn=initialiser_quiz,
        inputs=[typeQuiz],
        outputs=[
            page_1,
            page_2,
            page_3,
            liste_questions_state,
            idx_question_state,
            score_state,
            zone_question,
            options_qcm,
            zone_redaction,
            btn_valider_reponse,
            zone_resultat_final,
        ],
    )

    btn_valider_reponse.click(
        fn=etape_suivante_quiz,
        inputs=[
            liste_questions_state,
            idx_question_state,
            score_state,
            options_qcm,
            zone_redaction,
        ],
        outputs=[
            idx_question_state,
            score_state,
            zone_question,
            options_qcm,
            zone_redaction,
            btn_valider_reponse,
            zone_resultat_final,
        ],
    )

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=3)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )