"""
Strands Agents - Tool 1: Supplier Lookup Lambda
Step 2: Query DynamoDB suppliers by category → returns top 5 by rating
Optimized with structured output and comprehensive logging
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
suppliers_table = dynamodb.Table('rfp-suppliers')


def handler(event, context):
    """
    Supplier Lookup Lambda Handler
    
    Input: {"body": {"rfp_id": "RFP-...", "category": "sensors"}}
    Output: Structured supplier list with top 5 by rating
    """
    try:
        logger.info(f"[Tool 1] 🔍 Supplier Lookup - Starting")
        
        # Parse input
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        
        category = body.get("category", "").strip()
        rfp_id = body.get("rfp_id", "")
        
        if not category:
            logger.error(f"[Tool 1] ❌ Missing category")
            return _response(400, {"error": "category required", "success": False})
        
        logger.info(f"[Tool 1] Querying suppliers - Category: {category}, RFP: {rfp_id}")
        
        # Query DynamoDB with category filter
        response = suppliers_table.scan(
            FilterExpression="contains(#cat, :cat)",
            ExpressionAttributeNames={"#cat": "category"},
            ExpressionAttributeValues={":cat": category}
        )
        
        items = response.get("Items", [])
        logger.info(f"[Tool 1] Found {len(items)} total suppliers in category")
        
        # Convert to structured dicts and sort by rating
        suppliers: List[Dict[str, Any]] = []
        for item in items:
            try:
                supplier = {
                    "supplier_id": item.get("supplier_id", ""),
                    "name": item.get("name", ""),
                    "rating": float(item.get("rating", 0)) if item.get("rating") else 0.0,
                    "contact_email": item.get("contact_email", ""),
                    "category": item.get("category", "")
                }
                suppliers.append(supplier)
            except Exception as e:
                logger.warning(f"[Tool 1] ⚠️ Skipping malformed supplier: {str(e)}")
                continue
        
        # Sort by rating (highest first) and take top 5
        suppliers = sorted(suppliers, key=lambda x: x["rating"], reverse=True)[:5]
        
        result = {
            "success": True,
            "supplier_count": len(suppliers),
            "suppliers": suppliers,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[Tool 1] ✅ Found {result['supplier_count']} top suppliers")
        
        return _response(200, result)
        
    except Exception as e:
        logger.error(f"[Tool 1] ❌ Error: {str(e)}", exc_info=True)
        return _response(500, {"error": str(e), "success": False})


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format Lambda response"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }
