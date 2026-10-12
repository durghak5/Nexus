with open("app/api/ocr_routes.py", "r", encoding="utf-8") as f:
    content = f.read()

keywords = ["PrescriptionModel", "processed_text", "db.add", "db.commit"]
for kw in keywords:
    print(f"{kw}: {'✅ FOUND' if kw in content else '❌ MISSING'}")