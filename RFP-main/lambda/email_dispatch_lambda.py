"""
Strands Agents - Tool 3: Email Dispatch Lambda
Step 4: Send RFP to suppliers via SES with Google Form URL + RFP .docx link
SES mock mode = True always
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# SES mock mode — always True, never send real emails
SES_MOCK_MODE = True


def handler(event, context):
    """
    Email Dispatch Lambda Handler

    Input: {
        "body": {
            "rfp_id": "RFP-...",
            "supplier_emails": [...],
            "supplier_names": [...],        (optional, parallel list to emails)
            "component_name": "...",        (optional)
            "quantity": "500",              (optional)
            "deadline": "2026-09-30",       (optional)
            "google_form_url": "https://...",
            "docx_presigned_url": "https://..."
        }
    }
    Output: Email dispatch confirmation with structured results
    """
    try:
        logger.info("[Tool 3] 📧 Email Dispatch - Starting")

        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)

        rfp_id            = body.get("rfp_id", "")
        supplier_emails   = body.get("supplier_emails", [])
        supplier_names    = body.get("supplier_names", [])
        component_name    = body.get("component_name", "Component")
        quantity          = body.get("quantity", "As specified")
        deadline          = body.get("deadline", "2026-09-30")
        google_form_url   = body.get("google_form_url", "")
        docx_presigned_url = body.get("docx_presigned_url", "")

        if not rfp_id or not supplier_emails:
            logger.error("[Tool 3] ❌ Missing rfp_id or supplier_emails")
            return _response(400, {
                "error": "rfp_id and supplier_emails required",
                "success": False
            })

        logger.info(
            f"[Tool 3] Dispatching RFP {rfp_id} to {len(supplier_emails)} suppliers "
            f"[MOCK={SES_MOCK_MODE}]"
        )

        dispatch_results: List[Dict[str, Any]] = []

        for idx, email in enumerate(supplier_emails):
            # Get supplier name if parallel list provided
            supplier_name = supplier_names[idx] if idx < len(supplier_names) else email.split("@")[0]

            # Build full email body
            email_body = _build_email_body(
                supplier_name=supplier_name,
                rfp_id=rfp_id,
                component_name=component_name,
                quantity=str(quantity),
                deadline=deadline,
                google_form_url=google_form_url,
                docx_presigned_url=docx_presigned_url
            )

            if SES_MOCK_MODE:
                # Log email content but do not send
                logger.info(f"[Tool 3] [MOCK] Email to: {email}\n{email_body}")
                status = "MockSent"
            else:
                # Real SES send (not used — mock mode always on)
                status = "Sent"

            dispatch_results.append({
                "email":      email,
                "supplier":   supplier_name,
                "status":     status,
                "timestamp":  datetime.now().isoformat(),
                "mock_mode":  SES_MOCK_MODE
            })

        output = {
            "success": True,
            "sent": len(dispatch_results)
        }

        logger.info(f"[Tool 3] ✅ Dispatched to {len(dispatch_results)} recipients [MOCK={SES_MOCK_MODE}]")
        return _response(200, output)

    except Exception as e:
        logger.error(f"[Tool 3] ❌ Error: {e}", exc_info=True)
        return _response(500, {"error": str(e), "success": False})


def _build_email_body(
    supplier_name: str,
    rfp_id: str,
    component_name: str,
    quantity: str,
    deadline: str,
    google_form_url: str,
    docx_presigned_url: str
) -> str:
    """Build full email body with Google Form URL and RFP .docx link."""

    form_section = (
        f"SUBMIT YOUR PROPOSAL HERE:\n{google_form_url}"
        if google_form_url
        else "SUBMIT YOUR PROPOSAL: Google Form link will be provided separately."
    )

    docx_section = (
        f"VIEW RFP DOCUMENT (.docx):\n{docx_presigned_url}"
        if docx_presigned_url
        else "RFP document will be shared separately."
    )

    return f"""
Dear {supplier_name},

You are invited to submit a proposal for the following procurement requirement.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RFP ID        : {rfp_id}
Component     : {component_name}
Quantity      : {quantity} units
Deadline      : {deadline}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{form_section}

{docx_section}

Please submit before {deadline}.

Proposals are evaluated on:
  • Price          (30%)
  • Quality        (30%)
  • Delivery Time  (20%)
  • Compliance     (20%)

Regards,
Procurement Team

[MOCK MODE — No real email sent]
"""


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }
