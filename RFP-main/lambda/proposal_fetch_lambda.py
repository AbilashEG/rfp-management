"""
Strands Agents - Tool 4: Proposal Fetch Lambda
Step 5: Fetch proposals from DynamoDB, auto-generate mock if empty
Optimized with structured output
"""

import json
import logging
import boto3
import os
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
proposals_table = dynamodb.Table('rfp-proposals')


def handler(event, context):
    """
    Proposal Fetch Lambda Handler
    
    Input: {"body": {"rfp_id": "RFP-...", "supplier_ids": [...]}}
    Output: Fetched or auto-generated proposals with structured output
    """
    try:
        logger.info(f"[Tool 4] 📋 Proposal Fetch - Starting")
        
        # Parse input
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        
        rfp_id = body.get("rfp_id", "")
        supplier_ids = body.get("supplier_ids", [])
        
        if not rfp_id or not supplier_ids:
            logger.error(f"[Tool 4] ❌ Missing rfp_id or supplier_ids")
            return _response(400, {"error": "rfp_id and supplier_ids required", "success": False})
        
        logger.info(f"[Tool 4] Fetching proposals for {len(supplier_ids)} suppliers")
        
        proposals: List[Dict[str, Any]] = []
        
        for supplier_id in supplier_ids:
            proposal_id = f"{rfp_id}-{supplier_id}"
            
            # Try to fetch from DynamoDB
            proposal_data = None
            try:
                response = proposals_table.get_item(Key={"proposal_id": proposal_id})
                proposal_data = response.get("Item")
            except Exception as e:
                logger.warning(f"[Tool 4] ⚠️ DynamoDB fetch failed: {str(e)}")
            
            # Auto-generate mock if not found
            if not proposal_data:
                proposal_data = _generate_mock_proposal(rfp_id, supplier_id, proposal_id)
                try:
                    proposals_table.put_item(Item=proposal_data)
                    logger.info(f"[Tool 4] 🔄 Auto-generated mock: {proposal_id}")
                except Exception as e:
                    logger.warning(f"[Tool 4] ⚠️ Failed to save mock: {str(e)}")
            
            # Use as dict - no model conversion needed
            try:
                proposals.append(proposal_data)
            except Exception as e:
                logger.warning(f"[Tool 4] ⚠️ Failed to process proposal: {str(e)}")
                continue
        
        # Slim to minimum fields only
        slim_proposals = [
            {
                "proposal_id":       p.get("proposal_id", ""),
                "supplier_id":       p.get("supplier_id", ""),
                "price":             p.get("price", 0),
                "lead_time_days":    p.get("delivery_time_days", 30),
                "quality_score":     p.get("quality_score", 80),
                "compliance_docs":   p.get("certifications", [])
            }
            for p in proposals
        ]

        output = {
            "status": "success",
            "count": len(slim_proposals),
            "proposals": slim_proposals
        }

        logger.info(f"[Tool 4] ✅ Retrieved {len(slim_proposals)} proposals")
        return _response(200, output)
        
    except Exception as e:
        logger.error(f"[Tool 4] ❌ Error: {str(e)}", exc_info=True)
        return _response(500, {"error": str(e), "success": False})


def _generate_mock_proposal(rfp_id: str, supplier_id: str, proposal_id: str) -> Dict[str, Any]:
    """Generate mock proposal data"""
    # Deterministic mock generation based on supplier_id
    hash_val = hash(supplier_id)
    
    return {
        "proposal_id": proposal_id,
        "rfp_id": rfp_id,
        "supplier_id": supplier_id,
        "price": round(2000 + (hash_val % 3000), 2),
        "delivery_time_days": 25 + (hash_val % 15),
        "quality_score": 80 + (hash_val % 20),
        "certifications": ["ISO 9001", "IATF 16949"],
        "submitted_at": datetime.now().isoformat()
    }


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format Lambda response"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }
