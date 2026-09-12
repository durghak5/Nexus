# backend/init_db.py

import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import engine, Base
from app.database.models import (
    Substance, Generic, Supplier, Brand, 
    DrugForm, RouteOfAdministration, Composition, Prescription
)

def main():
    print("🚀 Initializing Medical Prescription OCR Database")
    print("=" * 60)
    
    try:
        print("📊 Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        print("📊 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        
        print("\n📋 Tables created:")
        for table in Base.metadata.tables:
            print(f"  - {table}")
            
        print("\n✅ Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()