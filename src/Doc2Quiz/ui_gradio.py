from pathlib import Path
import gradio as gr
from pages.page_register import render_register_page
from pages.page_sign_in import render_sign_in_page
from pages.page_homePage import render_homePage
from pages.page_revisionEtudiant import render_revisionEtudiant
from pages.page_QCM import render_QCM

css_file = Path(__file__).resolve().parent / "style.css"
custom_css = css_file.read_text(encoding="utf-8") if css_file.exists() else ""

global_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.blue,
    font=[gr.themes.GoogleFont("Roboto"), "sans-serif"],
)

with gr.Blocks(title="11_Doc2Quiz") as demo:
    homepage_container, upload_zone, difficulty_dropdown, revision_choice, btn_to_generate =  render_homePage()
    generateQCM_container, btn_generate_ok, btn_submit_correction, correction_input = render_QCM()
    register_view, btn_to_login = render_register_page()
    sign_in_view, btn_to_register = render_sign_in_page()
    revisionEtudiant_container = render_revisionEtudiant()

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

    btn_generate_ok.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        inputs=None,
        outputs=[generateQCM_container, revisionEtudiant_container]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=global_theme,
        css=custom_css,
        share=False,
    )