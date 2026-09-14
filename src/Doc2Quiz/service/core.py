from shared.pdf import extractFromPdf

def process_uploaded_pdf(file) -> str:
    filepath = file.name
    return extractFromPdf(filepath)