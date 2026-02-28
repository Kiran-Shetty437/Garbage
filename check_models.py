from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEY is not set.")
    exit(1)

client = genai.Client(api_key=api_key)

try:
    print("Available Models:")
    # Trying models.list() as per common SDK patterns
    models = client.models.list()
    for model in models:
        print(f"- {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")
