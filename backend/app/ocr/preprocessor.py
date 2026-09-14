"""
Image preprocessing for TrOCR.
Cleans and normalizes handwriting images before feeding to the model.
"""

from PIL import Image, ImageOps, ImageFilter
import numpy as np


class Preprocessor:
    """Preprocess images for OCR model"""

    def __init__(self, target_size=(384, 384), invert_if_dark=True):
        self.target_size = target_size
        self.invert_if_dark = invert_if_dark

    def process(self, image_path_or_pil):
        """
        Full preprocessing pipeline.

        Args:
            image_path_or_pil: str (path) or PIL.Image

        Returns:
            PIL.Image in RGB mode, ready for TrOCR processor
        """
        # 1. Load image
        if isinstance(image_path_or_pil, str):
            img = Image.open(image_path_or_pil)
        else:
            img = image_path_or_pil

        # 2. Convert to RGB (TrOCR expects 3-channel)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 3. Optionally invert if image is dark-on-light vs light-on-dark
        # TrOCR prefers light background, dark text (like natural images)
        if self.invert_if_dark:
            img = self._maybe_invert(img)

        # 4. Resize while preserving aspect ratio, then pad
        img = self._resize_with_padding(img, self.target_size)

        return img

    def _maybe_invert(self, img: Image.Image) -> Image.Image:
        """Invert if the image is mostly dark (inverted handwriting)."""
        arr = np.array(img.convert('L'))
        mean = arr.mean()
        # If mean < 128, image is darker than white → likely inverted
        if mean < 128:
            return ImageOps.invert(img)
        return img

    def _resize_with_padding(self, img: Image.Image, target) -> Image.Image:
        """Resize to fit within target, pad with white to reach exact size."""
        target_w, target_h = target
        original_w, original_h = img.size

        # Compute scale to fit within target
        scale = min(target_w / original_w, target_h / original_h)
        new_w = int(original_w * scale)
        new_h = int(original_h * scale)

        # Resize
        resized = img.resize((new_w, new_h), Image.LANCZOS)

        # Pad with white to reach target size
        padded = Image.new('RGB', target, (255, 255, 255))
        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2
        padded.paste(resized, (paste_x, paste_y))

        return padded


# Quick test when run directly
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python preprocessor.py <image_path>")
        sys.exit(1)

    preprocessor = Preprocessor()
    img = preprocessor.process(sys.argv[1])
    print(f"✅ Processed image size: {img.size}")
    print(f"   Mode: {img.mode}")

    # Save for visual check
    img.save("preprocessed_test.png")
    print("   Saved to preprocessed_test.png")