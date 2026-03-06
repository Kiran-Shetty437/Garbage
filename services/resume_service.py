from google import genai
import pdfplumber
import docx
from config import GEMINI_API_KEY
import os

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in environment variables.")

client = genai.Client(api_key=GEMINI_API_KEY)

def extract_pdf_text(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text

def extract_docx_text(file):
    text = ""
    try:
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
    return text

def analyze_resume(text):
    prompt = f"""
    You are an AI Resume Analyzer.

    First determine if the document is a RESUME.

    A valid resume usually contains sections like:
    - Name
    - Contact information
    - Education
    - Skills
    - Projects / Experience

    If the document is NOT a resume (for example: project report, synopsis, article, notes),
    return only this message:

    "⚠️ This file does not appear to be a resume. Please upload a valid resume."

    If the document IS a resume, analyze it and return the result in this format:

    📌 Suitable Job Roles
    - Role 1
    - Role 2

    📌 Skills Found
    - Skill 1
    - Skill 2

    📌 Missing Skills to Learn
    - Skill 1
    - Skill 2

    📌 Resume Improvement Suggestions
    - Suggestion 1
    - Suggestion 2

    Keep each point concise and professional.

    Document:
    {text}
    """
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        return response.text
    except Exception as e:
        error_msg = str(e).upper()
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "QUOTA" in error_msg:
            return "⚠️ **Service is busy.** The AI analyzer has reached its free limit. Please wait about 60 seconds and try your analysis again."
        return f"Error analyzing resume: {str(e)}"
