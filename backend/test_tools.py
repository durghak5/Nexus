"""
Test script for the agent tools.
"""

from app.agent.tools import check_interaction, find_alternatives, get_drug_info, list_prescription_drugs


def print_dict(title, d):
    print(f"\n=== {title} ===")
    for k, v in d.items():
        if isinstance(v, list):
            print(f"  {k}: [{len(v)} items]")
            for item in v[:3]:
                print(f"    - {item}")
        else:
            print(f"  {k}: {v}")


def main():
    # Test 1: Known interaction (should be in clinical DB)
    r1 = check_interaction("Warfarin", "Aspirin")
    print_dict("Warfarin + Aspirin (known danger)", r1)

    # Test 2: Unknown pair (not in DB)
    r2 = check_interaction("Augmentin", "Pan-D")
    print_dict("Augmentin + Pan-D (not in DB)", r2)

    # Test 3: Alternatives
    r3 = find_alternatives("Augmentin")
    print(f"\n=== Alternatives for Augmentin ===")
    print(f"  Found: {r3.get('count', 0)} alternatives")
    for alt in r3.get("alternatives", [])[:3]:
        print(f"    - {alt.get('brand_name', '')[:80]}")

    # Test 4: Drug info
    r4 = get_drug_info("Paracetamol")
    print(f"\n=== Info for Paracetamol ===")
    print(f"  Brands: {len(r4.get('brands', []))}")
    print(f"  Generics: {len(r4.get('generics', []))}")
    print(f"  Substances: {len(r4.get('substances', []))}")

    # Test 5: Prescription drugs
    r5 = list_prescription_drugs()
    print(f"\n=== Last Prescription ===")
    print(f"  Found: {r5.get('found')}")
    print(f"  Drugs: {r5.get('drugs', [])}")


if __name__ == "__main__":
    main()