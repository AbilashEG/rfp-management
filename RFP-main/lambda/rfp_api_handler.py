"""
RFP API Handler Lambda
Backend bridge between Next.js frontend and AgentCore Runtime.

Routes:
  POST   /rfp              → Submit new RFP → invoke AgentCore
  GET    /rfp/{id}         → Get RFP status from DynamoDB
  POST   /rfp/{id}/approve → Approve or reject RFP
  GET    /rfp/{id}/docs    → Get S3 presigned download URLs
"""

import json
import boto3
import base64
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ============================================================================
# CONFIG
# ============================================================================

REGION              = os.environ.get("REGION", "us-east-1")
AGENT_RUNTIME_ARN   = os.environ.get(
    "AGENT_RUNTIME_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:689050397154:runtime/rfpsupplieragent-ODy0E42s5l"
)
REQUESTS_TABLE      = os.environ.get("REQUESTS_TABLE", "rfp-requests")
RFP_DOCS_BUCKET     = os.environ.get("RFP_DOCS_BUCKET", "rfp-documents-quadrasystems")

# AWS clients
dynamodb    = boto3.resource("dynamodb", region_name=REGION)
s3          = boto3.client("s3", region_name=REGION)
agentcore   = boto3.client("bedrock-agentcore", region_name=REGION)

# ============================================================================
# LAMBDA ENTRY POINT
# ============================================================================

def handler(event: dict, context: Any) -> dict:
    """Main Lambda handler — routes HTTP method + path to correct function."""
    logger.info(f"Event: {json.dumps(event, default=str)[:500]}")

    method  = event.get("requestContext", {}).get("http", {}).get("method", "").upper()
    path    = event.get("rawPath", "/")

    try:
        # POST /rfp
        if method == "POST" and path == "/rfp":
            return handle_submit_rfp(event)

        # GET /rfp/{id}
        if method == "GET" and re.match(r"^/rfp/[^/]+$", path):
            rfp_id = path.split("/")[2]
            return handle_get_rfp(rfp_id)

        # POST /rfp/{id}/approve
        if method == "POST" and re.match(r"^/rfp/[^/]+/approve$", path):
            rfp_id = path.split("/")[2]
            return handle_approve_rfp(rfp_id, event)

        # GET /rfp/{id}/docs
        if method == "GET" and re.match(r"^/rfp/[^/]+/docs$", path):
            rfp_id = path.split("/")[2]
            return handle_get_docs(rfp_id)

        # OPTIONS preflight (CORS)
        if method == "OPTIONS":
            return cors_response(200, {})

        return cors_response(404, {"error": "Route not found"})

    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return cors_response(500, {"error": str(e)})


# ============================================================================
# ROUTE: POST /rfp — Submit RFP + invoke AgentCore
# ============================================================================

def handle_submit_rfp(event: dict) -> dict:
    """
    Receives message from frontend.
    Invokes AgentCore Runtime synchronously.
    Returns rfp_id + full agent response.
    """
    try:
        body = parse_body(event)
        message = body.get("message", "").strip()

        if not message:
            return cors_response(400, {"error": "message field is required"})

        logger.info(f"[submit_rfp] Invoking AgentCore: {message[:100]}")

        # Invoke AgentCore Runtime
        result = invoke_agentcore(message)

        rfp_id   = result.get("rfp_id", "")
        response = result.get("response", "")
        status   = result.get("status", "error")

        logger.info(f"[submit_rfp] ✅ RFP: {rfp_id}")

        return cors_response(200, {
            "rfp_id":   rfp_id,
            "status":   status,
            "response": response
        })

    except Exception as e:
        logger.error(f"[submit_rfp] Error: {e}", exc_info=True)
        return cors_response(500, {"error": str(e)})


# ============================================================================
# ROUTE: GET /rfp/{id} — Get RFP status
# ============================================================================

def handle_get_rfp(rfp_id: str) -> dict:
    """
    Reads rfp-requests DynamoDB table.
    Returns current status and metadata.
    """
    try:
        logger.info(f"[get_rfp] Reading: {rfp_id}")

        table = dynamodb.Table(REQUESTS_TABLE)
        result = table.get_item(Key={"RequestID": rfp_id})
        item = result.get("Item")

        if not item:
            return cors_response(404, {"error": f"RFP {rfp_id} not found"})

        return cors_response(200, {
            "rfp_id":              item.get("RequestID", rfp_id),
            "status":              item.get("Status", "unknown"),
            "requirement":         item.get("Requirement", ""),
            "awarded_supplier":    item.get("awarded_supplier", None),
            "awarded_at":          item.get("awarded_at", None),
            "docx_presigned_url":  item.get("DocxPresignedUrl", ""),
            "google_form_url":     item.get("GoogleFormUrl", ""),
            "created_at":          item.get("CreatedAt", ""),
            "supplier_count":      item.get("SupplierCount", 0),
        })

    except Exception as e:
        logger.error(f"[get_rfp] Error: {e}", exc_info=True)
        return cors_response(500, {"error": str(e)})


