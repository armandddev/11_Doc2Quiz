from pathlib import Path
import gradio as gr

def render_homePage():
    with gr.Column(visible=True) as homepage_container:
        with gr.Row():
            gr.HTML('''
                <div style="width: 100%; text-align: center; margin: 0px auto 20px auto;">
                    <h1 style="font-size: 3rem !important; font-weight: 800 !important; letter-spacing: 0.35em !important; color: #000000 !important; margin: 0 !important; text-align: center !important;">
                        DOC<span style ="color: #1B57A1">2</span>QUIZ
                    </h1>
                </div>
            ''')

            btn_profil_homePage = gr.Button(
                "👤 Mon profil",
                elem_id="btn_profil"
            )

        with gr.Row(elem_id="main_grid"):
            with gr.Column(scale=3):
                upload_zone = gr.File(
                    show_label=False,
                    file_count="single",
                    elem_id="file_upload_zone"
                )

            with gr.Column(scale=1, elem_id="revision_box"):
                gr.HTML('<h2 class="revision-title">Révision</h2>')
                revision_choice = gr.Radio(
                    choices=["Question de cours", "Exercices", "Les deux"],
                    value="Question de cours",
                    show_label=False,
                    interactive = True,
                    elem_id="revision_options"
                )

        with gr.Row(elem_id="widthPage"):
            difficulty_dropdown = gr.Dropdown(
                label = "Difficulté",
                choices=["---- CHOISIR ----","BUT", "BTS", "Licence", "École d'Ingénieur"],
                value="---- CHOISIR ----",                  
                interactive = True,
                elem_id= "ChoiceDifficulty"
            )

        with gr.Row(elem_id="widthPage"):
            btn_to_generate = gr.Button(
                "Générer le QCM",
                variant="secondary",
                elem_id="buttonCreateAccount"
            )


    return homepage_container, upload_zone, difficulty_dropdown, revision_choice, btn_to_generate, btn_profil_homePage



