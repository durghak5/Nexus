"""
Crop drug-name regions from a prescription using EasyOCR detection.
Saves crops for manual inspection and model testing.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ocr.detector import TextDetector


def crop_drugs(image_path, output_dir, min_confidence=0.4):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    detector = TextDetector()
    detections = detector.detect(image_path, min_confidence=min_confidence)

    print(f"\n📸 Found {len(detections)} regions. Saving crops...")

    saved = []
    for i, det in enumerate(detections):
        text = det["text"]
        # Keep only reasonable drug-name candidates
        if len(text) < 4:
            continue
        # Save crop
        crop_filename = f"{i:02d}_{text.replace(' ', '_').replace('/', '_')[:30]}.png"
        crop_path = output_dir / crop_filename
        det["crop"].save(crop_path)
        saved.append((crop_filename, text, det["confidence"]))

    print(f"✅ Saved {len(saved)} crops to {output_dir}\n")
    for fname, text, conf in saved:
        print(f"  {fname}  ←  '{text}' (conf={conf:.2f})")

    return saved


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crop_drugs.py <image_path> [output_dir]")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "data/test_prescriptions/crops"
    crop_drugs(image_path, output_dir)