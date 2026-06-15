from strands import tool
import boto3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SUPPLIERS_TABLE, REGION

dynamodb = boto3.resource("dynamodb", region_name=REGION)


@tool
def recommendation_tool(rfp_id: str, scored_proposals: list) -> dict:
    """
    Generates final ranked Top-2 supplier recommendation based on scores.
    Returns full reasoning, risk summary, and approval_required flag.
    This tool output triggers the AgentCore Policy human approval gate.

    Args:
        rfp_id:           The RFP ID
        scored_proposals: Scored proposal dicts from scoring_tool (sorted desc)

    Returns:
        dict with top_2_recommendations, all_flags, approval_required,
        approval_message, and total_evaluated
    """
    if not scored_proposals:
        return {"status": "error", "message": "No scored proposals provided"}

    sup_table = dynamodb.Table(SUPPLIERS_TABLE)
    # Take top 2 (already sorted by scoring_tool)
    top2                  = scored_proposals[:2]
    recommendation_lines  = []
    all_flags             = []
    approval_required     = False

    for rank, item in enumerate(top2, 1):
        # Enrich with supplier master data
        try:
            sup_resp = sup_table.get_item(Key={"supplier_id": item["supplier_id"]})
            supplier = sup_resp.get("Item", {})
        except Exception:
            supplier = {}

        flags = item.get("flags", [])
        all_flags.extend(flags)
        if flags:
            approval_required = True

        # Determine dominant strength
        dim_scores = {
            "quality":  item.get("quality_score",   0),
            "price":    item.get("price_score",      0),
            "delivery": item.get("delivery_score",   0),
        }
        dominant = max(dim_scores, key=dim_scores.get)

        risk_text = (f"RISKS: {'; '.join(flags)}" if flags
                     else "No major risks identified.")

        recommendation_lines.append({
            "rank":             rank,
            "supplier_id":      item["supplier_id"],
            "supplier_name":    supplier.get("name",               item["supplier_id"]),
            "region":           supplier.get("region",             "Unknown"),
            "total_score":      item["total_score"],
            "price_score":      item["price_score"],
            "quality_score":    item["quality_score"],
            "delivery_score":   item["delivery_score"],
            "compliance_score": item["compliance_score"],
            "certifications":   supplier.get("certifications",     []),
            "past_delivery":    supplier.get("past_delivery_score","N/A"),
            "flags":            flags,
            "recommendation":   item["recommendation"],
            "reasoning": (
                f"Ranked #{rank} with overall score "
                f"{item['total_score']:.1f}/100. "
                f"Dominant strength: {dominant}. {risk_text}"
            ),
        })

    approval_message = (
        "HUMAN APPROVAL REQUIRED — One or more flagged risks detected. "
        "Procurement manager must review before contract award."
        if approval_required else
        "No critical flags detected. Proceed to contract award "
        "pending manager confirmation."
    )

    return {
        "status":                "success",
        "rfp_id":                rfp_id,
        "top_2_recommendations": recommendation_lines,
        "all_flags":             all_flags,
        "approval_required":     approval_required,
        "approval_message":      approval_message,
        "total_evaluated":       len(scored_proposals),
    }
