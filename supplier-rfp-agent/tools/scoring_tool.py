from strands import tool
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime
from decimal import Decimal
import uuid
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (SCORES_TABLE, REGION,
                    PRICE_WEIGHT, QUALITY_WEIGHT,
                    DELIVERY_WEIGHT, COMPLIANCE_WEIGHT)

dynamodb = boto3.resource("dynamodb", region_name=REGION)


def _sanitize(obj):
    """Recursively convert Decimal to native Python types for JSON serialization."""
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return int(obj) if obj == int(obj) else float(obj)
    return obj


@tool
def scoring_tool(rfp_id: str) -> dict:
    """
    Scores each proposal using weighted multi-criteria scoring:
    Price 30%, Quality 30%, Delivery 20%, Compliance 20%.
    Flags risks: no certifications, long lead time, price anomaly, low quality.
    Saves score records to rfp-scores DynamoDB table.

    Args:
        rfp_id: The RFP ID being evaluated

    Returns:
        dict with scored_proposals sorted by total_score descending
    """
    # Fetch proposals from DynamoDB for this RFP
    table_proposals = dynamodb.Table(PROPOSALS_TABLE)
    response = table_proposals.scan(
        FilterExpression=Attr("rfp_id").eq(rfp_id)
    )
    proposals = response.get("Items", [])

    if not proposals:
        return {"status": "error", "message": "No proposals to score"}

    prices = [float(p.get("price", 999999))        for p in proposals]
    leads  = [float(p.get("lead_time_days", 99))   for p in proposals]
    min_p, max_p = min(prices), max(prices)
    min_l, max_l = min(leads),  max(leads)

    table  = dynamodb.Table(SCORES_TABLE)
    scored = []

    for p in proposals:
        price     = float(p.get("price", 999999))
        lead      = float(p.get("lead_time_days", 99))
        # Clamp quality_score to 0-100
        quality   = max(0.0, min(100.0, float(p.get("quality_score", 0))))
        comp_docs = p.get("compliance_docs", [])

        price_score      = ((max_p - price) / (max_p - min_p + 1)) * 100
        delivery_score   = ((max_l - lead)  / (max_l - min_l + 1)) * 100
        quality_score    = quality
        compliance_score = (100 if len(comp_docs) >= 2
                            else 50 if len(comp_docs) == 1
                            else 0)

        total = (price_score      * PRICE_WEIGHT +
                 quality_score    * QUALITY_WEIGHT +
                 delivery_score   * DELIVERY_WEIGHT +
                 compliance_score * COMPLIANCE_WEIGHT)

        flags = []
        if len(comp_docs) == 0:
            flags.append("NO_CERTIFICATIONS — High compliance risk")
        if lead > 30:
            flags.append(f"LONG_LEAD_TIME — {lead} days exceeds 30-day threshold")
        if price < (min_p * 0.6):
            flags.append("PRICE_ANOMALY — Price unusually low, verify quality")
        if quality < 70:
            flags.append(f"LOW_QUALITY_SCORE — {quality}/100 below acceptable threshold")

        score_id   = f"SCORE-{str(uuid.uuid4())[:8].upper()}"
        score_item = {
            "score_id":        score_id,
            "proposal_id":     p["proposal_id"],
            "rfp_id":          rfp_id,
            "supplier_id":     p["supplier_id"],
            "price_score":     round(price_score,      2),
            "quality_score":   round(quality_score,    2),
            "delivery_score":  round(delivery_score,   2),
            "compliance_score":round(compliance_score, 2),
            "total_score":     round(total,            2),
            "flags":           flags,
            "recommendation":  ("shortlist" if total >= 70 and not flags
                                else "review"),
            "scored_at":       datetime.utcnow().isoformat(),
        }

        try:
            table.put_item(Item={
                "score_id":         score_id,
                "proposal_id":      p["proposal_id"],
                "rfp_id":           rfp_id,
                "supplier_id":      p["supplier_id"],
                "price_score":      Decimal(str(round(price_score,      2))),
                "quality_score":    Decimal(str(round(quality_score,    2))),
                "delivery_score":   Decimal(str(round(delivery_score,   2))),
                "compliance_score": Decimal(str(round(compliance_score, 2))),
                "total_score":      Decimal(str(round(total,            2))),
                "flags":            flags,
                "recommendation":   ("shortlist" if total >= 70 and not flags
                                     else "review"),
                "scored_at":        datetime.utcnow().isoformat(),
            })
        except Exception as e:
            raise RuntimeError(
                f"DynamoDB put_item failed for score_id={score_id}: {e}")

        scored.append({**score_item,
                       "supplier_name": p.get("supplier_id")})

    scored.sort(key=lambda x: (x["total_score"], -ord(x["proposal_id"][0])),
                reverse=True)

    return {
        "status":           "success",
        "rfp_id":           rfp_id,
        "scored_count":     len(scored),
        "scored_proposals": _sanitize(scored),
        "top_supplier_id":  scored[0]["supplier_id"] if scored else None,
    }
