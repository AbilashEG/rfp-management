"""
Strands Agents - Tool 6: Recommendation Lambda
Step 7: Return top 2 suppliers with reasoning and risk assessment
Optimized with structured output for agent consumption
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Recommendation Lambda Handler
    
    Input: {"body": {"rfp_id": "RFP-...", "scored_proposals": [...]}}
    Output: Top 2 recommendations with structured reasoning
    """
    try:
        logger.info(f"[Tool 6] 🏆 Recommendation - Starting")
        
        # Parse input
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        
        rfp_id = body.get("rfp_id", "")
        scored_proposals = body.get("scored_proposals", [])
        
        if not rfp_id or not scored_proposals:
            logger.error(f"[Tool 6] ❌ Missing rfp_id or scored_proposals")
            return _response(400, {"error": "rfp_id and scored_proposals required", "success": False})
        
        logger.info(f"[Tool 6] Evaluating {len(scored_proposals)} proposals for recommendations")
        
        # Generate recommendations from top 2 proposals
        if len(scored_proposals) < 2:
            logger.warning(f"[Tool 6] ⚠️ Insufficient proposals: {len(scored_proposals)}")
            return _response(200, {
                "success": True,
                "recommendation_count": 0,
                "recommendations": [],
                "timestamp": datetime.now().isoformat()
            })
        
        top_2 = scored_proposals[:2]
        recommendations: List[Dict[str, Any]] = []
        
        for rank, proposal in enumerate(top_2, 1):
            # Build structured recommendation as dict
            rec = {
                "rank": rank,
                "supplier_id": proposal["supplier_id"],
                "total_score": proposal["total_score"],
                "price": proposal["price"],
                "delivery_days": proposal["delivery_days"],
                "quality": proposal["quality"],
                "compliance": proposal["compliance"],
                "risk_flags": proposal.get("risk_flags", []),
                "reasoning": _generate_reasoning(proposal, rank),
                "recommendation": _get_recommendation_text(rank, proposal.get("risk_flags", []))
            }
            recommendations.append(rec)
        
        result = {
            "success": True,
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[Tool 6] ✅ Generated {len(recommendations)} recommendations")
        
        return _response(200, result)
        
    except Exception as e:
        logger.error(f"[Tool 6] ❌ Error: {str(e)}", exc_info=True)
        return _response(500, {"error": str(e), "success": False})


def _generate_reasoning(proposal: Dict[str, Any], rank: int) -> str:
    """Generate structured reasoning for recommendation"""
    score = proposal["total_score"]
    risk_count = len(proposal.get("risk_flags", []))
    
    if risk_count > 0:
        risk_note = f" ({risk_count} risk flag(s) detected)"
    else:
        risk_note = " (no risk flags)"
    
    return (
        f"Rank {rank} supplier scores {score:.1f}/100 based on weighted criteria "
        f"(Price 30%, Quality 30%, Delivery 20%, Compliance 20%){risk_note}"
    )


def _get_recommendation_text(rank: int, risk_flags: List[str]) -> str:
    """Generate recommendation action text"""
    if rank == 1:
        if risk_flags:
            return f"RECOMMENDED with risk review - {len(risk_flags)} flag(s)"
        else:
            return "RECOMMENDED - Optimal choice"
    else:
        if risk_flags:
            return f"BACKUP option - Review {len(risk_flags)} risk(s) before proceeding"
        else:
            return "BACKUP option - Good alternative"


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format Lambda response"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }
