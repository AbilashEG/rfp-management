"""
Unit tests for all 6 RFP agent tools.
Uses moto to mock AWS services — no real AWS calls made.
Usage: pytest tests/test_tools.py -v
"""
import pytest
import boto3
from decimal import Decimal
from unittest.mock import patch, MagicMock
from moto import mock_dynamodb, mock_s3, mock_ses
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REGION = "us-east-1"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def aws_credentials():
    """Mocked AWS credentials for moto."""
    import os
    os.environ["AWS_ACCESS_KEY_ID"]     = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"]    = "testing"
    os.environ["AWS_SESSION_TOKEN"]     = "testing"
    os.environ["AWS_DEFAULT_REGION"]    = REGION


@pytest.fixture
def dynamo_tables():
    """Create all 4 DynamoDB tables in moto."""
    with mock_dynamodb():
        client = boto3.client("dynamodb", region_name=REGION)

        client.create_table(
            TableName="rfp-suppliers",
            KeySchema=[{"AttributeName": "supplier_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "supplier_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        client.create_table(
            TableName="rfp-requests",
            KeySchema=[
                {"AttributeName": "rfp_id",     "KeyType": "HASH"},
                {"AttributeName": "created_at", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "rfp_id",     "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        client.create_table(
            TableName="rfp-proposals",
            KeySchema=[
                {"AttributeName": "proposal_id", "KeyType": "HASH"},
                {"AttributeName": "rfp_id",      "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "proposal_id", "AttributeType": "S"},
                {"AttributeName": "rfp_id",      "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[{
                "IndexName": "rfp_id-index",
                "KeySchema": [{"AttributeName": "rfp_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }],
            BillingMode="PAY_PER_REQUEST",
        )
        client.create_table(
            TableName="rfp-scores",
            KeySchema=[
                {"AttributeName": "score_id",    "KeyType": "HASH"},
                {"AttributeName": "proposal_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "score_id",    "AttributeType": "S"},
                {"AttributeName": "proposal_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Seed supplier data
        resource = boto3.resource("dynamodb", region_name=REGION)
        table    = resource.Table("rfp-suppliers")
        table.put_item(Item={
            "supplier_id": "SUP003", "name": "AutoSensor Global",
            "category": "sensors",  "region": "Bangalore",
            "certifications": ["ISO9001", "IATF16949", "ISO14001"],
            "rating": Decimal("4.9"), "past_delivery_score": Decimal("98"),
            "contact_email": "rfp@autosensor-mock.com", "status": "active",
        })
        table.put_item(Item={
            "supplier_id": "SUP005", "name": "NexaComponents",
            "category": "sensors",  "region": "Hyderabad",
            "certifications": [], "rating": Decimal("3.5"),
            "past_delivery_score": Decimal("65"),
            "contact_email": "rfp@nexa-mock.com", "status": "active",
        })

        yield resource


# ---------------------------------------------------------------------------
# Tool 1: supplier_lookup_tool
# ---------------------------------------------------------------------------

def test_supplier_lookup_returns_active_suppliers(dynamo_tables):
    from tools.supplier_lookup_tool import supplier_lookup_tool
    result = supplier_lookup_tool(category="sensors")
    assert result["status"] == "success"
    assert result["count"]  >= 1
    for s in result["suppliers"]:
        assert s["category"] == "sensors"
        assert s["status"]   == "active"


def test_supplier_lookup_empty_category_returns_error(dynamo_tables):
    from tools.supplier_lookup_tool import supplier_lookup_tool
    result = supplier_lookup_tool(category="")
    assert result["status"] == "error"


# ---------------------------------------------------------------------------
# Tool 2: rfp_generator_tool
# ---------------------------------------------------------------------------

@mock_s3
def test_rfp_generator_creates_record(dynamo_tables):
    # Create S3 bucket first
    s3 = boto3.client("s3", region_name=REGION)
    s3.create_bucket(Bucket="rfp-documents-quadrasystems")

    from tools.rfp_generator_tool import rfp_generator_tool
    result = rfp_generator_tool(
        component_name="Brake Sensor",
        specs="IP67, ABS, AMP Superseal",
        quantity=500,
        deadline="2026-09-30",
        supplier_ids=["SUP003", "SUP005"],
    )
    assert result["status"]         == "success"
    assert result["rfp_id"].startswith("RFP-")
    assert result["supplier_count"] == 2
    assert "rfp_content"            in result


def test_rfp_generator_missing_param_returns_error(dynamo_tables):
    from tools.rfp_generator_tool import rfp_generator_tool
    result = rfp_generator_tool(
        component_name="",
        specs="some spec",
        quantity=100,
        deadline="2026-09-30",
        supplier_ids=["SUP003"],
    )
    assert result["status"] == "error"
    assert "missing required parameter" in result["message"]


# ---------------------------------------------------------------------------
# Tool 3: email_dispatch_tool
# ---------------------------------------------------------------------------

def test_email_dispatch_mock_mode(dynamo_tables):
    from tools.email_dispatch_tool import email_dispatch_tool
    result = email_dispatch_tool(
        rfp_id="RFP-TEST-001",
        supplier_ids=["SUP003", "SUP005"],
        rfp_content="Test RFP content",
    )
    assert result["status"]     == "success"
    assert result["dispatched"] == 2
    for r in result["results"]:
        assert r["status"] == "mock_sent"


# ---------------------------------------------------------------------------
# Tool 4: proposal_fetch_tool
# ---------------------------------------------------------------------------

def test_proposal_fetch_generates_mocks(dynamo_tables):
    from tools.proposal_fetch_tool import proposal_fetch_tool
    result = proposal_fetch_tool(
        rfp_id="RFP-FAKE-001",
        supplier_ids=["SUP003", "SUP005"],
    )
    assert result["status"]         == "success"
    assert result["proposal_count"] == 2
    ids = [p["supplier_id"] for p in result["proposals"]]
    assert "SUP003" in ids
    assert "SUP005" in ids


def test_proposal_fetch_empty_supplier_ids(dynamo_tables):
    from tools.proposal_fetch_tool import proposal_fetch_tool
    result = proposal_fetch_tool(rfp_id="RFP-NONE", supplier_ids=[])
    assert result["status"]         == "success"
    assert result["proposal_count"] == 0


# ---------------------------------------------------------------------------
# Tool 5: scoring_tool
# ---------------------------------------------------------------------------

def test_scoring_tool_scores_proposals(dynamo_tables):
    from tools.scoring_tool import scoring_tool
    proposals = [
        {"proposal_id": "PROP-A", "rfp_id": "RFP-001", "supplier_id": "SUP003",
         "price": 940, "lead_time_days": 10, "quality_score": 97,
         "compliance_docs": ["ISO9001", "IATF16949"]},
        {"proposal_id": "PROP-B", "rfp_id": "RFP-001", "supplier_id": "SUP005",
         "price": 590, "lead_time_days": 35, "quality_score": 62,
         "compliance_docs": []},
    ]
    result = scoring_tool(rfp_id="RFP-001", proposals=proposals)
    assert result["status"]       == "success"
    assert result["scored_count"] == 2
    # Sorted descending by total_score
    scores = [p["total_score"] for p in result["scored_proposals"]]
    assert scores == sorted(scores, reverse=True)


def test_scoring_tool_empty_proposals_returns_error(dynamo_tables):
    from tools.scoring_tool import scoring_tool
    result = scoring_tool(rfp_id="RFP-001", proposals=[])
    assert result["status"] == "error"


def test_scoring_tool_no_division_by_zero_same_price(dynamo_tables):
    from tools.scoring_tool import scoring_tool
    proposals = [
        {"proposal_id": "PROP-X", "rfp_id": "RFP-002", "supplier_id": "SUP003",
         "price": 800, "lead_time_days": 10, "quality_score": 90,
         "compliance_docs": ["ISO9001"]},
        {"proposal_id": "PROP-Y", "rfp_id": "RFP-002", "supplier_id": "SUP005",
         "price": 800, "lead_time_days": 20, "quality_score": 70,
         "compliance_docs": []},
    ]
    result = scoring_tool(rfp_id="RFP-002", proposals=proposals)
    assert result["status"] == "success"  # no exception raised


# ---------------------------------------------------------------------------
# Tool 6: recommendation_tool
# ---------------------------------------------------------------------------

def test_recommendation_tool_returns_top2(dynamo_tables):
    from tools.recommendation_tool import recommendation_tool
    scored = [
        {"proposal_id": "PROP-A", "supplier_id": "SUP003",
         "total_score": 88.5, "price_score": 60.0,
         "quality_score": 97.0, "delivery_score": 95.0,
         "compliance_score": 100.0, "flags": [], "recommendation": "shortlist"},
        {"proposal_id": "PROP-B", "supplier_id": "SUP005",
         "total_score": 45.0, "price_score": 80.0,
         "quality_score": 62.0, "delivery_score": 20.0,
         "compliance_score": 0.0,
         "flags": ["NO_CERTIFICATIONS — High compliance risk"],
         "recommendation": "review"},
        {"proposal_id": "PROP-C", "supplier_id": "SUP007",
         "total_score": 72.0, "price_score": 70.0,
         "quality_score": 83.0, "delivery_score": 60.0,
         "compliance_score": 50.0, "flags": [], "recommendation": "shortlist"},
    ]
    result = recommendation_tool(rfp_id="RFP-001", scored_proposals=scored)
    assert result["status"] == "success"
    assert len(result["top_2_recommendations"]) == 2
    assert result["top_2_recommendations"][0]["rank"] == 1


def test_recommendation_tool_empty_input_returns_error(dynamo_tables):
    from tools.recommendation_tool import recommendation_tool
    result = recommendation_tool(rfp_id="RFP-001", scored_proposals=[])
    assert result["status"] == "error"


def test_recommendation_approval_required_when_flags(dynamo_tables):
    from tools.recommendation_tool import recommendation_tool
    scored = [
        {"proposal_id": "PROP-A", "supplier_id": "SUP005",
         "total_score": 88.0, "price_score": 80.0,
         "quality_score": 62.0, "delivery_score": 20.0,
         "compliance_score": 0.0,
         "flags": ["NO_CERTIFICATIONS — High compliance risk"],
         "recommendation": "review"},
        {"proposal_id": "PROP-B", "supplier_id": "SUP003",
         "total_score": 85.0, "price_score": 60.0,
         "quality_score": 97.0, "delivery_score": 95.0,
         "compliance_score": 100.0, "flags": [], "recommendation": "shortlist"},
    ]
    result = recommendation_tool(rfp_id="RFP-001", scored_proposals=scored)
    assert result["approval_required"] is True
