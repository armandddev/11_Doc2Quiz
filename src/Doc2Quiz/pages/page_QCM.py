from pathlib import Path
import gradio as gr

def render_qcm_html(questions: list[dict]) -> str:
    """
    Génère l'HTML de revue du QCM avec la réponse correcte indiquée.
    Destiné à la page de relecture/correction par l'enseignant.
    """
    if not questions:
        return "<p style='text-align:center;color:#888;padding:60px'>Aucune question générée.</p>"

    mathjax = '''
    <script>
      MathJax = { tex: { inlineMath: [["$","$"],["\\\\(","\\\\)"]] } };
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
    '''

    parts = [mathjax, '<div style="max-width:820px;margin:0 auto;padding:20px 10px;">']

    for i, q in enumerate(questions):
        question_text  = (q.get("question") or "").replace("\n", "<br>")
        correct_letter = (q.get("correct") or "").strip().upper()
        options        = q.get("options", [])

        parts.append(f"""
        <div style="background:#f8f9fa;border-left:4px solid #1B57A1;
                    border-radius:8px;padding:20px 22px;margin-bottom:22px;
                    box-shadow:0 1px 4px rgba(0,0,0,.06);">
          <p style="font-weight:700;font-size:.9rem;color:#1B57A1;
                    margin:0 0 8px 0;text-transform:uppercase;letter-spacing:.05em;">
            Question {i + 1}
          </p>
          <p style="font-size:1.05rem;color:#111;margin:0 0 16px 0;line-height:1.5;">
            {question_text}
          </p>
          <div style="display:flex;flex-direction:column;gap:8px;">
        """)

        for opt in options:
            if not opt:
                continue
            letter     = opt[0].upper()
            is_correct = (letter == correct_letter)
            bg     = "#e8f4fd" if is_correct else "#ffffff"
            border = "#1B57A1" if is_correct else "#d1d5db"
            weight = "600"     if is_correct else "400"
            badge  = (
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

        parts.append("</div></div>")

    parts.append("</div>")
    return "".join(parts)


def render_QCM():
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

        # Spinner
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

            # Aperçu dynamique du QCM
            qcm_html_out = gr.HTML(value="", elem_id="qcm_preview")

            # Barre de correction
            with gr.Row(elem_id="correction_bar"):
                correction_input = gr.Textbox(
                    placeholder="Apporter une correction…",
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

            # Validation / passage à la suite
            with gr.Row(elem_id="widthPage"):
                btn_generate_ok = gr.Button(
                    "Aucune erreur / Correction détectée",
                    variant="secondary",
                    elem_id="buttonGenerateOK",
                )

    return (
        generateQCM_container,
        loading_section,
        qcm_section,
        qcm_html_out,
        btn_generate_ok,
        btn_submit_correction,
        correction_input,
        btn_back_QCM,
        btn_profil_QCM,
    )