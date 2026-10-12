"""
OCR API endpoints.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import shutil
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.ocr.full_prescription import FullPrescriptionPipeline
from app.services.recommendation_service import RecommendationService


router = APIRouter(prefix="/api/v1/ocr", tags=["OCR"])


# Lazy-loaded pipeline (heavy to initialize)
_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        print("🔧 Initializing OCR pipeline (first request)...")
        _pipeline = FullPrescriptionPipeline()
    return _pipeline


@router.post("/process")
async def process_prescription(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a prescription image and get:
    - extracted drug names
    - recommendations (alternatives)
    - confidence levels
    """
    # Validate file
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Save upload
    upload_dir = PROJECT_ROOT / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = (file.filename or "prescription").replace(" ", "_")
    file_path = upload_dir / f"{timestamp}_{safe_name}"

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Run OCR pipeline
    try:
        pipeline = get_pipeline()
        ocr_result = pipeline.process(str(file_path), verbose=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

    # For each detected drug, get recommendations
    drugs_with_recs = []
    for drug in ocr_result["drugs"]:
        drug_info = {
            "name": drug["name"],
            "raw_text": drug["raw_text"],
            "confidence": drug["confidence"],
            "source": drug["source"],
            "recommendations": [],
        }

        # Try to find alternatives
        try:
            rec = RecommendationService.get_alternatives_with_savings(db, drug["name"])
            if "error" not in rec:
                drug_info["recommendations"] = rec.get("alternatives", [])[:5]
        except Exception as e:
            print(f"⚠️ Recommendation error for '{drug['name']}': {e}")

        drugs_with_recs.append(drug_info)
        # Save to database so the agent can access it later
    import json
    from datetime import datetime as _dt
    from app.database.models import Prescription as PrescriptionModel

    try:
        db_prescription = PrescriptionModel(
            image_path=str(file_path),
            uploaded_at=_dt.utcnow(),
            ocr_status="COMPLETED",
            confidence_score=0.99,
            processed_text=json.dumps({
                "drugs": [{"name": d["name"], "confidence": d["confidence"]} for d in drugs_with_recs],
                "source": ocr_result.get("source", "gemini"),
            }),
        )
        db.add(db_prescription)
        db.commit()
        db.refresh(db_prescription)
        print(f"✅ Saved prescription #{db_prescription.id} with {len(drugs_with_recs)} drugs")
    except Exception as e:
        print(f"⚠️  Could not save prescription: {e}")
        db.rollback()
    return {
        "success": True,
        "file_name": file.filename,
        "total_detected": len(ocr_result["detections"]),
        "total_drugs": ocr_result["count"],
        "drugs": drugs_with_recs,
        "raw_detections": [
            {"text": d["text"], "confidence": d["confidence"]}
            for d in ocr_result["detections"]
        ],
    }


@router.get("/health")
async def ocr_health():
    """Check if OCR pipeline is available."""
    return {"status": "ok", "model": "trocr_finetuned", "ready": _pipeline is not None}