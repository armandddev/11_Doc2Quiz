from pathlib import Path
import gradio as gr
from service.modif_service import corriger_question, modifier_question


def render_qcm_html(data, current_index: int = 0, total_questions: int = None) -> str:
    """
    Génère le rendu HTML du QCM.
    - Si 'data' est une liste : affiche la question située à 'current_index'.
    - Si 'data' est un dictionnaire : affiche cette question unique.
    """
    if not data:
        return "<p style='text-align:center;color:#888;padding:60px'>Aucune question générée.</p>"

    if isinstance(data, list):
        total = total_questions if total_questions is not None else len(data)
        if total == 0:
            return "<p style='text-align:center;color:#888;padding:60px'>Aucune question générée.</p>"
        idx = max(0, min(current_index, total - 1))
        question_data = data[idx]
    elif isinstance(data, dict):
        question_data = data
        idx = current_index
        total = total_questions if total_questions is not None else 1
    else:
        return "<p style='text-align:center;color:#888;padding:60px'>Format de question non reconnu.</p>"

    mathjax = '''
    <script>
      MathJax = { tex: { inlineMath: [["$","$"],["\\\\(","\\\\)"]] } };
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
    '''

    question_text = (question_data.get("question") or "").replace("\n", "<br>")
    options = question_data.get("options", [])

    correct_value = (
        question_data.get("bonne_reponse")
        or question_data.get("correct")
        or ""
    ).strip().upper()

    correct_letter = (
        correct_value[0]
        if correct_value and correct_value[0].isalpha()
        else ""
    )

    parts = [
        mathjax,
        '<div style="max-width:820px;margin:0 auto;padding:10px 10px;">',
        f"""
        <div style="background:#f8f9fa;border-left:4px solid #1B57A1;
                    border-radius:8px;padding:20px 22px;margin-bottom:20px;
                    box-shadow:0 1px 4px rgba(0,0,0,.06);">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <p style="font-weight:700;font-size:.9rem;color:#1B57A1;
                      margin:0;text-transform:uppercase;letter-spacing:.05em;">
              Question {idx + 1}
            </p>
            <span style="font-size:.85rem;color:#666;font-weight:600;">
              {idx + 1} / {total}
            </span>
          </div>
          <p style="font-size:1.05rem;color:#111;margin:0 0 16px 0;line-height:1.5;">
            {question_text}
          </p>
          <div style="display:flex;flex-direction:column;gap:8px;">
        """
    ]

    for opt in options:
        if not opt:
            continue
        letter = opt[0].upper()
        is_correct = (
            letter == correct_letter
            and (
                correct_value == letter
                or correct_value == opt.strip().upper()
            )
        )
        bg = "#e8f4fd" if is_correct else "#ffffff"
        border = "#1B57A1" if is_correct else "#d1d5db"
        weight = "600" if is_correct else "400"
        badge = (
            '<span style="float:right;background:#1B57A1;color:#fff;'
            'font-size:.72rem;padding:2px 9px;border-radius:12px;'
            'font-weight:600;letter-spacing:.03em;">✓ Correcte</span>'
            if is_correct else ""
        )
        parts.append(f"""
        <div style="background:{bg};border:1.5px solid {border};
                    border-radius:6px;padding:10px 14px;
                    font-size:.95rem;color:#222;font-weight:{weight};
                    line-height:1.4;">
          {opt}{badge}
        </div>
        """)

    parts.append("</div></div></div>")
    return "".join(parts)


def render_QCM():
    current_index = gr.State(value=0)
    questions_store = gr.State(value=[])

    with gr.Column(visible=False) as generateQCM_container:

        # En-tête
        with gr.Row():
            btn_back_QCM = gr.Button("← Retour", elem_id="btn_back")
            gr.HTML('''
                <div style="width:100%;text-align:center;margin:0 auto 20px auto;">
                    <h1 style="font-size:3rem;font-weight:800;letter-spacing:.35em;
                               color:#000;margin:0;text-align:center;">
                        DOC<span style="color:#1B57A1">2</span>QUIZ
                    </h1>
                </div>
            ''')
            btn_profil_QCM = gr.Button("👤 Mon profil", elem_id="btn_profil")

        # Spinner de chargement
        with gr.Column(visible=True) as loading_section:
            gr.HTML('''
                <style>
                  @keyframes d2q-spin { to { transform: rotate(360deg); } }
                  .d2q-spinner {
                    width: 64px; height: 64px;
                    border: 5px solid #dbe8f7;
                    border-top-color: #1B57A1;
                    border-radius: 50%;
                    animation: d2q-spin .85s linear infinite;
                    margin: 0 auto 28px auto;
                  }
                </style>
                <div style="text-align:center;padding:100px 20px;">
                  <div class="d2q-spinner"></div>
                  <p style="font-size:1.4rem;font-weight:600;color:#1B57A1;margin:0 0 10px 0;">
                    Génération du QCM en cours…
                  </p>
                  <p style="color:#666;font-size:.95rem;margin:0;">
                    Le modèle analyse votre document — merci de patienter.
                  </p>
                </div>
            ''')

        # Contenu QCM
        with gr.Column(visible=False) as qcm_section:

            gr.HTML('''
                <div style="width:100%;text-align:center;margin:20px auto 10px auto;">
                    <h2 style="font-size:1.8rem;color:#000;margin:0;">
                        Votre QCM est généré
                    </h2>
                </div>
            ''')

            # Aperçu HTML dynamique
            qcm_html_out = gr.HTML(value="", elem_id="qcm_preview")

            # Boutons de navigation
            with gr.Row():
                btn_prev_qcm = gr.Button("← Question précédente", variant="secondary")
                btn_next_qcm = gr.Button("Question suivante →", variant="secondary")

            # Barre de correction
            with gr.Row(elem_id="correction_bar"):
                correction_input = gr.Textbox(
                    placeholder="Apporter une correction à cette question…",
                    show_label=False,
                    container=False,
                    scale=9,
                    elem_id="correction_text",
                )
                btn_submit_correction = gr.Button(
                    "↑",
                    scale=1,
                    elem_id="btn_send_correction",
                )
            correction_status = gr.Markdown()

            # Validation / passage à la suite
            with gr.Row(elem_id="widthPage"):
                btn_generate_ok = gr.Button(
                    "Aucune erreur / Correction détectée",
                    variant="secondary",
                    elem_id="buttonGenerateOK",
                )

        # Callbacks de navigation
        def show_previous(idx, questions):
            if not questions:
                return 0, "<p style='text-align:center;color:#888;padding:60px'>Aucune question générée.</p>"
            new_idx = max(0, idx - 1)
            return new_idx, render_qcm_html(questions, new_idx, len(questions))

        def show_next(idx, questions):
            if not questions:
                return 0, "<p style='text-align:center;color:#888;padding:60px'>Aucune question générée.</p>"
            new_idx = min(len(questions) - 1, idx + 1)
            return new_idx, render_qcm_html(questions, new_idx, len(questions))

        btn_prev_qcm.click(
            fn=show_previous,
            inputs=[current_index, questions_store],
            outputs=[current_index, qcm_html_out]
        )
        btn_next_qcm.click(
            fn=show_next,
            inputs=[current_index, questions_store],
            outputs=[current_index, qcm_html_out]
        )

    # 10 éléments stricts pour correspondre à ui_gradio.py
    return (
        generateQCM_container,
        loading_section,
        qcm_section,
        qcm_html_out,
        btn_generate_ok,
        btn_submit_correction,
        correction_input,
        correction_status,
        btn_back_QCM,
        btn_profil_QCM,
    )