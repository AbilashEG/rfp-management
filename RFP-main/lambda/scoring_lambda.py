"""
Strands Agents - Tool 5: Scoring Lambda
Step 6: Score proposals with weighted criteria and risk flagging
Optimized with structured output for agent evaluation
"""

import json
import logging
import boto3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
scores_table = dynamodb.Table('rfp-scores')

# Scoring weights (fixed policy)
SCORING_WEIGHTS = {
    "price": 0.30,
    "quality": 0.30,
    "delivery": 0.20,
    "compliance": 0.20
}


def handler(event, context):
    """
    Scoring Lambda Handler
    
    Input: {"body": {"rfp_id": "RFP-...", "proposals": [...]}}
    Output: Ranked proposals with scores and risk assessment
    """
    try:
        logger.info(f"[Tool 5] 🎯 Scoring - Starting")
        
        # Parse input
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        
        rfp_id = body.get("rfp_id", "")
        proposals = body.get("proposals", [])
        
        if not rfp_id or not proposals:
            logger.error(f"[Tool 5] ❌ Missing rfp_id or proposals")
            return _response(400, {"error": "rfp_id and proposals required", "success": False})
        
        logger.info(f"[Tool 5] Scoring {len(proposals)} proposals")
        
        # Normalize prices for scoring
        max_price = max((p.get("price", 2000) for p in proposals), default=2000) or 2000
        logger.info(f"[Tool 5] Max price for normalization: ${max_price}")
        
        scored_proposals: List[Dict[str, Any]] = []
        
        for proposal in proposals:
            try:
                # Calculate normalized component scores (0-100)
                price_score = _calculate_price_score(proposal.get("price", 2000), max_price)
                quality_score = float(proposal.get("quality_score", 80))
                delivery_score = _calculate_delivery_score(proposal.get("delivery_time_days", 30))
                compliance_score = 90.0 if proposal.get("certifications") else 60.0
                
                # Calculate total weighted score
                total_score = (
                    price_score * SCORING_WEIGHTS["price"] +
                    quality_score * SCORING_WEIGHTS["quality"] +
                    delivery_score * SCORING_WEIGHTS["delivery"] +
                    compliance_score * SCORING_WEIGHTS["compliance"]
                )
                
                # Identify risk flags
                risk_flags = _identify_risks(proposal)
                
                # Create structured proposal as dict
                scored = {
                    "proposal_id": proposal.get("proposal_id", ""),
                    "supplier_id": proposal.get("supplier_id", ""),
                    "price": float(proposal.get("price", 0)),
                    "quality": round(quality_score, 1),
                    "delivery_days": int(proposal.get("delivery_time_days", 0)),
                    "compliance": "Yes" if proposal.get("certifications") else "No",
                    "score_breakdown": {
                        "price_score": round(price_score, 1),
                        "quality_score": round(quality_score, 1),
                        "delivery_score": round(delivery_score, 1),
                        "compliance_score": round(compliance_score, 1)
                    },
                    "total_score": round(total_score, 1),
                    "risk_flags": risk_flags
                }
                
                scored_proposals.append(scored)
                
                # Persist to DynamoDB
                _save_score_to_dynamodb(rfp_id, scored)
                
            except Exception as e:
                logger.warning(f"[Tool 5] ⚠️ Failed to score proposal: {str(e)}")
                continue
        
        # Sort by score descending, return minimum fields only
        scored_proposals = sorted(scored_proposals, key=lambda x: x["total_score"], reverse=True)

        result = {
            "status": "success",
            "count": len(scored_proposals),
            "scored": [
                {
                    "supplier_id": s["supplier_id"],
                    "total_score": s["total_score"],
                    "flags":       s["risk_flags"]
                }
                for s in scored_proposals
            ]
        }

        logger.info(f"[Tool 5] ✅ Scored {result['count']} proposals")
        return _response(200, result)
        
    except Exception as e:
        logger.error(f"[Tool 5] ❌ Error: {str(e)}", exc_info=True)
        return _response(500, {"error": str(e), "success": False})


def _calculate_price_score(price: float, max_price: float) -> float:
    """Calculate normalized price score (lower price = higher score)"""
    if max_price <= 0:
        return 50.0
    return (1 - (price / max_price)) * 100


def _calculate_delivery_score(delivery_days: int) -> float:
    """Calculate normalized delivery score (fewer days = higher score)"""
    # Assume 60 days is the baseline for 0 points
    return max(0, (1 - (delivery_days / 60)) * 100)


def _identify_risks(proposal: Dict[str, Any]) -> List[str]:
    """Identify risk flags in proposal"""
    risks = []
    if proposal.get("price", 0) > 3000:
        risks.append("High Price")
    if proposal.get("delivery_time_days", 0) > 45:
        risks.append("Long Delivery")
    if not proposal.get("certifications"):
        risks.append("Compliance Gap")
    if proposal.get("quality_score", 0) < 80:
        risks.append("Quality Concern")
    return risks


def _save_score_to_dynamodb(rfp_id: str, scored: Dict[str, Any]) -> None:
    """Persist score to DynamoDB"""
    try:
        scores_table.put_item(
            Item={
                "score_id": f"{rfp_id}-{scored['supplier_id']}",
                "rfp_id": rfp_id,
                "proposal_id": scored["proposal_id"],
                "supplier_id": scored["supplier_id"],
                "total_score": scored["total_score"],
                "risk_flags": json.dumps(scored["risk_flags"]),
                "scored_at": datetime.now().isoformat()
            }
        )
        logger.info(f"[Tool 5] 💾 Saved score for {scored['supplier_id']}: {scored['total_score']}")
    except Exception as e:
        logger.warning(f"[Tool 5] ⚠️ Failed to save score: {str(e)}")


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format Lambda response"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }
