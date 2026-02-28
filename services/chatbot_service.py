from google import genai
from config import GEMINI_API_KEY

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in environment variables.")

client = genai.Client(api_key=GEMINI_API_KEY)

def job_chatbot(user_input):
    prompt = f"""
You are a job assistant chatbot.

Rules:
- If greeting → reply greeting
- If job related → answer properly
- If NOT job related → reply EXACTLY:
Sorry, I answer only job related questions.

User: {user_input}
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error connecting to chatbot: {str(e)}"
