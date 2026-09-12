# backend/load_data.py

import sys
import os
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import re
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal, engine
from app.database.models import (
    Base, Substance, Generic, Supplier, Brand, 
    DrugForm, RouteOfAdministration
)

DATA_DIR = Path(__file__).parent / "data" / "raw"

def clean_value(value):
    """Clean string values"""
    if pd.isna(value):
        return ''
    if isinstance(value, float) and math.isnan(value):
        return ''
    return str(value).strip()

def clean_identifier(identifier):
    """Clean identifier by removing .0 suffix and whitespace"""
    if pd.isna(identifier):
        return ''
    if isinstance(identifier, float) and math.isnan(identifier):
        return ''
    identifier = str(identifier).strip()
    if identifier.endswith('.0'):
        identifier = identifier[:-2]
    return identifier

def parse_date(date_str):
    """Parse date string to datetime"""
    if pd.isna(date_str) or not date_str:
        return None
    if isinstance(date_str, float) and math.isnan(date_str):
        return None
    try:
        if isinstance(date_str, (int, float)):
            date_str = str(int(date_str))
        if isinstance(date_str, str) and date_str.isdigit() and len(date_str) == 8:
            return datetime.strptime(date_str, '%Y%m%d')
        return pd.to_datetime(date_str)
    except:
        return None

def load_substances(session, file_path):
    """Load SubstanceMaster.txt - Skip duplicates"""
    print(f"\n📖 Loading {file_path.name}...")
    
    if not file_path.exists():
        print(f"❌ File not found")
        return 0
    
    try:
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8',
                        on_bad_lines='skip', engine='python')
        
        print(f"📊 Found {len(df)} records")
        
        # Get existing identifiers
        existing_ids = {s.identifier for s in session.query(Substance.identifier).all()}
        print(f"📊 Found {len(existing_ids)} existing substances in database")
        
        added = 0
        skipped_duplicate = 0
        
        for idx, row in df.iterrows():
            identifier = clean_value(row.get('Identifier'))
            
            # Skip if identifier already exists
            if identifier in existing_ids:
                skipped_duplicate += 1
                continue
            
            substance_data = {
                'identifier': identifier,
                'substance_name': clean_value(row.get('Substance Name')),
                'cas_number': clean_value(row.get('CAS Number')),
                'unii': clean_value(row.get('UNII')),
                'substance_description': clean_value(row.get('Substance Description')),
                'molecular_weight': clean_value(row.get('Molecular Weight')),
                'toxicity': clean_value(row.get('Toxicity')),
                'smile': clean_value(row.get('SMILE')),
                'inchi': clean_value(row.get('InChI')),
                'iupac_name': clean_value(row.get('IUPAC Name')),
                'molecular_formula': clean_value(row.get('Molecular Formula')),
                'last_updated_on': parse_date(row.get('last_updated_on')),
            }
            
            if not substance_data['identifier'] or not substance_data['substance_name']:
                continue
            
            session.add(Substance(**substance_data))
            added += 1
            existing_ids.add(identifier)
            
            if added % 200 == 0:
                session.commit()
                print(f"   ✅ Added {added} substances (skipped {skipped_duplicate} duplicates)...")
        
        session.commit()
        print(f"✅ Added {added} substances (skipped {skipped_duplicate} duplicates)")
        return added
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return 0

def load_suppliers(session, file_path):
    """Load SupplierMaster.txt"""
    print(f"\n📖 Loading {file_path.name}...")
    
    if not file_path.exists():
        print(f"❌ File not found")
        return 0
    
    try:
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8',
                        on_bad_lines='skip', engine='python')
        
        print(f"📊 Found {len(df)} records")
        
        added = 0
        for _, row in df.iterrows():
            supplier_data = {
                'identifier': clean_value(row.get('Identifier')),
                'supplier_name': clean_value(row.get('Supplier Name')),
                'country': clean_value(row.get('Country')),
            }
            
            if not supplier_data['identifier'] or not supplier_data['supplier_name']:
                continue
            
            existing = session.query(Supplier).filter(
                Supplier.identifier == supplier_data['identifier']
            ).first()
            
            if not existing:
                session.add(Supplier(**supplier_data))
                added += 1
            
            if added % 1000 == 0:
                session.commit()
                print(f"   ✅ Added {added} suppliers...")
        
        session.commit()
        print(f"✅ Added {added} suppliers")
        return added
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return 0

def load_drug_forms(session, file_path):
    """Load DrugFormMaster.txt"""
    print(f"\n📖 Loading {file_path.name}...")
    
    if not file_path.exists():
        print(f"❌ File not found")
        return 0
    
    try:
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8',
                        on_bad_lines='skip', engine='python')
        
        print(f"📊 Found {len(df)} records")
        
        added = 0
        for _, row in df.iterrows():
            form_data = {
                'identifier': clean_value(row.get('Identifier')),
                'dose_form': clean_value(row.get('Dose Form')),
            }
            
            if not form_data['identifier'] or not form_data['dose_form']:
                continue
            
            existing = session.query(DrugForm).filter(
                DrugForm.identifier == form_data['identifier']
            ).first()
            
            if not existing:
                session.add(DrugForm(**form_data))
                added += 1
        
        session.commit()
        print(f"✅ Added {added} drug forms")
        return added
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return 0

