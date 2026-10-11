"""
Dual-model OCR inference:
- Generic-name model (NEW - permanent fix)
- Fine-tuned brand model (legacy - works on Kaggle test)
- Pretrained (fallback)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from app.ocr.preprocessor import Preprocessor


GENERIC_PATH = PROJECT_ROOT / "models" / "trocr_generic"
BRAND_PATH = PROJECT_ROOT / "models" / "trocr_finetuned"
PRETRAINED_MODEL = "microsoft/trocr-base-handwritten"
MAX_LENGTH = 40


class PrescriptionOCR:
    """
    Multi-model OCR.
    - self.predict(image)          → uses generic model (default, permanent fix)
    - self.predict_brand(image)    → uses brand model (legacy)
    - self.predict_dual(image)     → runs generic + brand
    """

    def __init__(self, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # 1. Generic model (PRIMARY)
        print(f"🔧 Loading generic model from {GENERIC_PATH}...")
        if GENERIC_PATH.exists():
            self.processor_gen = TrOCRProcessor.from_pretrained(str(GENERIC_PATH))
            self.model_gen = VisionEncoderDecoderModel.from_pretrained(str(GENERIC_PATH))
            self.model_gen.to(self.device).eval()
            print("✅ Generic model loaded")
        else:
            self.model_gen = None
            print("⚠️  Generic model not found — run train_generic.py first")

        # 2. Brand model (secondary)
        print(f"🔧 Loading brand model from {BRAND_PATH}...")
        if BRAND_PATH.exists():
            self.processor_brand = TrOCRProcessor.from_pretrained(str(BRAND_PATH))
            self.model_brand = VisionEncoderDecoderModel.from_pretrained(str(BRAND_PATH))
            self.model_brand.to(self.device).eval()
            print("✅ Brand model loaded")
        else:
            self.model_brand = None

        self.preprocessor = Preprocessor(target_size=(384, 384))
        print("✅ OCR ready")

    def _run(self, model, processor, image, max_length=MAX_LENGTH):
        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = image
        img = self.preprocessor.process(img)

        pixel_values = processor(images=img, return_tensors="pt").pixel_values.to(self.device)

        with torch.no_grad():
            output = model.generate(
                pixel_values, max_length=max_length, num_beams=4,
                output_scores=True, return_dict_in_generate=True,
            )
        text = processor.batch_decode(output.sequences, skip_special_tokens=True)[0].strip()

        if output.sequences_scores is not None:
            prob = float(torch.exp(output.sequences_scores[0]).item())
        else:
            prob = 0.0
        return text, round(prob, 4)

    def predict(self, image, return_confidence=False):
        """Default: use generic model."""
        if self.model_gen is None:
            raise RuntimeError("Generic model not loaded")
        text, conf = self._run(self.model_gen, self.processor_gen, image)
        if return_confidence:
            return text, conf
        return text

    def predict_brand(self, image, return_confidence=False):
        """Legacy: use brand model."""
        if self.model_brand is None:
            raise RuntimeError("Brand model not loaded")
        text, conf = self._run(self.model_brand, self.processor_brand, image, max_length=16)
        if return_confidence:
            return text, conf
        return text

    def predict_dual(self, image):
        """Run both models and return both results."""
        results = {}
        if self.model_gen is not None:
            t, c = self._run(self.model_gen, self.processor_gen, image)
            results["generic"] = {"text": t, "confidence": c}
        if self.model_brand is not None:
            t, c = self._run(self.model_brand, self.processor_brand, image, max_length=16)
            results["brand"] = {"text": t, "confidence": c}
        return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.ocr.inference <image_path>")
        sys.exit(1)

    ocr = PrescriptionOCR()
    print("\n=== PREDICTION ===")
    text, conf = ocr.predict(sys.argv[1], return_confidence=True)
    print(f"  Generic model: '{text}' (conf: {conf})")
    print("\n=== DUAL ===")
    dual = ocr.predict_dual(sys.argv[1])
    for name, r in dual.items():
        print(f"  {name}: '{r['text']}' (conf: {r['confidence']})")