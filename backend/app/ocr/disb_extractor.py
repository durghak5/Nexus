"""
Extract short brand names from DISB identifiers.

DISB stores brands as full descriptions like:
    "Augmentin (amoxicillin and clavulanate potassium) 625 mg oral tablet"

We extract the leading word(s) as the short brand name:
    "Augmentin"

This gives us a usable dictionary for matching OCR output.
"""

import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database.connection import SessionLocal
from app.database.models import Brand


# Words that indicate end of brand name
STOP_WORDS_AFTER_BRAND = {
    'tablet', 'tab', 'capsule', 'cap', 'syrup', 'syp', 'suspension',
    'injection', 'inj', 'cream', 'ointment', 'gel', 'lotion', 'drops',
    'oral', 'iv', 'im', 'solution', 'powder', 'granules',
}


def extract_short_name(identifier: str) -> str:
    """
    Extract the leading brand word(s) from a DISB identifier.

    Examples:
        "Augmentin (amoxicillin...) 625 mg oral tablet" -> "Augmentin"
        "Pan-D capsule" -> "Pan-D"
        "Dolo 650 tablet" -> "Dolo"
    """
    if not identifier:
        return ""

    text = identifier.strip()

    # Take everything before the first parenthesis
    if '(' in text:
        text = text.split('(')[0].strip()

    # Take everything before the first comma
    if ',' in text:
        text = text.split(',')[0].strip()

    # Split into words
    words = text.split()

    # Take first 1-2 words, stopping at:
    #   - a dose marker (number + unit)
    #   - a stop word (tablet, capsule, etc.)
    #   - a number
    brand_words = []
    for word in words[:3]:  # look at first 3 words max
        # Stop if word is a number
        if re.match(r'^\d', word):
            break
        # Stop if word contains only numbers/units
        if re.match(r'^\d+(mg|ml|g|mcg|iu|%)?$', word, re.IGNORECASE):
            break
        # Stop if word is a stop word
        if word.lower() in STOP_WORDS_AFTER_BRAND:
            break
        brand_words.append(word)
        if len(brand_words) >= 2:
            break

    return ' '.join(brand_words).strip()


def build_disb_short_names():
    """Load all brands from DISB and return set of short names."""
    print("📚 Extracting short brand names from DISB...")
    db = SessionLocal()
    try:
        brands = db.query(Brand.identifier).all()
        short_names = set()
        for (identifier,) in brands:
            if not identifier:
                continue
            short = extract_short_name(identifier)
            if short and len(short) >= 3:
                short_names.add(short)
        print(f"   ✅ Extracted {len(short_names)} unique short names")
        return short_names
    finally:
        db.close()


if __name__ == "__main__":
    names = build_disb_short_names()
    sample = sorted(names)[:50]
    print(f"\n📋 First 50 short names:")
    for n in sample:
        print(f"   - {n}")

    # Test specific drugs
    print(f"\n🎯 Testing known Indian drugs:")
    for test in ['Augmentin', 'Enzoflam', 'PanD', 'Hexigel', 'Paracetamol', 'Dolo']:
        found = test.lower() in {n.lower() for n in names}
        print(f"   {'✅' if found else '❌'} {test}")