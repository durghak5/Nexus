"""
Multi-source drug dictionary with trusted and untrusted matching modes.

trusted_only=True:  Only matches against a curated list of common drugs + aliases.
                    No false positives. Used in the pipeline.

trusted_only=False: Fuzzy matching against full DISB + Kaggle.
                    Used for testing and exploration.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import re
import pandas as pd
from Levenshtein import distance as levenshtein_distance
from app.database.connection import SessionLocal
from app.database.models import Generic
from app.ocr.disb_extractor import build_disb_short_names


KAGGLE_CSV = PROJECT_ROOT / "data" / "raw" / "Doctor’s Handwritten Prescription BD dataset" / "Training" / "training_labels.csv"


BLACKLIST = {
    'tab', 'cap', 'syp', 'syrup', 'inj', 'susp', 'adv', 'rx', 'dr', 'mr', 'mrs', 'ms',
    'meals', 'after', 'before', 'day', 'days', 'week', 'weeks', 'month', 'months',
    'morning', 'night', 'evening', 'gum', 'paint', 'massage', 'sign', 'clinic',
    'address', 'phone', 'email', 'the', 'and', 'for', 'with', 'use', 'take', 'apply',
    'tablet', 'capsule', 'injection', 'twice', 'thrice', 'daily', 'as', 'needed',
    'tab.', 'cap.', 'syp.', 'adv:', 'smile', 'designing', 'teeth', 'whitening',
    'dental', 'implants', 'general', 'dentistry', 'sachin', 'sansare',
    'clinic', 'hospital', 'address', 'phone', 'email', 'web', 'www', 'com',
    'ph', 'mob', 'tel', 'reg', 'no', 'mbbs', 'md', 'bds',
}


# ============================================================
# CURATED LIST OF COMMON INDIAN DRUGS (trusted matching)
# ============================================================
COMMON_INDIAN_DRUGS = {
    # Antibiotics
    'augmentin', 'amoxicillin', 'azithromycin', 'azee', 'azithral', 'taxim',
    'ceftum', 'monocef', 'mox', 'novamox', 'zithromax', 'azithrocin', 'azithral',
    'clavam', 'moxikind', 'amoxyclav',
    # Pain / fever
    'paracetamol', 'dolo', 'crocin', 'calpol', 'combiflam', 'brufen',
    'ibugesic', 'voveran', 'dynapar', 'zerodol', 'nise', 'aceclofenac',
    'diclofenac', 'ibuprofen', 'naproxen', 'etoshine', 'etoricoxib',
    # GI
    'pan', 'pand', 'pantop', 'pantoprazole', 'pan-d', 'pan-40', 'pan40',
    'rantac', 'zantac', 'omez', 'omeprazole', 'digene', 'gelusil', 'cremaffin',
    'razo', 'esomeprazole', 'nexium', 'esomep',
    # Antiallergic
    'cetirizine', 'cetzine', 'alerid', 'levocet', 'xyzal', 'montair',
    'montek', 'allegra', 'fexo', 'fexofast', 'allegra', 'fexofenadine',
    # Diabetes
    'metformin', 'glycomet', 'glucophage', 'januvia', 'galvus', 'glimepiride',
    'amaryl', 'janumet',
    # Cardiac
    'amlodipine', 'amlokind', 'stamlo', 'telma', 'telmisartan', 'telma-h',
    'atorvastatin', 'atorva', 'rosuvastatin', 'ecosprin', 'clopilet',
    'metoprolol', 'metolar',
    # Steroids
    'prednisolone', 'omnacortil', 'wysolone', 'deflazacort',
    # Respiratory
    'asthalin', 'salbutamol', 'foracort', 'seroflo', 'budecort', 'montek',
    # Others
    'hexigel', 'enzofam', 'enzoflam', 'chymoral', 'serratiopeptidase',
    'thyronorm', 'eltroxin', 'vitamin', 'shelcal', 'calcimax', 'becosules',
    'zincovit', 'limcee', 'supradyn',
    # Common Bengaluru/Mumbai specific
    'dol', 'combiflam', 'meftal', 'meftal-spas', 'cyclopen', 'crocine',
    'allegra', 'wikoryl', 'sinarest', 'cheston-cold', 'd-cold',
}


# ============================================================
# MANUAL ALIASES (OCR misreads → correct name)
# ============================================================
MANUAL_ALIASES = {
    # Augmentin variants
    "augmentin": "Augmentin",
    "aujnenturi": "Augmentin",
    "augmentn": "Augmentin",
    "augmenti": "Augmentin",
    # Enzoflam variants
    "enzoflam": "Enzoflam",
    "ennzlrn": "Enzoflam",
    "enzofam": "Enzoflam",
    # Pan-D variants
    "pand": "Pan-D",
    "pan d": "Pan-D",
    "pan-d": "Pan-D",
    "pantop": "Pan-D",
    "pan40": "Pan-D",
    # Hexigel variants
    "hexigel": "Hexigel",
    "hexiget": "Hexigel",
    "hexiqel": "Hexigel",
    "hexiqei": "Hexigel",
    # Common ones
    "dolo": "Dolo",
    "dolo650": "Dolo",
    "crocin": "Crocin",
    "combiflam": "Combiflam",
}


def normalize(s: str) -> str:
    """Lowercase, strip hyphens/spaces/dots."""
    if not s:
        return ""
    return re.sub(r'[\s\-\.\_]+', '', s.lower())


# Pre-normalized lookups
COMMON_DRUGS_NORM = {normalize(d): d for d in COMMON_INDIAN_DRUGS}
MANUAL_ALIASES_NORM = {normalize(k): v for k, v in MANUAL_ALIASES.items()}


class DrugDictionary:

    def __init__(self):
        self.brand_names = set()
        self.generic_names = set()
        self._load_all()

        self.brand_norm = {}
        for n in self.brand_names:
            norm = normalize(n)
            if norm and norm not in self.brand_norm:
                self.brand_norm[norm] = n

        self.generic_norm = {}
        for n in self.generic_names:
            norm = normalize(n)
            if norm and norm not in self.generic_norm:
                self.generic_norm[norm] = n

        print(f"   Full dictionary: {len(self.brand_norm)} brands, {len(self.generic_norm)} generics")
        print(f"   Trusted list: {len(COMMON_DRUGS_NORM)} drugs + {len(MANUAL_ALIASES_NORM)} aliases")

    def _load_all(self):
        disb_short = build_disb_short_names()
        self.brand_names.update(disb_short)

        print("📚 Loading DISB generics...")
        db = SessionLocal()
        try:
            generics = db.query(Generic.identifier).all()
            for (g,) in generics:
                if g and len(g.strip()) >= 3:
                    self.generic_names.add(g.strip())
        finally:
            db.close()

        if KAGGLE_CSV.exists():
            print("📚 Loading Kaggle brands...")
            df = pd.read_csv(KAGGLE_CSV)
            self.brand_names.update(df['MEDICINE_NAME'].dropna().astype(str).str.strip())
            self.generic_names.update(df['GENERIC_NAME'].dropna().astype(str).str.strip())

    def correct(self, text, min_length=4, trusted_only=False):
        """
        Correct OCR text to a known drug name.

        trusted_only=True: only alias, common drug, or exact match.
        trusted_only=False: also fuzzy against full dictionary.
        """
        text = text.strip()
        if not text or len(text) < min_length:
            return self._no_match(text)

        text_lower = text.lower()
        if text_lower in BLACKLIST:
            return self._no_match(text)

        text_norm = normalize(text)

        # === STAGE 0: MANUAL ALIASES ===
        if text_lower in MANUAL_ALIASES:
            return self._match(MANUAL_ALIASES[text_lower], 0, True, "alias")
        if text_norm in MANUAL_ALIASES_NORM:
            return self._match(MANUAL_ALIASES_NORM[text_norm], 0, True, "alias")

        # === STAGE 1: EXACT (normalized) ===
        if text_norm in self.brand_norm:
            return self._match(self.brand_norm[text_norm], 0, False, "exact")
        if text_norm in self.generic_norm:
            return self._match(self.generic_norm[text_norm], 0, False, "exact_generic")

        # === STAGE 2: COMMON DRUG LIST (also works for trusted) ===
        if text_norm in COMMON_DRUGS_NORM:
            return self._match(COMMON_DRUGS_NORM[text_norm], 0, False, "common")

        # If trusted_only, stop here
        if trusted_only:
            return self._no_match(text)

        # === STAGE 3: PREFIX (long words only) ===
        if len(text_norm) >= 6:
            for name_norm, name_orig in self.brand_norm.items():
                if len(name_norm) < 6:
                    continue
                if abs(len(name_norm) - len(text_norm)) > 2:
                    continue
                if name_norm.startswith(text_norm) and len(text_norm) >= 5:
                    return self._match(name_orig, 0, True, "prefix")

        # === STAGE 4: STRICT FUZZY ===
        max_dist = 1 if len(text_norm) < 7 else 2
        best_match = None
        best_dist = max_dist + 1
        best_src = None

        for name_norm, name_orig in self.brand_norm.items():
            if abs(len(name_norm) - len(text_norm)) > max_dist:
                continue
            d = levenshtein_distance(text_norm, name_norm)
            if d < best_dist:
                best_dist = d
                best_match = name_orig
                best_src = "fuzzy"
                if d == 1:
                    break

        if best_match and best_dist <= max_dist:
            return self._match(best_match, best_dist, True, best_src)

        return self._no_match(text)

    def _match(self, corrected, distance, was_corrected, source):
        return {
            "corrected": corrected,
            "matched": True,
            "distance": distance,
            "was_corrected": was_corrected,
            "source": source,
        }

    def _no_match(self, text):
        return {
            "corrected": text,
            "matched": False,
            "distance": None,
            "was_corrected": False,
            "source": None,
        }


if __name__ == "__main__":
    d = DrugDictionary()
    print("\n=== TRUSTED MODE (used in pipeline) ===")
    tests = ["Augmentin", "Aujnenturi", "Enzoflam", "Ennzlrn", "PanD",
             "Hexigel", "Crocin", "Dolo", "Random123", "Fair", "Tith", "Nivotril"]
    for t in tests:
        r = d.correct(t, trusted_only=True)
        mark = "✓" if r["matched"] else "✗"
        print(f"  {mark} '{t}' → '{r['corrected']}' (src={r['source']})")