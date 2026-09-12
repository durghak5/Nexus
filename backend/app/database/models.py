# backend/app/database/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from .connection import Base

class Substance(Base):
    """Active ingredients/substances"""
    __tablename__ = 'substances'
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(500), unique=True, index=True)
    substance_name = Column(String(500), nullable=False)
    cas_number = Column(String(500))
    unii = Column(Text)  # Can be long descriptions
    substance_description = Column(Text)
    molecular_weight = Column(Text)
    toxicity = Column(Text)
    smile = Column(Text)
    inchi = Column(Text)
    iupac_name = Column(Text)
    molecular_formula = Column(String(500))
    last_updated_on = Column(DateTime)

class Generic(Base):
    """Generic drug information"""
    __tablename__ = 'generics'
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(500), unique=True, index=True)
    generic_name = Column(String(500), nullable=False)
    substance_identifier = Column(String(500))
    route_of_administration = Column(String(500))
    dose_form = Column(String(500))
    therapeutic_role = Column(Text)
    indication = Column(Text)
    contra_indication = Column(Text)
    interaction_with_drugs = Column(Text)
    classification_of_drugs = Column(Text)
    source_regulatory = Column(String(500))
    last_updated_on = Column(DateTime)

class Supplier(Base):
    """Manufacturers/suppliers"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(500), unique=True, index=True)
    supplier_name = Column(String(500), nullable=False)
    country = Column(String(500))

class Brand(Base):
    """Brand/product information"""
    __tablename__ = 'brands'
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(500), unique=True, index=True)
    brand_name = Column(String(500), nullable=False)
    product_identifier = Column(String(500))
    supplier_identifier = Column(String(500))
    generic_identifier = Column(String(500))
    license_number = Column(String(500))
    license_status = Column(String(500))
    excipient = Column(Text)
    last_updated_on = Column(DateTime)

class DrugForm(Base):
    """Drug forms (Tablet, Injection, etc.)"""
    __tablename__ = 'drug_forms'
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(500), unique=True, index=True)
    dose_form = Column(String(500), nullable=False)

class RouteOfAdministration(Base):
    """Routes of administration"""
    __tablename__ = 'routes_of_administration'
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(500), unique=True, index=True)
    route_name = Column(String(500), nullable=False)

class Composition(Base):
    """For backward compatibility"""
    __tablename__ = 'compositions'
    
    id = Column(Integer, primary_key=True, index=True)
    brand_code = Column(String(500))
    ingredient_code = Column(String(500))
    ingredient_name = Column(String(500))
    strength = Column(String(500))
    unit = Column(String(500))

class Prescription(Base):
    """Prescription records"""
    __tablename__ = 'prescriptions'
    
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(500))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    ocr_status = Column(String(20), default='PENDING')
    confidence_score = Column(Float)
    processed_text = Column(Text)