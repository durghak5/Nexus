# backend/app/api/schemas.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BrandResponse(BaseModel):
    identifier: str
    brand_name: str
    product_identifier: Optional[str] = None
    supplier_identifier: Optional[str] = None
    generic_identifier: Optional[str] = None
    license_number: Optional[str] = None
    license_status: Optional[str] = None
    excipient: Optional[str] = None
    last_updated_on: Optional[datetime] = None

class GenericResponse(BaseModel):
    identifier: str
    generic_name: str
    substance_identifier: Optional[str] = None
    route_of_administration: Optional[str] = None
    dose_form: Optional[str] = None
    therapeutic_role: Optional[str] = None
    indication: Optional[str] = None
    contra_indication: Optional[str] = None
    interaction_with_drugs: Optional[str] = None
    classification_of_drugs: Optional[str] = None
    source_regulatory: Optional[str] = None

class SubstanceResponse(BaseModel):
    identifier: str
    substance_name: str
    cas_number: Optional[str] = None
    unii: Optional[str] = None
    substance_description: Optional[str] = None
    molecular_weight: Optional[str] = None
    toxicity: Optional[str] = None
    molecular_formula: Optional[str] = None

class SearchResponse(BaseModel):
    brands: List[BrandResponse]
    generics: List[GenericResponse]
    substances: List[SubstanceResponse]

class AlternativeBrand(BaseModel):
    brand_name: str
    manufacturer: Optional[str] = None
    price: Optional[float] = None
    savings: Optional[float] = None
    savings_percent: Optional[float] = None
    is_cheaper: Optional[bool] = None
    composition_match: Optional[float] = None

class RecommendationResponse(BaseModel):
    original_brand: str
    original_price: Optional[float] = None
    alternatives: List[AlternativeBrand]
    total_alternatives: int
    message: Optional[str] = None

class CompositionResponse(BaseModel):
    brand: str
    generic: Optional[dict] = None
    substance: Optional[dict] = None