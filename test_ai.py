import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
# Gunakan ini, jangan hardcode API KEY di sini!
GOOGLE_API_KEY = os.environ.get('GEMINI_API_KEY') 
client = genai.Client(api_key=GOOGLE_API_KEY)