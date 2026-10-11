import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Available models:")
for model in client.models.list():
    # Only show models that can process images and generate text
    if 'generateContent' in model.supported_actions:
        print(f"  - {model.name}")