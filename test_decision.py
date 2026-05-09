"""Quick end-to-end sanity check for decision.py."""
import json
from sustainability import get_sustainability_record
from decision import recommend_action


SCENARIOS = [
    {
        "name": "1. Modern A100 GPU, good condition (the headline demo)",
        "perception": {
            "device_class": "GPU",
            "manufacturer": "NVIDIA",
            "model": "A100",
            "visible_text": ["NVIDIA", "A100", "80GB"],
            "condition": "good",
            "form_factor": "PCIe",
            "generation_hint": "modern",
            "data_bearing": False,
            "contains_hazardous": False,
            "completeness": "complete",
            "confidence": 0.92,
            "notes": "PCIe form factor, no visible damage",
        },
    },
    {
        "name": "2. SSD in good condition (data-bearing)",
        "perception": {
            "device_class": "SSD",
            "manufacturer": "Samsung",
            "model": "PM9A3",
            "visible_text": ["SAMSUNG", "PM9A3", "1.92TB"],
            "condition": "good",
            "form_factor": "U.2",
            "generation_hint": "modern",
            "data_bearing": True,
            "contains_hazardous": False,
            "completeness": "complete",
            "confidence": 0.88,
            "notes": "enterprise NVMe drive",
        },
    },
    {
        "name": "3. HDD in poor condition (data-bearing + damaged)",
        "perception": {
            "device_class": "HDD",
            "manufacturer": "Seagate",
            "model": "Exos X16",
            "visible_text": ["SEAGATE", "EXOS"],
            "condition": "poor",
            "form_factor": "3.5\"",
            "generation_hint": "legacy",
            "data_bearing": True,
            "contains_hazardous": False,
            "completeness": "complete",
            "confidence": 0.78,
            "notes": "scratches on label, dented chassis",
        },
    },
    {
        "name": "4. PSU damaged (hard hazard from sustainability data)",
        "perception": {
            "device_class": "PSU",
            "manufacturer": "Corsair",
            "model": "RM850x",
            "visible_text": ["CORSAIR", "850W"],
            "condition": "poor",
            "form_factor": "ATX",
            "generation_hint": "modern",
            "data_bearing": False,
            "contains_hazardous": False,
            "completeness": "complete",
            "confidence": 0.85,
            "notes": "burnt smell, scorched casing",
        },
    },
    {
        "name": "5. Low confidence detection",
        "perception": {
            "device_class": "motherboard",
            "manufacturer": "Unknown",
            "model": "Unknown",
            "visible_text": [],
            "condition": "unknown",
            "form_factor": "ATX",
            "generation_hint": "unknown",
            "data_bearing": False,
            "contains_hazardous": False,
            "completeness": "unknown",
            "confidence": 0.42,
            "notes": "blurry image",
        },
    },
    {
        "name": "6. Cable (low-value, reuse-first default)",
        "perception": {
            "device_class": "cable",
            "manufacturer": "generic",
            "model": "Unknown",
            "visible_text": [],
            "condition": "good",
            "form_factor": "C13",
            "generation_hint": "unknown",
            "data_bearing": False,
            "contains_hazardous": False,
            "completeness": "complete",
            "confidence": 0.91,
            "notes": "standard power cable",
        },
    },
    {
        "name": "7. Undetected (perception failure)",
        "perception": {
            "device_class": "unknown",
            "manufacturer": "Unknown",
            "model": "Unknown",
            "visible_text": [],
            "condition": "unknown",
            "form_factor": "unknown",
            "generation_hint": "unknown",
            "data_bearing": False,
            "contains_hazardous": False,
            "completeness": "unknown",
            "confidence": 0.20,
            "notes": "could not identify",
        },
    },
    {
        "name": "8. RAM, missing major parts",
        "perception": {
            "device_class": "RAM",
            "manufacturer": "Kingston",
            "model": "KSM32RD4/32",
            "visible_text": ["KINGSTON", "DDR4", "32GB"],
            "condition": "fair",
            "form_factor": "DIMM",
            "generation_hint": "modern",
            "data_bearing": False,
            "contains_hazardous": False,
            "completeness": "missing_major_parts",
            "confidence": 0.81,
            "notes": "broken contacts on one side",
        },
    },
    {
        "name": "9. Motherboard with hard hazard (lithium battery flag in sustainability)",
        "perception": {
            "device_class": "motherboard",
            "manufacturer": "Supermicro",
            "model": "X11DPi-N",
            "visible_text": ["SUPERMICRO"],
            "condition": "good",
            "form_factor": "EATX",
            "generation_hint": "modern",
            "data_bearing": False,
            "contains_hazardous": False,
            "completeness": "complete",
            "confidence": 0.90,
            "notes": "server motherboard with onboard CMOS battery",
        },
    },
]


for scenario in SCENARIOS:
    print("=" * 78)
    print(scenario["name"])
    print("=" * 78)
    perception = scenario["perception"]
    sustainability = get_sustainability_record(perception["device_class"])
    decision = recommend_action(perception, sustainability)

    print(f"\nFinal action: {decision['action']}  ({decision['label']}, {decision['color']})")
    print(f"Reason:       {decision['reason']}")
    print(f"CO2 avoided:  {decision['co2_avoided_kg']} kg")
    print(f"Value:        ${decision['value_usd']}")
    print(f"Metals:       {decision['metals_total_g']} g total")
    print(f"Source:       {decision['source']}")
    print("\nRule trace:")
    for step in decision["rule_trace"]:
        print(f"  • {step}")
    print()
