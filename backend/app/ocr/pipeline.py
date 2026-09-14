"""
Full OCR pipeline: image → text → correction → confidence → drug info.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ocr.inference import PrescriptionOCR
from app.ocr.dictionary import DrugDictionary


class OCRPipeline:
    """One-stop pipeline: inference → dictionary → confidence."""

    def __init__(self):
        print("🚀 Initializing OCR Pipeline...")
        self.ocr = PrescriptionOCR()
        self.dictionary = DrugDictionary()
        print("✅ Pipeline ready\n")

    def process(self, image):
        """
        Full pipeline for one image.

        Returns:
            {
              "raw_text": OCR raw output,
              "corrected_text": Dictionary-corrected text,
              "confidence": Model confidence (0-1),
              "was_corrected": bool,
              "match_found": bool,
              "status": "HIGH" | "MEDIUM" | "LOW"
            }
        """
        # 1. OCR
        raw_text, confidence = self.ocr.predict(image, return_confidence=True)
        raw_text = raw_text.strip() if raw_text else ""

        # 2. Dictionary correction
        correction = self.dictionary.correct(raw_text)

        # 3. Confidence gate
        #    HIGH: confidence >= 0.9 AND dictionary match
        #    MEDIUM: confidence >= 0.5 OR dictionary match
        #    LOW: otherwise
        if confidence is None:
            confidence = 0.0

        if confidence >= 0.9 and correction["matched"]:
            status = "HIGH"
        elif confidence >= 0.5 or correction["matched"]:
            status = "MEDIUM"
        else:
            status = "LOW"

        return {
            "raw_text": raw_text,
            "corrected_text": correction["corrected"],
            "confidence": confidence,
            "was_corrected": correction["was_corrected"],
            "match_found": correction["matched"],
            "edit_distance": correction["distance"],
            "status": status,
        }


# CLI test
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.ocr.pipeline <image_path>")
        sys.exit(1)

    pipeline = OCRPipeline()
    result = pipeline.process(sys.argv[1])

    print("=" * 50)
    print("📋 PIPELINE RESULT")
    print("=" * 50)
    for key, val in result.items():
        print(f"  {key}: {val}")