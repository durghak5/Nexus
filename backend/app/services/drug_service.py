# backend/app/services/drug_service.py

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.database.models import Substance, Generic, Supplier, Brand

class DrugService:
    """Service for drug-related operations"""
    
    @staticmethod
    def search_by_name(db: Session, query: str, limit: int = 20):
        """Search for drugs by name (brand or generic)"""
        search_term = f"%{query}%"
        
        # Search in brands
        brands = db.query(Brand).filter(
            or_(
                Brand.brand_name.ilike(search_term),
                Brand.identifier.ilike(search_term)
            )
        ).limit(limit).all()
        
        # Search in generics
        generics = db.query(Generic).filter(
            or_(
                Generic.generic_name.ilike(search_term),
                Generic.identifier.ilike(search_term)
            )
        ).limit(limit).all()
        
        # Search in substances
        substances = db.query(Substance).filter(
            or_(
                Substance.substance_name.ilike(search_term),
                Substance.identifier.ilike(search_term)
            )
        ).limit(limit).all()
        
        return {
            "brands": brands,
            "generics": generics,
            "substances": substances
        }
    
    @staticmethod
    def get_brand_by_id(db: Session, brand_id: str):
        """Get complete brand information"""
        return db.query(Brand).filter(Brand.identifier == brand_id).first()
    
    @staticmethod
    def get_generic_by_id(db: Session, generic_id: str):
        """Get complete generic information"""
        return db.query(Generic).filter(Generic.identifier == generic_id).first()
    
    @staticmethod
    def get_substance_by_id(db: Session, substance_id: str):
        """Get complete substance information"""
        return db.query(Substance).filter(Substance.identifier == substance_id).first()
    
    @staticmethod
    def find_alternatives(db: Session, brand_id: str, max_results: int = 10):
        """Find alternative brands with same generic composition"""
        # Get the brand
        brand = db.query(Brand).filter(Brand.identifier == brand_id).first()
        if not brand:
            return []
        
        # Find all brands with the same generic
        alternatives = db.query(Brand).filter(
            and_(
                Brand.generic_identifier == brand.generic_identifier,
                Brand.identifier != brand_id
            )
        ).limit(max_results).all()
        
        return alternatives