from strands import tool
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime
import uuid
import random
import json
from decimal import Decimal
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROPOSALS_TABLE, REGION

dynamodb = boto3.resource("dynamodb", region_name=REGION)

# Predefined mock data for consistent demo scenarios
MOCK_PRICES  = {"SUP001": 850, "SUP002": 720, "SUP003": 940,
                "SUP004": 650, "SUP005": 590, "SUP006": 880,
                "SUP007": 810, "SUP008": 480}
MOCK_LEADS   = {"SUP001": 14,  "SUP002": 21,  "SUP003": 10,
                "SUP004": 28,  "SUP005": 35,  "SUP006": 18,
                "SUP007": 22,  "SUP008": 45}
MOCK_QUALITY = {"SUP001": 92,  "SUP002": 85,  "SUP003": 97,
                "SUP004": 70,  "SUP005": 62,  "SUP006": 90,
                "SUP007": 83,  "SUP008": 50}
NON_COMPLIANT = {"SUP005", "SUP008"}


def _sanitize(obj):
    """Recursively convert Decimal and other non-JSON types to native Python types."""
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return int(obj) if obj == int(obj) else float(obj)
    return obj


@tool
def proposal_fetch_tool(rfp_id: str, supplier_ids: list) -> dict:
    """
    Fetches submitted proposals for the given RFP from DynamoDB.
    If no proposals exist (demo mode), auto-generates realistic mock proposals
    for the provided supplier IDs so scoring can proceed immediately.

    Args:
        rfp_id:       The RFP ID to fetch proposals for
        supplier_ids: Expected supplier IDs (used for mock generation)

    Returns:
        dict with proposals list and count
    """
    if not supplier_ids:
        return {"status": "success", "rfp_id": rfp_id,
                "proposal_count": 0, "proposals": []}

    try:
        table    = dynamodb.Table(PROPOSALS_TABLE)
        response = table.scan(FilterExpression=Attr("rfp_id").eq(rfp_id))
        proposals = response.get("Items", [])
    except Exception as e:
        return {"status": "error",
                "message": f"DynamoDB operation failed: {e}"}

    if not proposals:
        # Demo mode — generate and persist mock proposals
        for sid in supplier_ids:
            proposal_id = f"PROP-{str(uuid.uuid4())[:8].upper()}"
            item = {
                "proposal_id":     proposal_id,
                "rfp_id":          rfp_id,
                "supplier_id":     sid,
                "price":           MOCK_PRICES.get(sid, random.randint(500, 1000)),
                "lead_time_days":  MOCK_LEADS.get(sid, random.randint(10, 45)),
                "quality_score":   MOCK_QUALITY.get(sid, random.randint(50, 98)),
                "compliance_docs": [] if sid in NON_COMPLIANT else ["ISO9001"],
                "submitted_at":    datetime.utcnow().isoformat(),
                "status":          "received",
            }
            try:
                table.put_item(Item=item)
            except Exception as e:
                return {"status": "error",
                        "message": f"DynamoDB operation failed: {e}"}
            proposals.append(item)

    return {
        "status":         "success",
        "rfp_id":         rfp_id,
        "proposal_count": len(proposals),
        "proposals":      _sanitize(proposals),
    }
