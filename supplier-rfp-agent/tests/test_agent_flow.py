"""
End-to-end agent flow test — mocks all AWS services via moto.
Validates the full 6-tool lifecycle runs without errors.
Usage: pytest tests/test_agent_flow.py -v
"""
import pytest
import boto3
from decimal import Decimal
from unittest.mock import patch, MagicMock
from moto import mock_dynamodb, mock_s3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REGION = "us-east-1"


@pytest.fixture(autouse=True)
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"]     = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"]    = "testing"
    os.environ["AWS_SESSION_TOKEN"]     = "testing"
    os.environ["AWS_DEFAULT_REGION"]    = REGION


import os


@mock_dynamodb
@mock_s3
def test_full_lifecycle_sensors():
    """
    Tests the full lifecycle: lookup → generate → dispatch → fetch → score → recommend.
    Uses only sensors category suppliers (SUP003, SUP005, SUP007).
    """
    # Setup DynamoDB tables
    client = boto3.client("dynamodb", region_name=REGION)
    for table_cfg in [
        {"TableName": "rfp-suppliers",
         "KeySchema": [{"AttributeName": "supplier_id", "KeyType": "HASH"}],
         "AttributeDefinitions": [{"AttributeName": "supplier_id", "AttributeType": "S"}],
         "BillingMode": "PAY_PER_REQUEST"},
        {"TableName": "rfp-requests",
         "KeySchema": [{"AttributeName": "rfp_id", "KeyType": "HASH"},
                       {"AttributeName": "created_at", "KeyType": "RANGE"}],
         "AttributeDefinitions": [{"AttributeName": "rfp_id", "AttributeType": "S"},
                                   {"AttributeName": "created_at", "AttributeType": "S"}],
         "BillingMode": "PAY_PER_REQUEST"},
        {"TableName": "rfp-proposals",
         "KeySchema": [{"AttributeName": "proposal_id", "KeyType": "HASH"},
                       {"AttributeName": "rfp_id", "KeyType": "RANGE"}],
         "AttributeDefinitions": [{"AttributeName": "proposal_id", "AttributeType": "S"},
                                   {"AttributeName": "rfp_id", "AttributeType": "S"}],
         "GlobalSecondaryIndexes": [{"IndexName": "rfp_id-index",
                                     "KeySchema": [{"AttributeName": "rfp_id", "KeyType": "HASH"}],
                                     "Projection": {"ProjectionType": "ALL"}}],
         "BillingMode": "PAY_PER_REQUEST"},
        {"TableName": "rfp-scores",
         "KeySchema": [{"AttributeName": "score_id", "KeyType": "HASH"},
                       {"AttributeName": "proposal_id", "KeyType": "RANGE"}],
         "AttributeDefinitions": [{"AttributeName": "score_id", "AttributeType": "S"},
                                   {"AttributeName": "proposal_id", "AttributeType": "S"}],
         "BillingMode": "PAY_PER_REQUEST"},
    ]:
        client.create_table(**table_cfg)

    # Seed suppliers
    resource = boto3.resource("dynamodb", region_name=REGION)
    sup_table = resource.Table("rfp-suppliers")
    for item in [
        {"supplier_id": "SUP003", "name": "AutoSensor Global", "category": "sensors",
         "region": "Bangalore", "certifications": ["ISO9001", "IATF16949", "ISO14001"],
         "rating": Decimal("4.9"), "past_delivery_score": Decimal("98"),
         "contact_email": "rfp@autosensor-mock.com", "status": "active"},
        {"supplier_id": "SUP005", "name": "NexaComponents", "category": "sensors",
         "region": "Hyderabad", "certifications": [],
         "rating": Decimal("3.5"), "past_delivery_score": Decimal("65"),
         "contact_email": "rfp@nexa-mock.com", "status": "active"},
        {"supplier_id": "SUP007", "name": "ElectroAuto Systems", "category": "sensors",
         "region": "Chennai", "certifications": ["ISO9001"],
         "rating": Decimal("4.1"), "past_delivery_score": Decimal("84"),
         "contact_email": "rfp@electroauto-mock.com", "status": "active"},
    ]:
        sup_table.put_item(Item=item)

    # Setup S3
    s3 = boto3.client("s3", region_name=REGION)
    s3.create_bucket(Bucket="rfp-documents-quadrasystems")

    # --- Run the 6-step lifecycle ---
    from tools.supplier_lookup_tool  import supplier_lookup_tool
    from tools.rfp_generator_tool    import rfp_generator_tool
    from tools.email_dispatch_tool   import email_dispatch_tool
    from tools.proposal_fetch_tool   import proposal_fetch_tool
    from tools.scoring_tool          import scoring_tool
    from tools.recommendation_tool   import recommendation_tool

    # Step 1: Lookup
    lookup_result = supplier_lookup_tool(category="sensors")
    assert lookup_result["status"] == "success"
    assert lookup_result["count"]  == 3
    supplier_ids = [s["supplier_id"] for s in lookup_result["suppliers"]]

    # Step 2: Generate RFP
    gen_result = rfp_generator_tool(
        component_name="ABS Wheel Speed Sensor",
        specs="IP67, -40C to 125C, AMP Superseal",
        quantity=500,
        deadline="2026-09-30",
        supplier_ids=supplier_ids,
    )
    assert gen_result["status"]         == "success"
    rfp_id = gen_result["rfp_id"]
    assert rfp_id.startswith("RFP-")

    # Step 3: Dispatch emails (mock mode)
    email_result = email_dispatch_tool(
        rfp_id=rfp_id,
        supplier_ids=supplier_ids,
        rfp_content=gen_result["rfp_content"],
    )
    assert email_result["dispatched"] == 3

    # Step 4: Fetch proposals (auto-generates mock)
    fetch_result = proposal_fetch_tool(rfp_id=rfp_id, supplier_ids=supplier_ids)
    assert fetch_result["proposal_count"] == 3
    proposals = fetch_result["proposals"]

    # Step 5: Score proposals
    score_result = scoring_tool(rfp_id=rfp_id, proposals=proposals)
    assert score_result["status"]       == "success"
    assert score_result["scored_count"] == 3
    scored = score_result["scored_proposals"]

    # Step 6: Recommend top 2
    rec_result = recommendation_tool(rfp_id=rfp_id, scored_proposals=scored)
    assert rec_result["status"]                    == "success"
    assert len(rec_result["top_2_recommendations"]) == 2
    assert rec_result["top_2_recommendations"][0]["rank"] == 1
    assert "approval_required" in rec_result
    assert "approval_message"  in rec_result

    print(f"\n✅ Full lifecycle passed. RFP: {rfp_id}")
    print(f"   Top supplier: {rec_result['top_2_recommendations'][0]['supplier_id']}")
    print(f"   Approval required: {rec_result['approval_required']}")
