"""
Gemini-based OCR. Uses Google's multimodal model to read prescriptions.
Permanent fix: reads ANY handwriting, not just training data.
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# The prompt instructs Gemini to act as a prescription OCR engine
PRESCRIPTION_PROMPT = """You are a medical prescription OCR system.
Extract ONLY the drug names written in this prescription image.

Rules:
- Return ONLY a Python list of drug names, like: ["Augmentin", "Enzoflam", "Pan-D"]
- Ignore: doctor names, patient names, dates, addresses, clinic names, dosages (like "625mg"), frequencies (like "1-0-1"), and instructions (like "after meals").
- Preserve the original spelling as written (e.g., "Augmentin" not "Amoxicillin").
- If no drug names are found, return an empty list: []

Output ONLY the Python list. No explanations, no extra text."""


class GeminiOCR:
    """OCR using Google Gemini API."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in .env file")

        self.client = genai.Client(api_key=api_key)
        # Use the fast, free-tier friendly model
        self.model = "gemini-3.8-flash"
        print(f"✅ Gemini OCR ready (model: {self.model})")

    def extract_drugs(self, image_path):
        """
        Send image to Gemini and get drug names.
        Returns: list of drug name strings.
        """
        # Load image
        img = Image.open(image_path)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Send to Gemini
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                img,
                PRESCRIPTION_PROMPT
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature = more deterministic
                max_output_tokens=1024,
            )
        )

        # Parse the response
        text = response.text.strip()
        print(f"📝 Gemini raw response: {text}")

        # Extract the Python list from the response
        drugs = self._parse_drug_list(text)
        return drugs

    def _parse_drug_list(self, text):
        """Parse a string like '["Augmentin", "Pan-D"]' into a Python list."""
        import ast
        try:
            # Find the list part
            start = text.find('[')
            end = text.rfind(']') + 1
            if start == -1 or end == 0:
                return []
            list_str = text[start:end]
            drugs = ast.literal_eval(list_str)
            if isinstance(drugs, list):
                return [str(d).strip() for d in drugs if d]
            return []
        except Exception as e:
            print(f"⚠️ Failed to parse Gemini response: {e}")
            return []

    def extract_text(self, image_path):
        """
        Send image to Gemini and get ALL text (for debugging/comparison).
        """
        img = Image.open(image_path)
        if img.mode != "RGB":
            img = img.convert("RGB")

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                img,
                "Read all text in this image. Output only the text, preserving line breaks."
            ],
            config=types.GenerateContentConfig(temperature=0.1)
        )
        return response.text.strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.ocr.gemini_ocr <image_path>")
        sys.exit(1)

    ocr = GeminiOCR()
    print(f"\n📄 Image: {sys.argv[1]}")

    # Extract drug names
    drugs = ocr.extract_drugs(sys.argv[1])
    print(f"\n💊 Drug names found: {drugs}")

    # Also show full text for debugging
    print("\n📝 Full text:")
    print(ocr.extract_text(sys.argv[1]))