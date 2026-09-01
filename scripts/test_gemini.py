
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
print(f"Key loaded: {key[:5]}...{key[-3:]} (Length: {len(key)})")

try:
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello, are you working?")
    print("SUCCESS: AI Responded")
    print(response.text)
except Exception as e:
    print(f"FAILURE: {e}")
