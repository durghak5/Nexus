"""
Confidence scoring based on evidence source.
Higher score = more trustworthy source.
"""


# Confidence by source keyword found in the interaction database
SOURCE_CONFIDENCE_MAP = {
    "fda drug label": 0.95,
    "fda label": 0.95,
    "fda": 0.93,
    "nih dailymed": 0.90,
    "dailymed": 0.90,
    "nih": 0.88,
    "clinical study": 0.85,
    "peer-reviewed": 0.85,
    "pubmed": 0.83,
    "case report": 0.65,
    "case series": 0.60,
    "theoretical": 0.45,
    "in vitro": 0.55,
    "animal study": 0.50,
}


# Fallback confidence when source is unknown
DEFAULT_CLINICAL_CONFIDENCE = 0.75

# Confidence when using AI inference (no clinical match)
AI_INFERENCE_CONFIDENCE = 0.55

# Confidence when nothing is found
NO_MATCH_CONFIDENCE = 0.40


def score_from_source(source: str) -> float:
    """
    Given a source string like 'FDA Drug Label — Warfarin',
    return a confidence score 0.0-1.0.
    """
    if not source:
        return DEFAULT_CLINICAL_CONFIDENCE

    source_lower = source.lower()
    for keyword, score in SOURCE_CONFIDENCE_MAP.items():
        if keyword in source_lower:
            return score

    # Unknown source but still from clinical DB
    return DEFAULT_CLINICAL_CONFIDENCE


def confidence_label(score: float) -> str:
    """Human-readable label for a confidence score."""
    if score >= 0.90:
        return "Very High"
    if score >= 0.75:
        return "High"
    if score >= 0.60:
        return "Moderate"
    if score >= 0.40:
        return "Low"
    return "Very Low"


def format_confidence(score: float) -> str:
    """Format as '92% (High)'."""
    return f"{int(score * 100)}% ({confidence_label(score)})"


def score_ai_inference() -> float:
    """Confidence when Gemini has to infer without clinical DB."""
    return AI_INFERENCE_CONFIDENCE


def score_no_match() -> float:
    """Confidence when nothing is found at all."""
    return NO_MATCH_CONFIDENCE