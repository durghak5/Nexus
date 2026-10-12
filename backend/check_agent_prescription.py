import os
os.environ["PYTHONIOENCODING"] = "utf-8"

from app.agent.tools import list_prescription_drugs

result = list_prescription_drugs()
print("Found:", result.get("found"))
print("Drugs:", result.get("drugs"))
print("Full:", result)