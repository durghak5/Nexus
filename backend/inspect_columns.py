# backend/inspect_columns.py

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data" / "raw"

files_to_check = [
    "SubstanceMaster.txt",
    "GenericMaster.txt", 
    "BrandMaster.txt",
    "SupplierMaster.txt",
    "DrugFormMaster.txt",
    "RouteOfAdministrationMaster.txt"
]

print("🔍 Checking column names...")
print("=" * 60)

for file in files_to_check:
    file_path = DATA_DIR / file
    if file_path.exists():
        df = pd.read_csv(file_path, sep='\t', nrows=2, encoding='utf-8')
        print(f"\n📄 {file}")
        print(f"   Columns: {df.columns.tolist()}")
        print(f"   Shape: {df.shape}")
    else:
        print(f"\n❌ {file} not found")