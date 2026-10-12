from app.database.connection import SessionLocal
from app.database.models import Prescription

db = SessionLocal()
count = db.query(Prescription).count()
print(f"Prescriptions in DB: {count}")

for r in db.query(Prescription).order_by(Prescription.id.desc()).limit(3):
    text = r.processed_text or ""
    snippet = text[:120].replace("\n", " ")
    print(f"  #{r.id} | {r.ocr_status} | {snippet}")

db.close()