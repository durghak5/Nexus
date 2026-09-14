"""
Data loader for the Doctor's Handwritten Prescription BD dataset.
PRELOADS all images and tokenized labels into RAM for speed.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from PIL import Image
from torch.utils.data import Dataset as TorchDataset


class PrescriptionWordDataset(TorchDataset):
    """
    PyTorch Dataset with PRELOADED images and tokenized labels.
    """

    def __init__(self, csv_path, images_dir, preprocessor=None,
                 processor=None, max_length=16,
                 image_col='IMAGE', label_col='MEDICINE_NAME'):
        """
        Args:
            csv_path: path to labels CSV
            images_dir: folder with PNG images
            preprocessor: optional Preprocessor instance
            processor: TrOCR processor for tokenizing labels
            max_length: max token length for labels
            image_col: CSV column with image filename
            label_col: CSV column with target text
        """
        self.df = pd.read_csv(csv_path)
        self.images_dir = Path(images_dir)
        self.preprocessor = preprocessor
        self.processor = processor
        self.max_length = max_length
        self.image_col = image_col
        self.label_col = label_col

        # Verify files exist
        self.df['_path'] = self.df[image_col].apply(lambda x: self.images_dir / x)
        self.df['_exists'] = self.df['_path'].apply(lambda p: p.exists())
        missing = self.df[~self.df['_exists']]
        if len(missing) > 0:
            print(f"⚠️  {len(missing)} images missing, filtering")
            self.df = self.df[self.df['_exists']].reset_index(drop=True)

        print(f"✅ Loaded {len(self.df)} samples from {csv_path}")
        print(f"🔄 Preloading images into RAM...")

        # PRELOAD images
        self.preloaded_images = []
        for i, row in self.df.iterrows():
            img = Image.open(row['_path'])
            if self.preprocessor:
                img = self.preprocessor.process(img)
            else:
                img = img.convert('RGB')
            self.preloaded_images.append(img)

        print(f"✅ Preloaded {len(self.preloaded_images)} images")

        # PRECOMPUTE tokenized labels if processor provided
        self.precomputed_labels = None
        if self.processor is not None:
            print(f"🔄 Precomputing tokenized labels...")
            self.precomputed_labels = []
            for label in self.df[label_col]:
                enc = self.processor.tokenizer(
                    str(label).strip(),
                    padding='max_length',
                    max_length=self.max_length,
                    truncation=True,
                    return_tensors='pt',
                )
                self.precomputed_labels.append(enc.input_ids.squeeze(0))
            print(f"✅ Precomputed {len(self.precomputed_labels)} tokenized labels")

    def __len__(self):
        return len(self.preloaded_images)

    def __getitem__(self, idx):
        img = self.preloaded_images[idx]
        label = str(self.df.iloc[idx][self.label_col]).strip()
        return img, label, idx  # return idx so we can look up precomputed token


# Quick sanity check
if __name__ == "__main__":
    from app.ocr.preprocessor import Preprocessor

    DATASET_DIR = PROJECT_ROOT / "data" / "raw" / "Doctor’s Handwritten Prescription BD dataset"

    preprocessor = Preprocessor()
    dataset = PrescriptionWordDataset(
        csv_path=DATASET_DIR / "Training" / "training_labels.csv",
        images_dir=DATASET_DIR / "Training" / "training_words",
        preprocessor=preprocessor,
    )

    print(f"\nDataset size: {len(dataset)}")
    for i in range(3):
        img, label, _ = dataset[i]
        print(f"  [{i}] Label: '{label}' | Image size: {img.size}")