# ============================================================================
# ROUTE: POST /rfp/{id}/approve — Approve or reject RFP
# ============================================================================

def handle_approve_rfp(rfp_id: str, event: dict) -> dict:
    """
    Updates rfp-requests status to 'awarded' or 'rejected'.
    Called when user clicks Approve or Reject in the UI.
    """
    try:
        body   = parse_body(event)
        action = body.get("action", "approve").lower()
        now    = datetime.now(timezone.utc).isoformat()

        logger.info(f"[approve_rfp] {rfp_id} → {action}")

        table = dynamodb.Table(REQUESTS_TABLE)

        if action == "approve":
            table.update_item(
                Key={"RequestID": rfp_id},
                UpdateExpression="SET #s = :s, approved_at = :at, approved_by = :by",
                ExpressionAttributeNames={"#s": "Status"},
                ExpressionAttributeValues={
                    ":s":  "awarded",
                    ":at": now,
                    ":by": body.get("user", "procurement_manager")
                }
            )
            return cors_response(200, {
                "rfp_id": rfp_id,
                "status": "awarded",
                "message": "Contract approved and awarded successfully",
                "approved_at": now
            })

        elif action == "reject":
            table.update_item(
                Key={"RequestID": rfp_id},
                UpdateExpression="SET #s = :s, rejected_at = :at, reject_reason = :r",
                ExpressionAttributeNames={"#s": "Status"},
                ExpressionAttributeValues={
                    ":s":  "rejected",
                    ":at": now,
                    ":r":  body.get("reason", "Rejected by procurement manager")
                }
            )
            return cors_response(200, {
                "rfp_id": rfp_id,
                "status": "rejected",
                "message": "RFP rejected",
                "rejected_at": now
            })

        else:
            return cors_response(400, {"error": "action must be approve or reject"})

    except Exception as e:
        logger.error(f"[approve_rfp] Error: {e}", exc_info=True)
        return cors_response(500, {"error": str(e)})


# ============================================================================
# ROUTE: GET /rfp/{id}/docs — Get S3 presigned URLs
# ============================================================================

def handle_get_docs(rfp_id: str) -> dict:
    """
    Generates fresh presigned S3 URLs for .docx files.
    URLs are valid for 7 days.
    """
    try:
        logger.info(f"[get_docs] Generating presigned URLs for: {rfp_id}")

        rfp_key  = f"rfp-documents/{rfp_id}.docx"
        rec_key  = f"recommendations/{rfp_id}-recommendation.docx"

        urls = {}

        # RFP document
        try:
            s3.head_object(Bucket=RFP_DOCS_BUCKET, Key=rfp_key)
            urls["rfp_docx_url"] = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": RFP_DOCS_BUCKET, "Key": rfp_key},
                ExpiresIn=604800
            )
        except Exception:
            urls["rfp_docx_url"] = None

        # Recommendation report
        try:
            s3.head_object(Bucket=RFP_DOCS_BUCKET, Key=rec_key)
            urls["report_docx_url"] = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": RFP_DOCS_BUCKET, "Key": rec_key},
                ExpiresIn=604800
            )
        except Exception:
            urls["report_docx_url"] = None

        return cors_response(200, {
            "rfp_id": rfp_id,
            **urls
        })

    except Exception as e:
        logger.error(f"[get_docs] Error: {e}", exc_info=True)
        return cors_response(500, {"error": str(e)})


# ============================================================================
# AGENTCORE INVOCATION
# ============================================================================

def invoke_agentcore(message: str) -> dict:
    """
    Invokes AgentCore Runtime with the user message.
    Decodes and parses the streaming response.
    """
    try:
        payload = json.dumps({"message": message})
        payload_b64 = base64.b64encode(payload.encode()).decode()

        logger.info(f"[agentcore] Invoking runtime: {AGENT_RUNTIME_ARN}")

        response = agentcore.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            payload=payload_b64
        )

        # Read response body
        response_body = response.get("response", b"")
        if hasattr(response_body, "read"):
            response_body = response_body.read()

        if isinstance(response_body, bytes):
            response_body = response_body.decode("utf-8")

        logger.info(f"[agentcore] Raw response: {response_body[:300]}")

        # Parse JSON response
        result = json.loads(response_body)
        logger.info(f"[agentcore] ✅ Status: {result.get('status')} | RFP: {result.get('rfp_id')}")
        return result

    except Exception as e:
        logger.error(f"[agentcore] Invocation error: {e}", exc_info=True)
        raise


# ============================================================================
# HELPERS
# ============================================================================

def parse_body(event: dict) -> dict:
    """Parse request body from API Gateway event."""
    body = event.get("body", "{}")
    if not body:
        return {}
    if isinstance(body, str):
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        return json.loads(body)
    return body


def cors_response(status_code: int, body: dict) -> dict:
    """Return response with CORS headers for Amplify frontend."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key",
        },
        "body": json.dumps(body, default=str)
    }
