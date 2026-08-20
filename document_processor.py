from docx import Document
import PyPDF2

from llm_service import extract_image_text


def create_chunks(text, chunk_size=1000):

    chunks = []

    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])

    return chunks


def extract_pdf_text(file):

    text = ""

    reader = PyPDF2.PdfReader(file)

    for page in reader.pages:

        extracted = page.extract_text()

        if extracted:
            text += extracted + "\n"

    return text


def extract_txt_text(file):

    return file.read().decode("utf-8") + "\n"


def extract_docx_text(file):

    text = ""

    document = Document(file)

    for para in document.paragraphs:

        text += para.text + "\n"

    return text


def extract_text_from_file(file):

    filename = file.filename.lower()

    if filename.endswith(".pdf"):

        return extract_pdf_text(file)

    elif filename.endswith(".txt"):

        return extract_txt_text(file)

    elif filename.endswith(".docx"):

        return extract_docx_text(file)

    elif filename.endswith(
        (".png", ".jpg", ".jpeg", ".webp")
    ):

        return extract_image_text(file) + "\n"

    else:

        raise ValueError(
            f"Unsupported file type: {file.filename}"
        )