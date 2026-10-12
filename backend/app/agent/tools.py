"""
Agent tools — functions the Gemini agent can call.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from typing import Optional
from app.agent.confidence import (
    score_from_source, score_ai_inference, score_no_match,
    format_confidence,
)
from app.database.connection import SessionLocal
from app.database.models import Prescription
from app.services.drug_service import DrugService
from app.services.recommendation_service import RecommendationService


# ============================================================
# Tool 1: Check drug-drug interaction
# ============================================================
_interaction_db = None


def _load_interactions():
    """Lazy-load the clinical interaction database."""
    global _interaction_db
    if _interaction_db is None:
        try:
            from drug_interaction_mcp.interactions import INTERACTIONS
            _interaction_db = INTERACTIONS
            print(f"✅ Loaded {len(_interaction_db)} clinical interactions")
        except ImportError:
            _interaction_db = []
            print("⚠️ drug_interaction_mcp not available")
    return _interaction_db


def _normalize(name: str) -> str:
    """Lowercase + strip whitespace for matching."""
    return (name or "").strip().lower()


def check_interaction(drug_a: str, drug_b: str) -> dict:
    """
    Check for a known interaction between two drugs.
    Returns: dict with severity, description, mechanism, recommendation, source, confidence.
    """
    if not drug_a or not drug_b:
        return {
            "found": False,
            "severity": "none",
            "message": "Both drug names are required.",
            "confidence": score_no_match(),
        }

    interactions = _load_interactions()
    a_norm = _normalize(drug_a)
    b_norm = _normalize(drug_b)

    # Search through the DB
    for interaction in interactions:
        a_names = [n.lower() for n in interaction.drug_a]
        b_names = [n.lower() for n in interaction.drug_b]

        # Match in either order, partial substring match supported
        def matches(query, names):
            return any(query in n or n in query for n in names)

        hit = (
            (matches(a_norm, a_names) and matches(b_norm, b_names)) or
            (matches(a_norm, b_names) and matches(b_norm, a_names))
        )

        if hit:
            severity = interaction.severity.value if hasattr(interaction.severity, 'value') else str(interaction.severity)
            conf = score_from_source(interaction.source)
            return {
                "found": True,
                "drug_a": drug_a,
                "drug_b": drug_b,
                "severity": severity,
                "description": interaction.description,
                "mechanism": interaction.mechanism,
                "recommendation": interaction.recommendation,
                "source": interaction.source,
                "confidence": conf,
                "confidence_label": format_confidence(conf),
            }

    # Not found in clinical DB
    return {
        "found": False,
        "drug_a": drug_a,
        "drug_b": drug_b,
        "severity": "unknown",
        "message": "No known interaction in our clinical database. This does not guarantee safety.",
        "confidence": score_no_match(),
        "confidence_label": format_confidence(score_no_match()),
    }


# ============================================================
# Tool 2: List drugs from user's last prescription
# ============================================================
def list_prescription_drugs(prescription_id: Optional[int] = None) -> dict:
    """
    Get drugs from a prescription's processed_text (JSON).
    Falls back to the most recent prescription if no ID given.
    """
    import json
    db = SessionLocal()
    try:
        if prescription_id is None:
            prescription = db.query(Prescription).order_by(Prescription.id.desc()).first()
        else:
            prescription = db.query(Prescription).filter(
                Prescription.id == prescription_id
            ).first()

        if not prescription:
            return {"found": False, "drugs": [], "message": "No prescription found."}

        drug_names = []
        seen = set()
        text = prescription.processed_text or ""

        if text:
            try:
                data = json.loads(text)
                items = data.get("drugs", []) if isinstance(data, dict) else data
                if isinstance(items, list):
                    for d in items:
                        name = (d.get("name") if isinstance(d, dict) else str(d)).strip()
                        if name and name.lower() not in seen:
                            seen.add(name.lower())
                            drug_names.append(name)
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "found": True,
            "prescription_id": prescription.id,
            "uploaded_at": prescription.uploaded_at.isoformat() if prescription.uploaded_at else None,
            "drugs": drug_names,
            "count": len(drug_names),
        }
    finally:
        db.close()

# ============================================================
# Tool 3: Find alternative brands
# ============================================================
def find_alternatives(drug_name: str) -> dict:
    """Find alternative brands with same composition."""
    db = SessionLocal()
    try:
        result = RecommendationService.get_alternatives_with_savings(db, drug_name)
        if "error" in result:
            return {"found": False, "message": result["error"], "alternatives": []}
        return {
            "found": True,
            "original": result.get("original_brand"),
            "alternatives": result.get("alternatives", [])[:5],
            "count": len(result.get("alternatives", [])),
        }
    finally:
        db.close()


# ============================================================
# Tool 4: Get general drug info
# ============================================================
def get_drug_info(drug_name: str) -> dict:
    """Search for drug info in DISB."""
    db = SessionLocal()
    try:
        results = DrugService.search_by_name(db, drug_name, limit=5)
        brands = [{"name": b.identifier, "id": b.id} for b in results.get("brands", [])]
        generics = [{"name": g.identifier, "id": g.id} for g in results.get("generics", [])]
        substances = [{"name": s.substance_name, "id": s.id} for s in results.get("substances", [])]
        return {
            "found": bool(brands or generics or substances),
            "query": drug_name,
            "brands": brands,
            "generics": generics,
            "substances": substances,
        }
    finally:
        db.close()


# ============================================================
# Tool registry for Gemini function calling
# ============================================================
TOOL_FUNCTIONS = {
    "check_interaction": check_interaction,
    "list_prescription_drugs": list_prescription_drugs,
    "find_alternatives": find_alternatives,
    "get_drug_info": get_drug_info,
}


# Gemini function-calling declarations
TOOL_DECLARATIONS = [
    {
        "name": "check_interaction",
        "description": "Check for a known drug-drug interaction between two drugs.",
        "parameters": {
            "type": "object",
            "properties": {
                "drug_a": {"type": "string", "description": "First drug name"},
                "drug_b": {"type": "string", "description": "Second drug name"},
            },
            "required": ["drug_a", "drug_b"],
        },
    },
    {
        "name": "list_prescription_drugs",
        "description": (
    "Retrieve drug names from the user's most recent uploaded prescription. "
    "Call this tool IMMEDIATELY when the user references THEIR OWN prescription "
    "using phrases like: 'my prescription', 'my last prescription', 'check my prescription', "
    "'the drugs I uploaded', 'review my last prescription', 'what did I upload', "
    "'the medicines I'm taking'. Do NOT ask the user for drug names — just call this tool "
    "with no arguments and use the returned drug list. Returns a JSON with 'drugs' array."
),
        "parameters": {
            "type": "object",
            "properties": {
                "prescription_id": {"type": "integer", "description": "Optional prescription ID"},
            },
        },
    },
    {
        "name": "find_alternatives",
        "description": "Find alternative brands with the same composition as the given drug.",
        "parameters": {
            "type": "object",
            "properties": {
                "drug_name": {"type": "string", "description": "Drug brand name"},
            },
            "required": ["drug_name"],
        },
    },
    {
        "name": "get_drug_info",
        "description": "Get general information about a drug from the DISB database.",
        "parameters": {
            "type": "object",
            "properties": {
                "drug_name": {"type": "string", "description": "Drug name to search"},
            },
            "required": ["drug_name"],
        },
    },
]


def execute_tool(name: str, args: dict) -> dict:
    """Dispatch a Gemini tool call to the right Python function."""
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    try:
        return fn(**args)
    except Exception as e:
        return {"error": f"Tool '{name}' failed: {e}"}