import docx
import pdfplumber

def extract_text(file_path):
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            return " ".join(page.extract_text() or "" for page in pdf.pages)

    if file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        return " ".join(p.text for p in doc.paragraphs)

    return ""
