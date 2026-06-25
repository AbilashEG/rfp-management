"""
Strands Agents - Tool 2: RFP Generator Lambda
Step 3: Generate .docx RFP document → S3 → DynamoDB
Returns presigned URL for the .docx file
"""

import json
import logging
import boto3
import os
import io
import uuid
from datetime import datetime
from typing import Dict, Any, List

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get("REGION", "us-east-1")
RFP_DOCS_BUCKET = os.environ.get("RFP_DOCS_BUCKET", "rfp-documents-quadrasystems")
RFP_DOCS_PREFIX = "rfp-documents/"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
requests_table = dynamodb.Table("rfp-requests")


def handler(event, context):
    """
    RFP Generator Lambda Handler

    Input: {"body": {"rfp_id": "RFP-...", "requirement": "...", "supplier_ids": [...]}}
    Output: Generated .docx RFP with S3 presigned URL
    """
    try:
        logger.info("[Tool 2] 📄 RFP Generator - Starting")

        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)

        requirement = body.get("requirement", "").strip()
        supplier_ids = body.get("supplier_ids", [])
        rfp_id = body.get("rfp_id", f"RFP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}")
        component_name = body.get("component_name", requirement[:60] if requirement else "Component")
        specs = body.get("specs", "As per requirement")
        quantity = body.get("quantity", "As specified")
        deadline = body.get("deadline", "2026-09-30")
        google_form_url = body.get("google_form_url", "")

        if not requirement or not supplier_ids:
            return _response(400, {"error": "requirement and supplier_ids required", "success": False})

        logger.info(f"[Tool 2] Generating RFP: {rfp_id} for {len(supplier_ids)} suppliers")

        timestamp = datetime.now().isoformat()

        # Generate .docx
        buffer = _generate_rfp_docx(
            rfp_id=rfp_id,
            component_name=component_name,
            specs=specs,
            quantity=str(quantity),
            deadline=deadline,
            supplier_ids=supplier_ids,
            requirement=requirement,
            google_form_url=google_form_url
        )

        # Save .docx to S3
        s3_key = f"{RFP_DOCS_PREFIX}{rfp_id}.docx"
        presigned_url = ""
        try:
            s3.put_object(
                Bucket=RFP_DOCS_BUCKET,
                Key=s3_key,
                Body=buffer.getvalue(),
                ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            logger.info(f"[Tool 2] 💾 Saved .docx to S3: s3://{RFP_DOCS_BUCKET}/{s3_key}")

            presigned_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": RFP_DOCS_BUCKET, "Key": s3_key},
                ExpiresIn=604800  # 7 days
            )
            logger.info(f"[Tool 2] 🔗 Presigned URL generated (7 days)")
        except Exception as e:
            logger.warning(f"[Tool 2] ⚠️ S3 save failed: {e}")

        # Save metadata to DynamoDB
        try:
            requests_table.put_item(
                Item={
                    "RequestID": rfp_id,
                    "CreatedAt": timestamp,
                    "Requirement": requirement,
                    "SupplierCount": len(supplier_ids),
                    "Status": "Active",
                    "S3Location": s3_key,
                    "DocxPresignedUrl": presigned_url,
                    "GoogleFormUrl": google_form_url
                }
            )
            logger.info("[Tool 2] 💾 Saved metadata to DynamoDB rfp-requests")
        except Exception as e:
            logger.warning(f"[Tool 2] ⚠️ DynamoDB save failed: {e}")

        result = {
            "status": "success",
            "rfp_id": rfp_id,
            "docx_url": presigned_url
        }

        logger.info(f"[Tool 2] ✅ RFP .docx generated: {rfp_id}")
        return _response(200, result)

    except Exception as e:
        logger.error(f"[Tool 2] ❌ Error: {e}", exc_info=True)
        return _response(500, {"error": str(e), "success": False})


def _generate_rfp_docx(
    rfp_id: str,
    component_name: str,
    specs: str,
    quantity: str,
    deadline: str,
    supplier_ids: List[str],
    requirement: str,
    google_form_url: str
) -> io.BytesIO:
    """Generate a formatted .docx RFP document."""
    doc = Document()

    # Title
    title = doc.add_heading("REQUEST FOR PROPOSAL", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # RFP ID heading
    doc.add_heading(f"RFP ID: {rfp_id}", level=1)

    # Details table
    table = doc.add_table(rows=5, cols=2)
    table.style = "Table Grid"
    cells = [
        ("Component", component_name),
        ("Specifications", specs),
        ("Quantity", quantity),
        ("Deadline", deadline),
        ("Suppliers Invited", str(len(supplier_ids)))
    ]
    for i, (key, val) in enumerate(cells):
        table.rows[i].cells[0].text = key
        table.rows[i].cells[1].text = val

    doc.add_paragraph()

    # Full requirement
    doc.add_heading("Requirement Description", level=2)
    doc.add_paragraph(requirement)

    doc.add_paragraph()

    # Evaluation criteria
    doc.add_heading("Evaluation Criteria", level=2)
    criteria = doc.add_table(rows=4, cols=2)
    criteria.style = "Table Grid"
    weights = [
        ("Price",         "30%"),
        ("Quality Score", "30%"),
        ("Delivery Time", "20%"),
        ("Compliance",    "20%")
    ]
    for i, (c, w) in enumerate(weights):
        criteria.rows[i].cells[0].text = c
        criteria.rows[i].cells[1].text = w

    doc.add_paragraph()

    # Submission instructions
    doc.add_heading("Submission Instructions", level=2)
    submission_text = (
        "Please submit your proposal via the Google Form link provided in the email. "
        "Include: unit price, lead time, quality certifications, and delivery commitment."
    )
    if google_form_url:
        submission_text += f"\n\nGoogle Form URL: {google_form_url}"
    doc.add_paragraph(submission_text)

    doc.add_paragraph()

    # Invited suppliers
    doc.add_heading("Invited Suppliers", level=2)
    for supplier_id in supplier_ids:
        doc.add_paragraph(f"• {supplier_id}")

    # Save to buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }
