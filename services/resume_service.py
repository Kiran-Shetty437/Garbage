import re
import PyPDF2


def extract_resume(filepath):

    text = ""

    with open(filepath, "rb") as f:

        reader = PyPDF2.PdfReader(f)

        for page in reader.pages:
            text += page.extract_text()

    email = re.findall(r'\S+@\S+', text)

    return {
        "email": email[0] if email else None,
        "text": text
    }