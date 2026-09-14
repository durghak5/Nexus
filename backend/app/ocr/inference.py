"""
Inference for the fine-tuned TrOCR model.
Loads model once, provides predict() function.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from app.ocr.preprocessor import Preprocessor


MODEL_PATH = PROJECT_ROOT / "models" / "trocr_finetuned"
MAX_LENGTH = 16


class PrescriptionOCR:
    """Wrapper around the fine-tuned TrOCR model."""

    def __init__(self, model_path=MODEL_PATH, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🔧 Loading model from {model_path} on {self.device}...")

        self.processor = TrOCRProcessor.from_pretrained(str(model_path))
        self.model = VisionEncoderDecoderModel.from_pretrained(str(model_path))
        self.model.to(self.device)
        self.model.eval()

        self.preprocessor = Preprocessor(target_size=(384, 384))
        print("✅ Model loaded")

    @torch.no_grad()
    def predict(self, image, return_confidence=False):
        """
        Predict text from a single image.

        Args:
            image: str (path) or PIL.Image
            return_confidence: if True, also compute a confidence score

        Returns:
            text (str) or (text, confidence)
        """
        # Preprocess
        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = image
        img = self.preprocessor.process(img)

        # Prepare pixel values
        pixel_values = self.processor(
            images=img, return_tensors="pt"
        ).pixel_values.to(self.device)

        # Generate with scores for confidence
        output = self.model.generate(
            pixel_values,
            max_length=MAX_LENGTH,
            num_beams=4,
            output_scores=True,
            return_dict_in_generate=True,
        )

        text = self.processor.batch_decode(
            output.sequences, skip_special_tokens=True
        )[0].strip()

        if not return_confidence:
            return text

        # Compute confidence from beam scores
        confidence = self._compute_confidence(output)
        return text, confidence

    def _compute_confidence(self, output):
        """Average token probability across the generated sequence."""
        if not hasattr(output, "sequences_scores") or output.sequences_scores is None:
            return None
        # sequences_scores are log-probs; convert to prob
        score = output.sequences_scores[0].item()
        prob = float(torch.exp(torch.tensor(score)))
        return round(prob, 4)

    @torch.no_grad()
    def predict_batch(self, images):
        """Predict for a list of images (paths or PIL)."""
        processed = []
        for img in images:
            if isinstance(img, str):
                img = Image.open(img)
            processed.append(self.preprocessor.process(img))

        pixel_values = self.processor(
            images=processed, return_tensors="pt"
        ).pixel_values.to(self.device)

        generated_ids = self.model.generate(
            pixel_values, max_length=MAX_LENGTH, num_beams=4
        )
        return self.processor.batch_decode(generated_ids, skip_special_tokens=True)


# ============================================================
# CLI test
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.ocr.inference <image_path>")
        sys.exit(1)

    ocr = PrescriptionOCR()
    result = ocr.predict(sys.argv[1], return_confidence=True)
    print(f"\n📝 Prediction: '{result[0]}'")
    print(f"🎯 Confidence: {result[1]}")