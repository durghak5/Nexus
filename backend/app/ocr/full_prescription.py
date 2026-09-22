"""
Full prescription pipeline:
1. Detect text regions (EasyOCR)
2. Recognize each crop with TrOCR
3. Filter with dictionary in TRUSTED mode (no false positives)
4. Return structured drug list
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import re
from app.ocr.detector import TextDetector
from app.ocr.inference import PrescriptionOCR
from app.ocr.dictionary import DrugDictionary


STOPWORDS = {
    'smile', 'designing', 'teeth', 'whitening', 'dental', 'implants', 'general',
    'dentistry', 'sachin', 'sansare', 'date', 'sign', 'signature',
    'meals', 'after', 'before', 'day', 'days', 'week', 'weeks', 'month',
    'morning', 'night', 'evening', 'gum', 'paint', 'massage', 'use', 'take',
    'clinic', 'hospital', 'address', 'phone', 'email', 'web', 'www', 'com',
    'ph', 'mob', 'tel', 'reg', 'no', 'mbbs', 'md', 'bds', 'dr',
    'rx', 'tab', 'cap', 'syp', 'inj', 'adv',
}

DOSAGE_PATTERN = re.compile(r'^\d+\s*(mg|ml|g|mcg|iu|%|x|tabs?|caps?)\b', re.IGNORECASE)
FREQ_PATTERN = re.compile(r'^[\d\-\s/x]+$', re.IGNORECASE)
DATE_PATTERN = re.compile(r'^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}$')


class FullPrescriptionPipeline:

    def __init__(self):
        print("🚀 Initializing Full Prescription Pipeline...")
        self.detector = TextDetector()
        self.ocr = PrescriptionOCR()
        self.dictionary = DrugDictionary()
        print("✅ Full pipeline ready\n")

    def process(self, image_path, verbose=True):
        # STEP 1: Detect
        if verbose:
            print("🔍 Step 1: Detecting text regions...")
        detections = self.detector.detect(image_path)
        if verbose:
            print(f"   Found {len(detections)} regions\n")

        # Sort by position
        detections.sort(key=lambda d: (d["bbox"][1] // 20, d["bbox"][0]))

        # STEP 2: Recognize
        if verbose:
            print("📖 Step 2: Reading each region with TrOCR...")
        recognized = []
        for i, det in enumerate(detections):
            try:
                text, conf = self.ocr.predict(det["crop"], return_confidence=True)
                recognized.append({
                    "bbox": det["bbox"],
                    "easyocr_text": det["text"],
                    "trocr_text": text or "",
                    "trocr_confidence": conf or 0.0,
                })
            except Exception as e:
                if verbose:
                    print(f"   [{i}] Error: {e}")

        # STEP 3: Trusted extraction
        if verbose:
            print(f"\n💊 Step 3: Extracting drug names (trusted mode)...")
        drugs = []
        seen_names = set()

        for rec in recognized:
            for source in ("trocr_text", "easyocr_text"):
                candidate = rec[source].strip()
                if not candidate or len(candidate) < 4:
                    continue

                candidate_lower = candidate.lower()
                if candidate_lower in STOPWORDS:
                    continue
                if DOSAGE_PATTERN.match(candidate):
                    continue
                if FREQ_PATTERN.match(candidate):
                    continue
                if DATE_PATTERN.match(candidate):
                    continue

                # TRUSTED MATCHING ONLY
                result = self.dictionary.correct(candidate, trusted_only=True)
                if result["matched"]:
                    canonical = result["corrected"].lower()
                    if canonical in seen_names:
                        break
                    seen_names.add(canonical)
                    drugs.append({
                        "name": result["corrected"],
                        "raw_text": candidate,
                        "confidence": rec["trocr_confidence"],
                        "source": result["source"],
                        "bbox": rec["bbox"],
                    })
                    break

        if verbose:
            print(f"   ✅ Found {len(drugs)} drug names\n")

        return {
            "detections": detections,
            "recognized": recognized,
            "drugs": drugs,
            "count": len(drugs),
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