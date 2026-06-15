from strands import tool
import boto3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SES_SENDER_EMAIL, SES_MOCK_MODE, REGION, SUPPLIERS_TABLE

ses      = boto3.client("ses",      region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)


@tool
def email_dispatch_tool(rfp_id: str, supplier_ids: list, rfp_content: str) -> dict:
    """
    Dispatches RFP email to each supplier in the list independently.
    In mock mode, logs the email without actually sending.
    In live mode, sends via Amazon SES.

    Args:
        rfp_id:       The RFP reference ID
        supplier_ids: List of supplier IDs to email
        rfp_content:  The full RFP document text to include in email

    Returns:
        dict with dispatch results per supplier
    """
    table   = dynamodb.Table(SUPPLIERS_TABLE)
    results = []

    for supplier_id in supplier_ids:
        # Lookup supplier contact info
        try:
            resp     = table.get_item(Key={"supplier_id": supplier_id})
            supplier = resp.get("Item", {})
            email    = supplier.get("contact_email", "unknown@mock.com")
            name     = supplier.get("name", supplier_id)
        except Exception as e:
            results.append({
                "supplier_id": supplier_id,
                "email":       "unknown@mock.com",
                "status":      "failed",
                "error":       f"DynamoDB lookup failed: {e}",
            })
            continue

        if SES_MOCK_MODE:
            print(f"[MOCK EMAIL] rfp_id={rfp_id} supplier_id={supplier_id} recipient={email}")
            results.append({
                "supplier_id":   supplier_id,
                "supplier_name": name,
                "email":         email,
                "status":        "mock_sent",
                "message":       f"[MOCK] RFP {rfp_id} would be sent to {email}",
            })
        else:
            try:
                ses.send_email(
                    Source=SES_SENDER_EMAIL,
                    Destination={"ToAddresses": [email]},
                    Message={
                        "Subject": {"Data": f"RFP Invitation: {rfp_id}"},
                        "Body":    {"Text": {"Data": rfp_content}},
                    },
                )
                results.append({
                    "supplier_id":   supplier_id,
                    "supplier_name": name,
                    "email":         email,
                    "status":        "sent",
                })
            except Exception as e:
                results.append({
                    "supplier_id": supplier_id,
                    "email":       email,
                    "status":      "failed",
                    "error":       str(e),
                })

    dispatched = len([r for r in results if r["status"] in ("sent", "mock_sent")])

    return {
        "status":     "success",
        "rfp_id":     rfp_id,
        "dispatched": dispatched,
        "results":    results,
    }
