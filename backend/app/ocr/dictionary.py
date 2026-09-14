"""
Dictionary-based correction for OCR output.
Uses Levenshtein distance against DISB database + Kaggle training brands.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from Levenshtein import distance as levenshtein_distance
from app.database.connection import SessionLocal
from app.database.models import Brand, Generic


KAGGLE_CSV = PROJECT_ROOT / "data" / "raw" / "Doctor’s Handwritten Prescription BD dataset" / "Training" / "training_labels.csv"


class DrugDictionary:
    """Corrects OCR output against known drug names."""

    def __init__(self):
        self.brand_names = set()
        self.generic_names = set()
        self._load_from_database()
        self._load_from_kaggle()

        # Convert to sorted lists for deterministic iteration
        self.brand_names = sorted(self.brand_names)
        self.generic_names = sorted(self.generic_names)

        print(f"   Total brand names: {len(self.brand_names)}")
        print(f"   Total generic names: {len(self.generic_names)}")

    def _load_from_database(self):
        """Load brand + generic identifiers from DISB database."""
        print("📚 Loading DISB drug dictionary...")
        db = SessionLocal()
        try:
            brands = db.query(Brand.identifier).all()
            generics = db.query(Generic.identifier).all()
            for b in brands:
                if b[0]:
                    self.brand_names.add(b[0].strip())
            for g in generics:
                if g[0]:
                    self.generic_names.add(g[0].strip())
            print(f"   ✅ DISB: {len(self.brand_names)} brands, {len(self.generic_names)} generics")
        finally:
            db.close()

    def _load_from_kaggle(self):
        """Load brand + generic names from Kaggle training CSV."""
        if not KAGGLE_CSV.exists():
            print(f"   ⚠️  Kaggle CSV not found: {KAGGLE_CSV}")
            return

        print("📚 Loading Kaggle training brands...")
        df = pd.read_csv(KAGGLE_CSV)
        kaggle_brands = set(df['MEDICINE_NAME'].dropna().astype(str).str.strip())
        kaggle_generics = set(df['GENERIC_NAME'].dropna().astype(str).str.strip())

        self.brand_names.update(kaggle_brands)
        self.generic_names.update(kaggle_generics)

        print(f"   ✅ Kaggle: {len(kaggle_brands)} brands, {len(kaggle_generics)} generics")

    def correct(self, text, max_distance=2):
        """Correct OCR text to the closest known drug name."""
        text = text.strip()
        if not text:
            return {"corrected": text, "matched": False, "distance": None, "was_corrected": False}

        text_lower = text.lower()

        # 1. Exact match against brand names
        for name in self.brand_names:
            if name.lower() == text_lower:
                return {"corrected": name, "matched": True, "distance": 0, "was_corrected": False}

        # 2. Fuzzy match against brand names
        best_match = None
        best_distance = max_distance + 1

        for name in self.brand_names:
            d = levenshtein_distance(text_lower, name.lower())
            if d < best_distance:
                best_distance = d
                best_match = name
                if d == 1:
                    break

        if best_match and best_distance <= max_distance:
            return {
                "corrected": best_match,
                "matched": True,
                "distance": best_distance,
                "was_corrected": best_distance > 0,
            }

        # 3. Try exact + fuzzy match against generic names too
        for name in self.generic_names:
            if name.lower() == text_lower:
                return {"corrected": name, "matched": True, "distance": 0, "was_corrected": False}

        for name in self.generic_names:
            d = levenshtein_distance(text_lower, name.lower())
            if d < best_distance and d <= max_distance:
                best_distance = d
                best_match = name

        if best_match and best_distance <= max_distance:
            return {
                "corrected": best_match,
                "matched": True,
                "distance": best_distance,
                "was_corrected": best_distance > 0,
            }

        return {
            "corrected": text,
            "matched": False,
            "distance": best_distance if best_match else None,
            "was_corrected": False,
        }


if __name__ == "__main__":
    d = DrugDictionary()
    tests = ["Aceta", "Acetaa", "Baclon", "Baclone", "Zithrin", "Paracetamol", "Crocin", "Random123"]
    print("\n🧪 Testing dictionary correction:")
    for t in tests:
        r = d.correct(t)
        status = "✓" if r["matched"] else "✗"
        print(f"  {status} '{t}' → '{r['corrected']}' (distance: {r['distance']})")