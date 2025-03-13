import requests
import fitz  # PyMuPDF
import pdfplumber

def download_pdf(url):
    """Downloads the PDF from a URL."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    return None

def extract_text_from_pdf(url):
    """Extracts text from a given PDF URL using PyMuPDF and pdfplumber."""
    pdf_data = download_pdf(url)
    if not pdf_data:
        return "Failed to download PDF."

    text = ""

    try:
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            text = "\n".join(page.get_text() for page in doc)
    except Exception:
        pass

    if not text:
        try:
            with pdfplumber.open(pdf_data) as pdf:
                text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        except Exception:
            return "Failed to extract text from PDF."

    return text if text else "No readable text found in PDF."
