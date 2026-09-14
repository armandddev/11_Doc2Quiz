from shared.pdf import extractFromPdf, extractFromMd

def process_uploaded_pdf(file) -> str:
    filepath = file.name
    return extractFromPdf(filepath)

def process_uploaded_pdf(file) -> str:
    filepath = file.name
    return extractFromMd(filepath)