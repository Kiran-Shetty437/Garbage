from google import genai
from config import GEMINI_API_KEY

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in environment variables.")

client = genai.Client(api_key=GEMINI_API_KEY)

def job_chatbot(user_input):
    prompt = f"""
You are a job assistant chatbot. Your goal is to provide helpful, structured, and easy-to-read information about jobs, companies, and careers.

Rules:
- If greeting → reply greeting politely.
- If job related → provide a detailed answer in a structured way (using bullet points, bold headers, and clear sections).
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
        error_msg = str(e).upper()
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "QUOTA" in error_msg:
            return "⚠️ **Service is busy.** The AI has reached its free limit. Please try again in about 60 seconds."
        return f"Error connecting to chatbot: {str(e)}"
