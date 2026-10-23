import gradio as gr

from Doc2Quiz.service.qcm_export import export_all, support_name_from_file

def make_download_buttons():
    gift_btn = gr.DownloadButton("Télécharger en GIFT (.txt)", visible=False)
    xml_btn = gr.DownloadButton("Télécharger en XML Moodle (.xml)", visible=False)
    return gift_btn, xml_btn


def refresh_download_buttons(questions, support_name: str):
    """Génère + valide GIFT et XML, puis met à jour les 2 boutons.
    Un format en échec (ou sans question exportable) -> son bouton reste masqué + toast."""
    if not questions:
        return gr.DownloadButton(visible=False), gr.DownloadButton(visible=False)

    result = export_all(questions, support_name or "qcm")

    for warning in result.warnings:
        gr.Warning(warning)
    for fmt, msg in result.errors.items():
        gr.Warning(f"Export {fmt.upper()} indisponible : {msg}")

    def btn(path):
        if path:
            return gr.DownloadButton(value=str(path), visible=True)
        return gr.DownloadButton(visible=False)

    return btn(result.gift_path), btn(result.xml_path)


def refresh_from_context(questions, app_context):
    """Variante écran de génération : le nom du support vient du fichier uploadé."""
    name = support_name_from_file(getattr(app_context, "pending_file", None))
    return refresh_download_buttons(questions, name)


def prepare_export(fmt, questions, app_context):
    key = (fmt or "").lower()
    if key not in ("gift", "xml", "pdf"):
        return gr.DownloadButton(value=None)
    if not questions:
        gr.Warning("Aucun QCM à exporter.")
        return gr.DownloadButton(value=None)

    name = support_name_from_file(getattr(app_context, "pending_file", None))
    result = export_all(questions, name, formats=(key,))

    for warning in result.warnings:
        gr.Warning(warning)
    if key in result.errors:
        gr.Warning(f"Export {fmt} impossible : {result.errors[key]}")

    path = {"gift": result.gift_path, "xml": result.xml_path, "pdf": result.pdf_path}[key]
    return gr.DownloadButton(value=str(path) if path else None)