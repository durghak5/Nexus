"""
Text detection using EasyOCR.
Finds WHERE text is in a prescription image.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import easyocr
import numpy as np
from PIL import Image


class TextDetector:
    """Detects text regions in a full prescription image."""

    def __init__(self, languages=['en'], gpu=True):
        print(f"🔧 Initializing EasyOCR detector (languages={languages}, gpu={gpu})...")
        self.reader = easyocr.Reader(languages, gpu=gpu)
        print("✅ Detector ready")

    def detect(self, image, min_confidence=0.3, min_width=15, min_height=10):
        """
        Detect text regions in the image.

        Args:
            image: path or PIL.Image or numpy array
            min_confidence: EasyOCR's own confidence filter
            min_width, min_height: filter out tiny noise boxes

        Returns:
            list of dicts: [{bbox, text, confidence, crop}]
        """
        if isinstance(image, str):
            img = Image.open(image).convert('RGB')
        elif isinstance(image, Image.Image):
            img = image.convert('RGB')
        else:
            img = Image.fromarray(image).convert('RGB')

        img_np = np.array(img)

        # EasyOCR expects BGR or path; np array works
        results = self.reader.readtext(img_np, detail=1)

        detections = []
        for bbox, text, confidence in results:
            # bbox is 4 points: [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))

            w = x2 - x1
            h = y2 - y1
            if w < min_width or h < min_height:
                continue
            if confidence < min_confidence:
                continue

            # Crop with small padding
            pad = 5
            crop = img.crop((
                max(0, x1 - pad),
                max(0, y1 - pad),
                min(img.width, x2 + pad),
                min(img.height, y2 + pad),
            ))

            detections.append({
                "bbox": (x1, y1, x2, y2),
                "text": text.strip(),
                "confidence": float(confidence),
                "crop": crop,
            })

        return detections


# CLI test
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.ocr.detector <image_path>")
        sys.exit(1)

    detector = TextDetector()
    detections = detector.detect(sys.argv[1])
    print(f"\n🔍 Detected {len(detections)} text regions:")
    for i, d in enumerate(detections[:20]):
        print(f"  [{i}] '{d['text']}' (conf={d['confidence']:.2f}, bbox={d['bbox']})")