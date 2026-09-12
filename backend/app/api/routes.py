# backend/app/api/routes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.services.drug_service import DrugService
from app.services.recommendation_service import RecommendationService
from app.api.schemas import (
    SearchResponse, RecommendationResponse, 
    CompositionResponse, BrandResponse
)

router = APIRouter(prefix="/api/v1/drugs", tags=["Drugs"])

@router.get("/search", response_model=SearchResponse)
async def search_drugs(
    query: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(10, ge=1, le=50, description="Max results per category"),
    db: Session = Depends(get_db)
):
    """Search for drugs by name (brand, generic, or substance)"""
    results = DrugService.search_by_name(db, query, limit)
    return results

@router.get("/brand/{brand_identifier}", response_model=BrandResponse)
async def get_brand(
    brand_identifier: str,
    db: Session = Depends(get_db)
):
    """Get complete brand information"""
    brand = DrugService.get_brand_by_id(db, brand_identifier)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    brand_name: str = Query(..., description="Brand name to find alternatives for"),
    db: Session = Depends(get_db)
):
    """Get alternative brands with same composition"""
    result = RecommendationService.get_alternatives_with_savings(db, brand_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/composition", response_model=CompositionResponse)
async def get_composition(
    brand_name: str = Query(..., description="Brand name to get composition for"),
    db: Session = Depends(get_db)
):
    """Get the composition (substances) of a brand"""
    result = RecommendationService.get_brand_composition(db, brand_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/brands/by-generic/{generic_identifier}")
async def get_brands_by_generic(
    generic_identifier: str,
    db: Session = Depends(get_db)
):
    """Get all brands for a specific generic"""
    brands = db.query(Brand).filter(
        Brand.generic_identifier == generic_identifier
    ).all()
    
    if not brands:
        raise HTTPException(status_code=404, detail="No brands found")
    
    return {
        "generic_identifier": generic_identifier,
        "brands": [b.brand_name for b in brands],
        "count": len(brands)
    }

@router.get("/generics/by-substance/{substance_identifier}")
async def get_generics_by_substance(
    substance_identifier: str,
    db: Session = Depends(get_db)
):
    """Get all generics for a specific substance"""
    generics = db.query(Generic).filter(
        Generic.substance_identifier == substance_identifier
    ).all()
    
    if not generics:
        raise HTTPException(status_code=404, detail="No generics found")
    
    return {
        "substance_identifier": substance_identifier,
        "generics": [g.generic_name for g in generics],
        "count": len(generics)
    }