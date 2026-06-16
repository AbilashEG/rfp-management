"""
Seeds the rfp-suppliers DynamoDB table with 8 mock automotive suppliers.
Idempotent — safe to re-run (uses put_item which overwrites duplicates).
Usage: python setup/seed_data.py
"""
import boto3
from decimal import Decimal
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REGION, SUPPLIERS_TABLE

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table    = dynamodb.Table(SUPPLIERS_TABLE)

SUPPLIERS = [
    {"supplier_id": "SUP001", "name": "BrakeTech Industries",
     "category": "brake_systems",   "region": "Chennai",
     "certifications": ["ISO9001", "IATF16949"],
     "rating": Decimal("4.8"), "past_delivery_score": Decimal("95"),
     "contact_email": "rfp@braketech-mock.com",  "status": "active"},

    {"supplier_id": "SUP002", "name": "PrecisionParts Co",
     "category": "brake_systems",   "region": "Pune",
     "certifications": ["ISO9001"],
     "rating": Decimal("4.2"), "past_delivery_score": Decimal("88"),
     "contact_email": "rfp@precisionparts-mock.com", "status": "active"},

    {"supplier_id": "SUP003", "name": "AutoSensor Global",
     "category": "sensors",         "region": "Bangalore",
     "certifications": ["ISO9001", "IATF16949", "ISO14001"],
     "rating": Decimal("4.9"), "past_delivery_score": Decimal("98"),
     "contact_email": "rfp@autosensor-mock.com", "status": "active"},

    {"supplier_id": "SUP004", "name": "SpeedMech Ltd",
     "category": "brake_systems",   "region": "Mumbai",
     "certifications": ["ISO9001"],
     "rating": Decimal("3.8"), "past_delivery_score": Decimal("72"),
     "contact_email": "rfp@speedmech-mock.com",  "status": "active"},

    {"supplier_id": "SUP005", "name": "NexaComponents",
     "category": "sensors",         "region": "Hyderabad",
     "certifications": [],
     "rating": Decimal("3.5"), "past_delivery_score": Decimal("65"),
     "contact_email": "rfp@nexa-mock.com",       "status": "active"},

    {"supplier_id": "SUP006", "name": "TitanForge Industries",
     "category": "structural_parts","region": "Coimbatore",
     "certifications": ["ISO9001", "IATF16949"],
     "rating": Decimal("4.6"), "past_delivery_score": Decimal("91"),
     "contact_email": "rfp@titanforge-mock.com", "status": "active"},

    {"supplier_id": "SUP007", "name": "ElectroAuto Systems",
     "category": "sensors",         "region": "Chennai",
     "certifications": ["ISO9001"],
     "rating": Decimal("4.1"), "past_delivery_score": Decimal("84"),
     "contact_email": "rfp@electroauto-mock.com","status": "active"},

    {"supplier_id": "SUP008", "name": "OldParts Pvt Ltd",
     "category": "brake_systems",   "region": "Delhi",
     "certifications": ["ISO9001"],
     "rating": Decimal("2.9"), "past_delivery_score": Decimal("55"),
     "contact_email": "rfp@oldparts-mock.com",   "status": "active"},
]

for supplier in SUPPLIERS:
    table.put_item(Item=supplier)
    print(f"✅ Seeded: {supplier['supplier_id']} — {supplier['name']}")

print("\n✅ All 8 suppliers seeded successfully.")
