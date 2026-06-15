from strands import tool
import boto3
from datetime import datetime
import uuid
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUESTS_TABLE, RFP_DOCS_BUCKET, RFP_DOCS_PREFIX, REGION

dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3       = boto3.client("s3",         region_name=REGION)


@tool
def rfp_generator_tool(
    component_name: str,
    specs:          str,
    quantity:       int,
    deadline:       str,
    supplier_ids:   list,
) -> dict:
    """
    Generates a structured RFP document for the given component requirement.
    Saves it to S3 and creates an RFP record in DynamoDB.

    Args:
        component_name: Name of the component needed (e.g. brake sensors)
        specs:          Technical specifications string
        quantity:       Number of units required
        deadline:       Delivery deadline (YYYY-MM-DD)
        supplier_ids:   List of supplier IDs to send this RFP to

    Returns:
        dict with rfp_id, s3_path, rfp_content, and supplier_count
    """
    # Input validation
    for param, val in [("component_name", component_name), ("specs", specs),
                       ("deadline", deadline), ("supplier_ids", supplier_ids)]:
        if not val:
            return {"status": "error", "message": f"missing required parameter: {param}"}
    if not quantity:
        return {"status": "error", "message": "missing required parameter: quantity"}

    rfp_id     = f"RFP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    created_at = datetime.utcnow().isoformat()

    rfp_content = f"""
REQUEST FOR PROPOSAL — {rfp_id}
Generated: {created_at}
========================================

COMPONENT REQUIREMENT
Component Name : {component_name}
Specifications : {specs}
Quantity       : {quantity} units
Deadline       : {deadline}

SUBMISSION REQUIREMENTS
1. Unit price per component (INR)
2. Lead time in business days
3. Quality certifications held (ISO9001, IATF16949, etc.)
4. Past delivery performance metrics
5. Minimum order quantity
6. Warranty terms

EVALUATION CRITERIA
- Price          : 30%
- Quality Score  : 30%
- Delivery Time  : 20%
- Compliance     : 20%

Submit proposals via the supplier portal by {deadline}.
RFP Reference ID: {rfp_id}
    """.strip()

    # Upload to S3
    s3_key  = f"{RFP_DOCS_PREFIX}{rfp_id}.txt"
    s3_warning = None
    try:
        s3.put_object(
            Bucket=RFP_DOCS_BUCKET,
            Key=s3_key,
            Body=rfp_content.encode("utf-8"),
            ContentType="text/plain",
        )
        s3_path = f"s3://{RFP_DOCS_BUCKET}/{s3_key}"
    except Exception as e:
        s3_path    = f"mock-s3://{s3_key}"
        s3_warning = f"S3 upload failed: {e}"

    # Persist to DynamoDB
    try:
        table = dynamodb.Table(REQUESTS_TABLE)
        table.put_item(Item={
            "rfp_id":                rfp_id,
            "created_at":            created_at,
            "component_name":        component_name,
            "specs":                 specs,
            "quantity":              quantity,
            "deadline":              deadline,
            "status":                "draft",
            "created_by":            "rfp-agent",
            "shortlisted_suppliers": supplier_ids,
            "s3_path":               s3_path,
        })
    except Exception as e:
        raise RuntimeError(f"DynamoDB put_item failed for rfp_id={rfp_id}: {e}")

    result = {
        "status":         "success",
        "rfp_id":         rfp_id,
        "s3_path":        s3_path,
        "rfp_content":    rfp_content,
        "supplier_count": len(supplier_ids),
    }
    if s3_warning:
        result["s3_warning"] = s3_warning
    return result
