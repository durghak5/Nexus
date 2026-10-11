"""
Full prescription pipeline with Gemini-primary OCR.
Gemini reads the full prescription image → extracts drug names directly.
Falls back to EasyOCR + local TrOCR if Gemini fails.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ocr.gemini_ocr import GeminiOCR
from app.ocr.dictionary import DrugDictionary


class FullPrescriptionPipeline:

    def __init__(self, use_gemini=True):
        print("🚀 Initializing Full Prescription Pipeline...")

        self.use_gemini = use_gemini
        if use_gemini:
            try:
                self.gemini = GeminiOCR()
            except Exception as e:
                print(f"⚠️  Gemini init failed: {e}")
                print("   Falling back to local TrOCR pipeline")
                self.use_gemini = False

        # Dictionary always loads (for correction + recommendations)
        self.dictionary = DrugDictionary()

        # Lazy-load local pipeline only if needed
        self._local_pipeline = None

        print("✅ Full pipeline ready\n")

    def _get_local_pipeline(self):
        """Lazy-load the local TrOCR pipeline (heavy)."""
        if self._local_pipeline is None:
            from app.ocr.full_prescription_local import FullPrescriptionPipelineLocal
            self._local_pipeline = FullPrescriptionPipelineLocal()
        return self._local_pipeline

    def process(self, image_path, verbose=True):
        """
        Main entry: process a prescription image.
        Uses Gemini if available, else falls back to local pipeline.
        """
        if self.use_gemini:
            return self._process_with_gemini(image_path, verbose)
        else:
            return self._get_local_pipeline().process(image_path, verbose)

    def _process_with_gemini(self, image_path, verbose=True):
        if verbose:
            print("🌟 Using Gemini OCR (full prescription mode)...")

        # 1. Gemini extracts drug names directly
        try:
            drug_names_raw = self.gemini.extract_drugs(image_path)
        except Exception as e:
            print(f"❌ Gemini failed: {e}")
            print("   Falling back to local pipeline...")
            return self._get_local_pipeline().process(image_path, verbose)

        if verbose:
            print(f"   Gemini found: {drug_names_raw}")

        # 2. Validate each drug against dictionary
        drugs = []
        seen = set()
        for name in drug_names_raw:
            result = self.dictionary.correct(name, trusted_only=False)
            canonical = result["corrected"].lower()
            if canonical in seen:
                continue
            seen.add(canonical)
            drugs.append({
                "name": result["corrected"],
                "raw_text": name,
                "confidence": 0.99,       # Gemini is highly reliable
                "source": "gemini" + ("+dict" if result["was_corrected"] else ""),
                "was_corrected": result["was_corrected"],
                "dictionary_matched": result["matched"],
            })

        if verbose:
            print(f"   ✅ {len(drugs)} drug names validated\n")

        # Return in the same shape as the local pipeline (frontend compatibility)
        return {
            "detections": [],                    # not applicable with Gemini
            "recognized": [],
            "drugs": drugs,
            "count": len(drugs),
            "source": "gemini",
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.ocr.full_prescription <image_path>")
        sys.exit(1)

    pipeline = FullPrescriptionPipeline()
    result = pipeline.process(sys.argv[1])

    print("=" * 60)
    print("📋 FINAL RESULT")
    print("=" * 60)
    print(f"Drug names found: {result['count']}\n")
    for d in result["drugs"]:
        print(f"  • {d['name']}")
        print(f"      raw: '{d['raw_text']}' | src: {d['source']} | conf: {d['confidence']:.2f}")