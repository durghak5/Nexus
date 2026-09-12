# backend/app/services/recommendation_service.py

from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.services.drug_service import DrugService
from app.database.models import Brand, Generic, Substance
import re


class RecommendationService:
    """Service for generating drug recommendations"""

    @staticmethod
    def _extract_ingredients(text: str):
        """Extract ingredient names from a drug description like:
        'Flucret (caffeine and chlorphenamine maleate and paracetamol) 30 mg...'
        Returns a lowercase set of ingredient words for matching.
        """
        if not text:
            return set()
        # Grab text inside parentheses (the ingredients list)
        match = re.search(r'\(([^)]+)\)', text)
        if not match:
            return set()
        inside = match.group(1).lower()
        # Split on ' and ' and '+'
        parts = re.split(r'\s+and\s+|\+', inside)
        return {p.strip() for p in parts if p.strip()}

    @staticmethod
    def get_alternatives_with_savings(db: Session, brand_name: str):
        """Find alternatives by matching ingredient composition (no prices available)."""

        # 1. Find the brand
        brand = db.query(Brand).filter(
            Brand.identifier.ilike(f"%{brand_name}%")
        ).first()

        if not brand:
            return {"error": f"Brand '{brand_name}' not found"}

        # 2. Extract ingredients from the identifier
        target_ingredients = RecommendationService._extract_ingredients(brand.identifier)

        if not target_ingredients:
            return {
                "original_brand": brand.identifier,
                "alternatives": [],
                "total_alternatives": 0,
                "message": "Could not extract composition from brand description"
            }

        # 3. Find candidate brands: simple approach — pull brands that mention
        #    the first ingredient, then filter by ingredient overlap
        primary_ingredient = list(target_ingredients)[0]
        candidates = db.query(Brand).filter(
            Brand.identifier.ilike(f"%{primary_ingredient}%"),
            Brand.identifier != brand.identifier
        ).limit(200).all()

        # 4. Score candidates by ingredient overlap
        scored = []
        for cand in candidates:
            cand_ingredients = RecommendationService._extract_ingredients(cand.identifier)
            if not cand_ingredients:
                continue
            overlap = len(target_ingredients & cand_ingredients)
            union = len(target_ingredients | cand_ingredients)
            similarity = overlap / union if union > 0 else 0
            if similarity >= 0.5:  # at least 50% match
                scored.append((similarity, cand))

        # 5. Sort by similarity descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # 6. Build response
        alternatives = []
        for similarity, cand in scored[:10]:
            alternatives.append({
                "brand_name": cand.identifier,
                "manufacturer": None,        # not available in DISB data
                "price": None,               # not available in DISB data
                "savings": None,
                "savings_percent": None,
                "is_cheaper": None,
                "composition_match": round(similarity * 100, 1)
            })

        return {
            "original_brand": brand.identifier,
            "original_price": None,
            "alternatives": alternatives,
            "total_alternatives": len(alternatives)
        }

    @staticmethod
    def get_brand_composition(db: Session, brand_name: str):
        """Return composition info for a brand (ingredients from the description)."""

        brand = db.query(Brand).filter(
            Brand.identifier.ilike(f"%{brand_name}%")
        ).first()

        if not brand:
            return {"error": f"Brand '{brand_name}' not found"}

        ingredients = list(RecommendationService._extract_ingredients(brand.identifier))

        return {
            "brand": brand.identifier,
            "ingredients": ingredients,
            "dose_form": None,
            "route": None
        }