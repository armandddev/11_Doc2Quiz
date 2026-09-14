import gradio as gr

############
## STYLES ##
############
theme_global = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.blue,
    font=[gr.themes.GoogleFont("Roboto"), "ui-sans-serif", "sans-serif"],
).set(
        input_border_color="black",  # Bordure noire
        input_border_width="1px",  # Épaisseur du cadre
    )


custom_css = """
/* Positionnement et style de la zone de saisie de la matière */
.zone-matiere {
    width: 60% ;
    margin-left: 25% ;
    background: transparent ;
    border: none ;
    box-shadow: none ;
}



/* Rend le conteneur de la colonne totalement transparent */
.gradio-container .block,
.gradio-container .form {
    background: transparent ;
    border: none ;
    box-shadow: none ;
}

.upload_doc {
    width: 70% ;
    margin-left: 20% ;
    background: transparent ;
}

.ButtonSuivante {
    width: 20% ;
    margin-left: 40% ;
    background-color: green ;
    color: white ;
}

/* Empilement vertical et centrage */
.select-mode .wrap {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 16px !important;
}

/* Style de base des cases (rectangle gris clair avec bordure noire) */
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

/* Texte à l'intérieur */
.select-mode label span {
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    color: #000000 !important;
}

/* Cache le rond radio natif */
.select-mode input[type="radio"] {
    display: none !important;
}

/* Case sélectionnée : fond jaune clair */
.select-mode label:has(input:checked),
.select-mode label.selected {
    background-color: #e8f0a0 !important;
}

/* Bouton vert du bas "Générer mon QCM" */
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
"""

#######################
## Fonctions BackEnd ##
#######################
def choixDifficulte(choix):
    if choix == "Autres":
        return gr.update(visible=True)
    return gr.update(visible=False, value="")

def lancer_ChangementPage(matiere, upload_doc, difficulte, autre_precision):
    # Vérification des champs vides, si champs vides --> message d'erreur (popup) et ne change pas de page
    if not matiere or matiere.strip() == "":
        gr.Warning("Veuillez entrer le thème de votre matière.")
        return gr.update(), gr.update()  

    if upload_doc is None:
        gr.Warning("Veuillez déposer un fichier.")
        return gr.update(), gr.update()

    if difficulte == "--Choisir la difficulté--":
        gr.Warning("Veuillez choisir la difficulté.")
        return gr.update(), gr.update()

    if difficulte == "Autres" and (
        not autre_precision or autre_precision.strip() == ""
    ):
        gr.Warning("Veuillez préciser votre niveau.")
        return gr.update(), gr.update()

    # Si aucune case vide --> page suivante
    return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)


def retour_PagePrecedente():
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)


def generer_QCM(matiere, upload_doc, difficulte, autre_precision, typeQuiz):
    gr.Info(f"QCM généré pour le sujet : {matiere}, difficulté : {difficulte}, type : {typeQuiz}")
    return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)





######################
## Interface Gradio ##
######################

## Zone du Texte général du haut
with gr.Blocks(title="11_Doc2Quiz", theme=theme_global, css=custom_css) as demo:
    gr.Markdown(
        """
        <h1 style="text-align: center; font-size: 300%; font-weight: 900; letter-spacing: 2%;">
            D O C <span style="color: #1e3a8a;">2</span> Q U I Z
        </h1>
        """
    )

    # ==========================================
    # PAGE 1 : Formulaire
    # ==========================================
    with gr.Column(visible=True) as page_1:
        ## Zone de saisie de la matière
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

        ## Zone de dépôt de fichier    
        upload_doc = gr.File(
            show_label=False,
            file_types=[".md", ".txt", ".pdf", ".docx"],
            elem_classes=["upload_doc"],
        )

        gr.HTML("<br>")


        ## Menu déroulant pour choisir le niveau des exercices
        difficulteContent = gr.Dropdown(
            show_label=False,
            value="--Choisir la difficulté--",
            interactive=True,
            choices=[
                "--Choisir la difficulté--",
                "BUT",
                "Licence",
                "Prépa",
                "Master",
                "BTS",
                "Autres",
            ],
            elem_classes=["zone-matiere"],
        )

        # Zone de texte masqué sauf quand "Autres" selectionné
        autre_precision = gr.Textbox(
            placeholder="Précisez votre niveau...",
            visible=False,
            show_label=False,
            interactive=True,
            lines=1,
            elem_classes=["zone-matiere"],
        )

        # Permet de rendre invisible la zone "Autre" quand l'utilisateur choisit une autre option que "Autres"
        difficulteContent.change(
            fn=choixDifficulte,
            inputs=[difficulteContent],
            outputs=[autre_precision],
        )



        bouton_suivante = gr.Button(
            "Passer à l'étape suivante",
            elem_classes=["ButtonSuivante"],
        )

    # ==========================================
    # PAGE 2 : Quiz / Validation
    # ==========================================
    with gr.Column(visible=False) as page_2:
        gr.Markdown(
            """
            <h2 style="text-align: center;">Comment souhaitez vous réviser ?</h2>
            """
        )

        typeQuiz = gr.Radio(
            choices=[
                "Questions de cours",
                "Exercices",
                "Questions de cours & Exercices",
            ],
            show_label=False,
            value="Exercices",  # Remplace "QCM" par "Exercices"
            interactive=True,
            elem_classes=["select-mode"],
        )

        bouton_generer = gr.Button(
            "Générer mon QCM",
            elem_classes=["btn-generer"],
        )

        bouton_retour_p2 = gr.Button(
            "Retour",
            elem_classes=["ButtonSuivante"],
        )



    # ==========================================
    # PAGE 3 : QCM
    # ==========================================
    with gr.Column(visible=False) as page_3:
        gr.Markdown(
            """
            <h2 style="text-align: center;">Votre QCM est prêt !</h2>
            """
        )

        gr.Markdown(
            """
            <p style="text-align: center; font-size: 120%; color: gray;">
                Vous pouvez maintenant télécharger votre QCM ou le réviser directement sur la plateforme.
            </p>
            """
        )

        bouton_retour_p3 = gr.Button(
            "Retour",
            elem_classes=["ButtonSuivante"],
        )

## Évènement de navigations des boutons
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

    bouton_retour_p3.click(
        fn=retour_PagePrecedente,
        inputs=[],
        outputs=[page_1, page_2, page_3],
    )

    bouton_generer.click(
        fn=generer_QCM,
        inputs=[matiereContent, upload_doc, difficulteContent, autre_precision, typeQuiz],
        outputs=[page_1, page_2, page_3],
    )




###########################
## Lancement Application ##
###########################
if __name__ == "__main__":
    demo.queue(default_concurrency_limit=3)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )