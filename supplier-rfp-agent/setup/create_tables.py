"""
Run once to create all 4 DynamoDB tables.
Usage: python setup/create_tables.py
"""
import boto3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REGION, SUPPLIERS_TABLE, REQUESTS_TABLE, PROPOSALS_TABLE, SCORES_TABLE

dynamodb = boto3.client("dynamodb", region_name=REGION)

TABLES = [
    {
        "TableName":            SUPPLIERS_TABLE,
        "KeySchema":            [{"AttributeName": "supplier_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "supplier_id", "AttributeType": "S"}],
        "BillingMode":          "PAY_PER_REQUEST",
    },
    {
        "TableName": REQUESTS_TABLE,
        "KeySchema": [
            {"AttributeName": "rfp_id",     "KeyType": "HASH"},
            {"AttributeName": "created_at", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "rfp_id",     "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": PROPOSALS_TABLE,
        "KeySchema": [
            {"AttributeName": "proposal_id", "KeyType": "HASH"},
            {"AttributeName": "rfp_id",      "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "proposal_id", "AttributeType": "S"},
            {"AttributeName": "rfp_id",      "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [{
            "IndexName": "rfp_id-index",
            "KeySchema": [{"AttributeName": "rfp_id", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"},
        }],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": SCORES_TABLE,
        "KeySchema": [
            {"AttributeName": "score_id",    "KeyType": "HASH"},
            {"AttributeName": "proposal_id", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "score_id",    "AttributeType": "S"},
            {"AttributeName": "proposal_id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
]

for t in TABLES:
    try:
        dynamodb.create_table(**t)
        print(f"✅ Created: {t['TableName']}")
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠️  Already exists: {t['TableName']}")