def load_routes(session, file_path):
    """Load RouteOfAdministrationMaster.txt"""
    print(f"\n📖 Loading {file_path.name}...")
    
    if not file_path.exists():
        print(f"❌ File not found")
        return 0
    
    try:
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8',
                        on_bad_lines='skip', engine='python')
        
        print(f"📊 Found {len(df)} records")
        
        added = 0
        for _, row in df.iterrows():
            route_data = {
                'identifier': clean_value(row.get('Identifier')),
                'route_name': clean_value(row.get('RouteOfAdministration')),
            }
            
            if not route_data['identifier'] or not route_data['route_name']:
                continue
            
            existing = session.query(RouteOfAdministration).filter(
                RouteOfAdministration.identifier == route_data['identifier']
            ).first()
            
            if not existing:
                session.add(RouteOfAdministration(**route_data))
                added += 1
        
        session.commit()
        print(f"✅ Added {added} routes")
        return added
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return 0

def load_generics(session, file_path):
    """Load GenericMaster.txt - Skip duplicates"""
    print(f"\n📖 Loading {file_path.name}...")
    
    if not file_path.exists():
        print(f"❌ File not found")
        return 0
    
    try:
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8',
                        on_bad_lines='skip', engine='python')
        
        print(f"📊 Found {len(df)} records")
        
        # Get existing identifiers
        existing_ids = {g.identifier for g in session.query(Generic.identifier).all()}
        print(f"📊 Found {len(existing_ids)} existing generics in database")
        
        added = 0
        skipped_duplicate = 0
        
        for _, row in df.iterrows():
            identifier = clean_value(row.get('Identifier'))
            
            # Skip if identifier already exists
            if identifier in existing_ids:
                skipped_duplicate += 1
                continue
            
            generic_data = {
                'identifier': identifier,
                'generic_name': clean_value(row.get('Generic Name')),
                'substance_identifier': clean_identifier(row.get('Substance Identifier')),
                'route_of_administration': clean_value(row.get('Route of Administration')),
                'dose_form': clean_value(row.get('Dose Form')),
                'therapeutic_role': clean_value(row.get('Therapeutic Role')),
                'indication': clean_value(row.get('Indication')),
                'contra_indication': clean_value(row.get('Contra Indication')),
                'interaction_with_drugs': clean_value(row.get('Interaction with Drugs')),
                'classification_of_drugs': clean_value(row.get('Classification of Drugs')),
                'source_regulatory': clean_value(row.get('Source/ Regulatory')),
                'last_updated_on': parse_date(row.get('last_updated_on')),
            }
            
            if not generic_data['identifier'] or not generic_data['generic_name']:
                continue
            
            session.add(Generic(**generic_data))
            added += 1
            existing_ids.add(identifier)
            
            if added % 500 == 0:
                session.commit()
                print(f"   ✅ Added {added} generics (skipped {skipped_duplicate} duplicates)...")
        
        session.commit()
        print(f"✅ Added {added} generics (skipped {skipped_duplicate} duplicates)")
        return added
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return 0

def load_brands(session, file_path):
    """Load BrandMaster.txt - Skip duplicates"""
    print(f"\n📖 Loading {file_path.name}...")
    
    if not file_path.exists():
        print(f"❌ File not found")
        return 0
    
    try:
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8',
                        on_bad_lines='skip', engine='python')
        
        print(f"📊 Found {len(df)} records")
        
        # Get existing identifiers to check for duplicates
        existing_ids = {b.identifier for b in session.query(Brand.identifier).all()}
        print(f"📊 Found {len(existing_ids)} existing brands in database")
        
        added = 0
        skipped_duplicate = 0
        
        for _, row in df.iterrows():
            identifier = clean_value(row.get('Identifier'))
            
            # Skip if identifier already exists
            if identifier in existing_ids:
                skipped_duplicate += 1
                continue
            
            brand_data = {
                'identifier': identifier,
                'brand_name': clean_value(row.get('Brand Name')),
                'product_identifier': clean_value(row.get('Product Identifier')),
                'supplier_identifier': clean_identifier(row.get('Supplier Identifier')),
                'generic_identifier': clean_identifier(row.get('Generic Identifier')),
                'license_number': clean_value(row.get('License Number')),
                'license_status': clean_value(row.get('License Status')),
                'excipient': clean_value(row.get('Excipient')),
                'last_updated_on': parse_date(row.get('last_updated_on')),
            }
            
            if not brand_data['identifier'] or not brand_data['brand_name']:
                continue
            
            session.add(Brand(**brand_data))
            added += 1
            existing_ids.add(identifier)  # Add to set to prevent duplicates in same batch
            
            if added % 500 == 0:
                session.commit()
                print(f"   ✅ Added {added} brands (skipped {skipped_duplicate} duplicates)...")
        
        session.commit()
        print(f"✅ Added {added} brands (skipped {skipped_duplicate} duplicates)")
        return added
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return 0

def main():
    print("🚀 DISB Data Loader")
    print("=" * 60)
    
    if not DATA_DIR.exists():
        print(f"❌ Data directory not found: {DATA_DIR}")
        return
    
    session = SessionLocal()
    
    try:
        # First, initialize database with fresh tables
        print("\n📊 Initializing database...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created!")
        
        print("\n📂 Loading data...")
        
        total = {}
        
        # Load all files
        total['substances'] = load_substances(session, DATA_DIR / "SubstanceMaster.txt")
        total['suppliers'] = load_suppliers(session, DATA_DIR / "SupplierMaster.txt")
        total['drug_forms'] = load_drug_forms(session, DATA_DIR / "DrugFormMaster.txt")
        total['routes'] = load_routes(session, DATA_DIR / "RouteOfAdministrationMaster.txt")
        total['generics'] = load_generics(session, DATA_DIR / "GenericMaster.txt")
        total['brands'] = load_brands(session, DATA_DIR / "BrandMaster.txt")
        
        print("\n" + "=" * 60)
        print("📊 LOADING SUMMARY")
        print("=" * 60)
        for key, count in total.items():
            print(f"✅ {key.capitalize()}: {count}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()