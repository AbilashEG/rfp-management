"""
Strands Agents - Google Form Webhook Lambda
Receives Google Apps Script POST when supplier submits form
Writes proposal to DynamoDB rfp-proposals table

Google Apps Script sends POST to this Lambda's API Gateway URL:
  {
    "rfp_id": "RFP-20260619-XXXX",
    "supplier_id": "SUP001",
    "supplier_name": "Acme Sensors Ltd",
    "price": 2500.00,
    "lead_time_days": 28,
    "quality_score": 92.0,
    "compliance_docs": "ISO 9001, IATF 16949"
  }
"""

import json
import boto3
import uuid
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get("REGION", "us-east-1")
PROPOSALS_TABLE = os.environ.get("PROPOSALS_TABLE", "rfp-proposals")

dynamodb = boto3.resource("dynamodb", region_name=REGION)


def handler(event, context):
    """
    Google Form Webhook Lambda Handler

    Triggered by: API Gateway (HTTP API) POST request from Google Apps Script
    Writes incoming proposal to DynamoDB rfp-proposals table
    """
    try:
        logger.info("[GoogleForm] 📥 Incoming form submission")

        # Parse body — API Gateway may pass as string or dict
        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)

        # Extract fields from Google Form response
        rfp_id         = body.get("rfp_id", "").strip()
        supplier_id    = body.get("supplier_id", "").strip()
        supplier_name  = body.get("supplier_name", "").strip()
        price          = float(body.get("price", 0))
        lead_time_days = int(body.get("lead_time_days", 0))
        quality_score  = float(body.get("quality_score", 0))
        compliance_raw = body.get("compliance_docs", "")

        # Validate required fields
        if not rfp_id or not supplier_id:
            logger.error("[GoogleForm] ❌ Missing rfp_id or supplier_id")
            return _response(400, {
                "status": "error",
                "error": "rfp_id and supplier_id are required"
            })

        # Parse compliance docs — can be comma-separated string or list
        if isinstance(compliance_raw, list):
            compliance_docs: List[str] = compliance_raw
        elif isinstance(compliance_raw, str) and compliance_raw:
            compliance_docs = [c.strip() for c in compliance_raw.split(",") if c.strip()]
        else:
            compliance_docs = []

        # Generate unique proposal ID
        proposal_id = f"PROP-{str(uuid.uuid4())[:8].upper()}"

        # Write to DynamoDB rfp-proposals table
        table = dynamodb.Table(PROPOSALS_TABLE)
        item = {
            "proposal_id":     proposal_id,
            "rfp_id":          rfp_id,
            "supplier_id":     supplier_id,
            "supplier_name":   supplier_name,
            "price":           str(price),
            "lead_time_days":  lead_time_days,
            "quality_score":   str(quality_score),
            "compliance_docs": compliance_docs,
            "submitted_at":    datetime.utcnow().isoformat(),
            "status":          "received",
            "source":          "google_form"
        }

        table.put_item(Item=item)

        logger.info(
            f"[GoogleForm] ✅ Proposal stored: {proposal_id} "
            f"| RFP: {rfp_id} | Supplier: {supplier_name} ({supplier_id})"
        )

        return _response(200, {
            "status": "success",
            "proposal_id": proposal_id,
            "message": f"Proposal from {supplier_name} stored successfully"
        })

    except json.JSONDecodeError as e:
        logger.error(f"[GoogleForm] ❌ Invalid JSON body: {e}")
        return _response(400, {"status": "error", "error": "Invalid JSON body"})

    except Exception as e:
        logger.error(f"[GoogleForm] ❌ Unexpected error: {e}", exc_info=True)
        return _response(500, {"status": "error", "error": str(e)})


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format Lambda response with CORS headers for Google Apps Script."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body, default=str)
    }
