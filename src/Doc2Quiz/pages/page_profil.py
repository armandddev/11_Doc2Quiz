import gradio as gr


def render_profil():
  with gr.Column(visible=False) as profil_container:
    with gr.Row(elem_id="training_header_row"):
      gr.HTML(
          """
                <div style="width: 100%; text-align: center;">
                    <h1 style="font-size: 3rem; font-weight: 800; letter-spacing: 0.35em; color: #000000; margin: 0;">
                        DOC<span style="color: #1B57A1">2</span>QUIZ
                    </h1>
                </div>
                """
      )
      btn_profil_trainingQuiz = gr.Button(
          "👤 Mon profil", elem_id="btn_profil"
      )

    btn_quit = gr.Button("← Revenir au générateur", elem_id="btn_quit_quiz")

    profil_title_html = gr.HTML(
        """
            <div style="margin: 20px 0 15px 0;">
                <h1 style="font-size: 2.8rem; font-weight: 700; color: #000000; margin: 0; line-height: 1.1;">
                    Mon profil
                </h1>
                <p style="font-size: 1.1rem; color: #000000; margin: 6px 0 0 0; font-weight: 400;">
                    Statut - Chargement...
                </p>
            </div>
            """,
        elem_id="profil_title_section",
    )

    # 1. Vue d'affichage normale du profil
    with gr.Column(visible=True) as view_profile_box:
      with gr.Row(elem_id="user_card_container"):
        user_info_html = gr.HTML(
            """
                    <div class="user-id-left">
                        <div class="user-avatar">--</div>
                        <div class="user-details">
                            <h2 class="user-fullname">Chargement du profil...</h2>
                            <p class="user-meta">Récupération des données...</p>
                        </div>
                    </div>
                    """,
            elem_id="user_info_section",
        )
        btn_edit_profile = gr.Button("Modifier", elem_id="btn_edit_profile")

      with gr.Column(elem_id="danger_zone_container"):
        gr.HTML(
            '<h3 style="color: #ef4444; font-size: 1.15rem; font-weight: 600;'
            ' margin: 0 0 16px 0;">Zone de suppression</h3>'
        )

        with gr.Row(
            elem_id="row_danger_history", elem_classes=["danger-box-row"]
        ):
          history_info_html = gr.HTML(
              """
                        <div>
                            <h4 style="margin: 0; font-size: 1rem; font-weight: 600; color: #1f2937;">Supprimer l'historique</h4>
                            <p style="margin: 4px 0 0 0; font-size: 0.875rem; color: #6b7280;">Supprime toutes vos sessions précédentes (-- sessions)</p>
                        </div>
                        """
          )
          btn_delete_history = gr.Button(
              "Supprimer", elem_id="btn_delete_history", variant="secondary"
          )

        with gr.Row(
            elem_id="row_danger_profile", elem_classes=["danger-box-row"]
        ):
          gr.HTML("""
                        <div>
                            <h4 style="margin: 0; font-size: 1rem; font-weight: 600; color: #1f2937;">Supprimer mon profil</h4>
                            <p style="margin: 4px 0 0 0; font-size: 0.875rem; color: #6b7280;">Supprime définitivement le profil, les données et l'historique</p>
                        </div>
                        """)
          btn_delete_profile = gr.Button(
              "Supprimer le profil",
              elem_id="btn_delete_profile",
              variant="stop",
          )

    # 2. Formulaire de modification (masqué par défaut)
    with gr.Column(
        visible=False, elem_id="edit_profile_container"
    ) as edit_profile_box:
      gr.HTML(
          '<h3 style="font-size: 1.25rem; font-weight: 600; margin: 0 0 15px'
          ' 0; color: #1f2937;">Modifier mes informations</h3>'
      )
      with gr.Row():
        edit_fname = gr.Textbox(label="Prénom*", elem_id="edit_fname")
        edit_name = gr.Textbox(label="Nom*", elem_id="edit_name")
      edit_email = gr.Textbox(label="Adresse e-mail*", elem_id="edit_email")
      edit_pwd = gr.Textbox(
          label="Nouveau mot de passe (laisser vide pour conserver l'actuel)",
          type="password",
          elem_id="edit_pwd",
      )

      with gr.Row():
        btn_save_profile = gr.Button(
            "Enregistrer les modifications",
            variant="primary",
            elem_id="btn_save_profile",
        )
        btn_cancel_edit = gr.Button(
            "Annuler", variant="secondary", elem_id="btn_cancel_edit"
        )

  return (
      profil_container,
      btn_quit,
      profil_title_html,
      user_info_html,
      btn_edit_profile,
      history_info_html,
      btn_delete_history,
      btn_delete_profile,
      view_profile_box,
      edit_profile_box,
      edit_fname,
      edit_name,
      edit_email,
      edit_pwd,
      btn_save_profile,
      btn_cancel_edit,
  )