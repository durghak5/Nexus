"""
Fine-tune TrOCR to predict GENERIC drug names (permanent fix).
Trains on the same images but with generic labels instead of brand names.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from torch.utils.data import DataLoader, Subset
from torch.optim import AdamW
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from tqdm import tqdm
import numpy as np
import random

from app.ocr.preprocessor import Preprocessor
from app.ocr.data_loader_v2 import PrescriptionGenericDataset


# ============================================================
# CONFIG
# ============================================================
DATASET_DIR = PROJECT_ROOT / "data" / "raw" / "Doctor’s Handwritten Prescription BD dataset"
MODEL_SAVE_DIR = PROJECT_ROOT / "models" / "trocr_generic"
PRETRAINED_MODEL = "microsoft/trocr-base-handwritten"

BATCH_SIZE = 4
GRAD_ACCUM_STEPS = 4
NUM_EPOCHS = 20
LEARNING_RATE = 5e-5
MAX_TARGET_LENGTH = 40                # Longer for generic names
SEED = 42
FREEZE_ENCODER = True

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def set_seed(seed):
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def split_train_val(dataset, val_ratio=0.1, seed=42):
    n = len(dataset)
    indices = list(range(n))
    random.seed(seed)
    random.shuffle(indices)
    val_size = int(n * val_ratio)
    return Subset(dataset, indices[val_size:]), Subset(dataset, indices[:val_size])


def train():
    set_seed(SEED)

    print("=" * 60)
    print("🚀 Fine-tuning TrOCR → GENERIC drug names")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    if DEVICE.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Max target length: {MAX_TARGET_LENGTH}")
    print()

    # 1. Load processor + model
    print("🤖 Loading pretrained TrOCR...")
    processor = TrOCRProcessor.from_pretrained(PRETRAINED_MODEL)
    model = VisionEncoderDecoderModel.from_pretrained(PRETRAINED_MODEL)

    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.vocab_size = model.config.decoder.vocab_size
    model.config.max_length = MAX_TARGET_LENGTH
    model.config.early_stopping = True
    model.config.no_repeat_ngram_size = 3
    model.config.length_penalty = 1.5
    model.config.num_beams = 4

    if FREEZE_ENCODER:
        for param in model.encoder.parameters():
            param.requires_grad = False
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())
        print(f"   Trainable: {trainable:,} / {total:,} params")

    model.to(DEVICE)

    # 2. Load dataset
    print("\n📂 Loading dataset...")
    preprocessor = Preprocessor(target_size=(384, 384))
    full_dataset = PrescriptionGenericDataset(
        csv_path=DATASET_DIR / "Training" / "training_labels.csv",
        images_dir=DATASET_DIR / "Training" / "training_words",
        preprocessor=preprocessor,
        processor=processor,
        max_length=MAX_TARGET_LENGTH,
    )
    train_ds, val_ds = split_train_val(full_dataset)
    print(f"   Train: {len(train_ds)} | Val: {len(val_ds)}\n")

    def collate_fn(batch):
        images = [item[0] for item in batch]
        labels = [item[1] for item in batch]
        indices = [item[2] for item in batch]
        label_ids = torch.stack([full_dataset.precomputed_labels[i] for i in indices])
        return images, labels, label_ids

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=0, collate_fn=collate_fn)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False,
                            num_workers=0, collate_fn=collate_fn)

    # 3. Optimizer
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = AdamW(trainable_params, lr=LEARNING_RATE)
    scaler = torch.amp.GradScaler('cuda') if DEVICE.type == "cuda" else None

    # 4. Training loop
    print("🏋️  Training...")
    print("=" * 60)

    for epoch in range(NUM_EPOCHS):
        model.train()
        total_loss = 0.0
        optimizer.zero_grad()
        progress = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{NUM_EPOCHS}")

        for step, (images, labels, label_ids) in enumerate(progress):
            pixel_values = processor(images=images, return_tensors="pt").pixel_values.to(DEVICE)
            labels_tensor = label_ids.to(DEVICE)
            labels_tensor[labels_tensor == processor.tokenizer.pad_token_id] = -100

            if DEVICE.type == "cuda":
                with torch.amp.autocast('cuda'):
                    outputs = model(pixel_values=pixel_values, labels=labels_tensor)
                    loss = outputs.loss / GRAD_ACCUM_STEPS
                scaler.scale(loss).backward()
            else:
                outputs = model(pixel_values=pixel_values, labels=labels_tensor)
                loss = outputs.loss / GRAD_ACCUM_STEPS
                loss.backward()

            if (step + 1) % GRAD_ACCUM_STEPS == 0:
                if scaler:
                    scaler.step(optimizer); scaler.update()
                else:
                    optimizer.step()
                optimizer.zero_grad()

            total_loss += loss.item() * GRAD_ACCUM_STEPS
            progress.set_postfix(loss=f"{loss.item() * GRAD_ACCUM_STEPS:.4f}")

        avg_loss = total_loss / len(train_loader)
        print(f"   Epoch {epoch + 1} avg loss: {avg_loss:.4f}")

        if (epoch + 1) % 5 == 0 or epoch == NUM_EPOCHS - 1:
            acc = quick_validate(model, processor, val_loader)
            print(f"   Epoch {epoch + 1} val word accuracy: {acc * 100:.2f}%")

    print("\n💾 Saving model...")
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(MODEL_SAVE_DIR)
    processor.save_pretrained(MODEL_SAVE_DIR)
    print(f"✅ Model saved to: {MODEL_SAVE_DIR}")
    print("\n🎉 Training complete!")


def quick_validate(model, processor, val_loader, max_batches=20):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for i, (images, labels, _) in enumerate(val_loader):
            if i >= max_batches:
                break
            pixel_values = processor(images=images, return_tensors="pt").pixel_values.to(DEVICE)
            generated_ids = model.generate(pixel_values, max_length=MAX_TARGET_LENGTH)
            preds = processor.batch_decode(generated_ids, skip_special_tokens=True)
            for pred, target in zip(preds, labels):
                if pred.strip().lower() == target.strip().lower():
                    correct += 1
                total += 1
    model.train()
    return correct / total if total > 0 else 0.0


if __name__ == "__main__":
    train()