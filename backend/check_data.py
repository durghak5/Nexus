# backend/check_data.py

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal
from app.database.models import Substance, Generic, Supplier, Brand, DrugForm, RouteOfAdministration

def check_data():
    session = SessionLocal()
    try:
        print("📊 DATABASE VERIFICATION")
        print("=" * 50)
        
        # Counts
        print(f"✅ Substances:  {session.query(Substance).count():,}")
        print(f"✅ Generics:    {session.query(Generic).count():,}")
        print(f"✅ Suppliers:   {session.query(Supplier).count():,}")
        print(f"✅ Brands:      {session.query(Brand).count():,}")
        print(f"✅ Drug Forms:  {session.query(DrugForm).count():,}")
        print(f"✅ Routes:      {session.query(RouteOfAdministration).count():,}")
        
        # Sample data
        print("\n📋 Sample Substances:")
        for s in session.query(Substance).limit(3):
            print(f"  - {s.identifier}: {s.substance_name}")
        
        print("\n📋 Sample Generic Drugs:")
        for g in session.query(Generic).limit(3):
            print(f"  - {g.identifier}: {g.generic_name}")
        
        print("\n📋 Sample Brands:")
        for b in session.query(Brand).limit(3):
            print(f"  - {b.identifier}: {b.brand_name}")
            
        print("\n📋 Sample Suppliers:")
        for s in session.query(Supplier).limit(3):
            print(f"  - {s.identifier}: {s.supplier_name} ({s.country})")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_data()