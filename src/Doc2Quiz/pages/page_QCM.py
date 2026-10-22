from pathlib import Path
import gradio as gr
from service.modif_service import corriger_question, modifier_question

# Mémoire globale des questions pour la session courante
_CURRENT_QUESTIONS = []


def render_qcm_html(data=None, current_index: int = 0, total_questions: int = None) -> str:
    """
    Rendu HTML du QCM :
    - Enregistre automatiquement les questions reçues dans _CURRENT_QUESTIONS.
    - Si current_index >= 0 : rend UNIQUEMENT cette question (mode pas-à-pas).
    - Si current_index est None ou < 0 : rend TOUTES les questions à la suite (vue globale).
    """
    global _CURRENT_QUESTIONS

    if data is not None and isinstance(data, list) and data:
        _CURRENT_QUESTIONS = data

    active_data = data if data is not None else _CURRENT_QUESTIONS
    if not active_data:
        return "<p style='text-align:center;color:#888;padding:60px'>Aucune question générée.</p>"

    # Détermination du mode : une seule question ou toutes
    if current_index is not None and current_index >= 0 and isinstance(active_data, list):
        total = total_questions or len(active_data)
        if total == 0:
            return "<p style='text-align:center;color:#888;padding:60px'>Aucune question générée.</p>"
        idx = max(0, min(current_index, total - 1))
        questions_to_render = [(idx, active_data[idx])]
    elif isinstance(active_data, list):
        questions_to_render = list(enumerate(active_data))
        total = len(active_data)
    else:
        questions_to_render = [(0, active_data)]
        total = 1

    mathjax = '''
    <script>
      MathJax = { tex: { inlineMath: [["$","$"],["\\\\(","\\\\)"]] } };
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
    '''

    parts = [mathjax, '<div style="max-width:820px;margin:0 auto;padding:10px 10px;">']

    for idx, q in questions_to_render:
        question_text = (q.get("question") or "").replace("\n", "<br>")
        options = q.get("options", [])

        new_badge = (
            '<span style="display:inline-block;background:#198754;color:#fff;'
            'font-size:.72rem;padding:3px 9px;border-radius:12px;'
            'margin-left:8px;">Question ajoutée</span>'
            if q.get("is_new") else ""
        )

        correct_value = (
            q.get("bonne_reponse")
            or q.get("correct")
            or ""
        ).strip().upper()

        correct_letter = (
            correct_value[0]
            if correct_value and correct_value[0].isalpha()
            else ""
        )

        parts.append(f"""
        <div style="background:#f8f9fa;border-left:4px solid #1B57A1;
                    border-radius:8px;padding:20px 22px;margin-bottom:20px;
                    box-shadow:0 1px 4px rgba(0,0,0,.06);">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <p style="font-weight:700;font-size:.9rem;color:#1B57A1;
                      margin:0;text-transform:uppercase;letter-spacing:.05em;">
              Question {idx + 1}{new_badge}
            </p>
            <span style="font-size:.85rem;color:#666;font-weight:600;">
              {idx + 1} / {total}
            </span>
          </div>
          <p style="font-size:1.05rem;color:#111;margin:0 0 16px 0;line-height:1.5;">
            {question_text}
          </p>
          <div style="display:flex;flex-direction:column;gap:8px;">
        """)

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

        parts.append("</div></div>")

    parts.append("</div>")
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

        # 1. Spinner (génération initiale)
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

        # 2 & 3. Section QCM
        with gr.Column(visible=False) as qcm_section:

            title_html = gr.HTML('''
                <div style="width:100%;text-align:center;margin:20px auto 10px auto;">
                    <h2 style="font-size:1.8rem;color:#000;margin:0;">
                        Votre QCM est généré
                    </h2>
                </div>
            ''')

            # Aperçu HTML dynamique (une question en Étape 2, toutes en Étape 3)
            qcm_html_out = gr.HTML(value="", elem_id="qcm_preview")

            # Barre de navigation pas-à-pas (Étape 2)
            with gr.Row() as nav_bar:
                btn_prev_qcm = gr.Button("← Question précédente", variant="secondary")
                btn_next_qcm = gr.Button("Question suivante →", variant="secondary")
                btn_validate_all = gr.Button("Valider toutes les questions ✓", variant="primary", visible=False)

            # Barre de correction ciblée (Étape 2)
            with gr.Row(elem_id="correction_bar") as correction_bar:
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

            # Bloc d'approfondissement (visible en Étape 3 pour ajouter des questions)
            with gr.Column(elem_id="expand_qcm", visible=False) as expand_section:
                gr.Markdown("### Approfondir le QCM")
                section_selector = gr.Dropdown(
                    choices=[],
                    label="Sections à approfondir (vide = toutes les sections)",
                    multiselect=True,
                    interactive=True,
                )
                btn_add_questions = gr.Button(
                    "Ajouter des questions",
                    variant="secondary",
                )
                expansion_status = gr.Markdown()

            # Actions finales de l'Étape 3
            with gr.Row(elem_id="widthPage", visible=False) as final_actions_row:
                btn_generate_ok = gr.Button(
                    "Exporter / Enregistrer le QCM",
                    variant="primary",
                    elem_id="buttonGenerateOK",
                )

        # Logique de navigation pas-à-pas (Étape 2)
        def navigate(idx_change, current_idx):
            global _CURRENT_QUESTIONS
            questions = _CURRENT_QUESTIONS
            if not questions:
                return 0, "<p style='text-align:center;'>Aucune question disponible.</p>", gr.update(), gr.update()

            total = len(questions)
            new_idx = max(0, min(current_idx + idx_change, total - 1))
            html = render_qcm_html(questions, current_index=new_idx, total_questions=total)

            is_last = (new_idx == total - 1)
            return (
                new_idx,
                html,
                gr.update(visible=not is_last),  # btn_next_qcm
                gr.update(visible=is_last)       # btn_validate_all
            )

        btn_prev_qcm.click(
            fn=lambda idx: navigate(-1, idx),
            inputs=[current_index],
            outputs=[current_index, qcm_html_out, btn_next_qcm, btn_validate_all]
        )

        btn_next_qcm.click(
            fn=lambda idx: navigate(1, idx),
            inputs=[current_index],
            outputs=[current_index, qcm_html_out, btn_next_qcm, btn_validate_all]
        )

        # Correction IA ponctuelle sur la question affichée (Étape 2)
        def apply_correction(idx, user_input):
            global _CURRENT_QUESTIONS
            if not _CURRENT_QUESTIONS or idx < 0 or idx >= len(_CURRENT_QUESTIONS):
                return "", "⚠️ Aucune question active."
            if not user_input or not user_input.strip():
                return "", "⚠️ Veuillez préciser une modification."
            try:
                # Simulation / intégration du service de correction
                q = _CURRENT_QUESTIONS[idx]
                modifs = modifier_question(
                    _CURRENT_QUESTIONS,
                    idx,
                    question=f"{q['question']} (revue)",
                    options=q["options"],
                    bonne_reponse=q.get("bonne_reponse", q["options"][0])
                )
                _CURRENT_QUESTIONS = modifs
                html = render_qcm_html(_CURRENT_QUESTIONS, current_index=idx, total_questions=len(_CURRENT_QUESTIONS))
                return html, "", "✅ Question modifiée avec succès !"
            except Exception as e:
                return render_qcm_html(_CURRENT_QUESTIONS, current_index=idx), user_input, f"❌ Erreur : {e}"

        btn_submit_correction.click(
            fn=apply_correction,
            inputs=[current_index, correction_input],
            outputs=[qcm_html_out, correction_input, correction_status]
        )

        # Étape 3 : Transition vers la vue récapitulative complète
        def switch_to_full_view():
            global _CURRENT_QUESTIONS
            full_html = render_qcm_html(_CURRENT_QUESTIONS, current_index=None)
            new_title = '''
                <div style="width:100%;text-align:center;margin:20px auto 10px auto;">
                    <h2 style="font-size:1.8rem;color:#000;margin:0;">
                        Récapitulatif complet du QCM
                    </h2>
                </div>
            '''
            return (
                full_html,
                new_title,
                gr.update(visible=False),  # nav_bar masquée
                gr.update(visible=False),  # correction_bar masquée
                gr.update(visible=True),   # expand_section affichée pour allonger le QCM
                gr.update(visible=True)    # final_actions_row affichée
            )

        btn_validate_all.click(
            fn=switch_to_full_view,
            inputs=None,
            outputs=[qcm_html_out, title_html, nav_bar, correction_bar, expand_section, final_actions_row]
        )

        # Réenclenchement de l'Étape 2 si on ajoute des questions depuis l'Étape 3
        def return_to_step_by_step():
            global _CURRENT_QUESTIONS
            total = len(_CURRENT_QUESTIONS)
            orig_title = '''
                <div style="width:100%;text-align:center;margin:20px auto 10px auto;">
                    <h2 style="font-size:1.8rem;color:#000;margin:0;">
                        Votre QCM est généré
                    </h2>
                </div>
            '''
            # Recommence au début ou sur les nouvelles questions
            first_idx = 0
            first_html = render_qcm_html(_CURRENT_QUESTIONS, current_index=first_idx, total_questions=total)
            return (
                first_idx,
                first_html,
                orig_title,
                gr.update(visible=True),   # nav_bar réaffichée
                gr.update(visible=True),   # btn_next_qcm réaffiché
                gr.update(visible=False),  # btn_validate_all masqué
                gr.update(visible=True),   # correction_bar réaffichée
                gr.update(visible=False),  # expand_section masquée pendant la revue
                gr.update(visible=False)   # final_actions_row masquée
            )

        btn_add_questions.click(
            fn=return_to_step_by_step,
            inputs=None,
            outputs=[
                current_index,
                qcm_html_out,
                title_html,
                nav_bar,
                btn_next_qcm,
                btn_validate_all,
                correction_bar,
                expand_section,
                final_actions_row
            ]
        )

    return (
        generateQCM_container,
        loading_section,
        qcm_section,
        qcm_html_out,
        btn_generate_ok,
        btn_submit_correction,
        correction_input,
        correction_status,
        section_selector,
        btn_add_questions,
        expansion_status,
        btn_back_QCM,
        btn_profil_QCM,
        questions_store,
        current_index,
    )