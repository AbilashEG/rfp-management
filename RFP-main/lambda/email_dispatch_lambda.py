"""
Strands Agents - Tool 3: Email Dispatch Lambda
Step 4: Send RFP to suppliers via SES (mock mode enabled)
Optimized with structured output
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Email Dispatch Lambda Handler
    
    Input: {"body": {"rfp_id": "RFP-...", "supplier_emails": [...]}}
    Output: Email dispatch confirmation with structured results
    """
    try:
        logger.info(f"[Tool 3] 📧 Email Dispatch - Starting")
        
        # Parse input
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        
        rfp_id = body.get("rfp_id", "")
        supplier_emails = body.get("supplier_emails", [])
        
        if not rfp_id or not supplier_emails:
            logger.error(f"[Tool 3] ❌ Missing rfp_id or supplier_emails")
            return _response(400, {"error": "rfp_id and supplier_emails required", "success": False})
        
        logger.info(f"[Tool 3] Dispatching RFP to {len(supplier_emails)} suppliers (mock mode)")
        
        # Mock email dispatch (SES mock mode enabled)
        dispatch_results: List[Dict[str, Any]] = []
        for email in supplier_emails:
            result = {
                "email": email,
                "status": "Sent",
                "timestamp": datetime.now().isoformat()
            }
            dispatch_results.append(result)
            logger.info(f"[Tool 3] ✉️ Sent to: {email}")
        
        output = {
            "success": True,
            "email_count": len(dispatch_results),
            "dispatch_results": dispatch_results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[Tool 3] ✅ Dispatched to {len(dispatch_results)} recipients")
        
        return _response(200, output)
        
    except Exception as e:
        logger.error(f"[Tool 3] ❌ Error: {str(e)}", exc_info=True)
        return _response(500, {"error": str(e), "success": False})


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format Lambda response"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }
