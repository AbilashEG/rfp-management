"""
Strands Agents - Tool 2: RFP Generator Lambda
Step 3: Generate RFP document and store in S3 + DynamoDB
Optimized with structured output
"""

import json
import logging
import boto3
import os
from datetime import datetime
import uuid
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
s3_client = boto3.client('s3', region_name=os.environ.get('REGION', 'us-east-1'))

requests_table = dynamodb.Table('rfp-requests')
S3_BUCKET = 'rfp-documents-quadrasystems'


def handler(event, context):
    """
    RFP Generator Lambda Handler
    
    Input: {"body": {"rfp_id": "RFP-...", "requirement": "...", "supplier_ids": [...]}}
    Output: Generated RFP document with S3 location
    """
    try:
        logger.info(f"[Tool 2] 📄 RFP Generator - Starting")
        
        # Parse input
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        
        requirement = body.get("requirement", "").strip()
        supplier_ids = body.get("supplier_ids", [])
        rfp_id = body.get("rfp_id", f"RFP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}")
        
        if not requirement or not supplier_ids:
            logger.error(f"[Tool 2] ❌ Missing requirement or supplier_ids")
            return _response(400, {"error": "requirement and supplier_ids required", "success": False})
        
        logger.info(f"[Tool 2] Generating RFP: {rfp_id} for {len(supplier_ids)} suppliers")
        
        timestamp = datetime.now().isoformat()
        
        # Create structured RFP document
        rfp_content = _generate_rfp_document(rfp_id, requirement, supplier_ids, timestamp)
        
        # Save to S3
        s3_key = f"rfp-documents/{rfp_id}.txt"
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=rfp_content.encode('utf-8'),
                ContentType='text/plain'
            )
            logger.info(f"[Tool 2] 💾 Saved to S3: s3://{S3_BUCKET}/{s3_key}")
        except Exception as e:
            logger.warning(f"[Tool 2] ⚠️ S3 save failed: {str(e)}")
        
        # Save metadata to DynamoDB
        try:
            requests_table.put_item(
                Item={
                    'RequestID': rfp_id,
                    'CreatedAt': timestamp,
                    'Requirement': requirement,
                    'SupplierCount': len(supplier_ids),
                    'Status': 'Active',
                    'S3Location': s3_key
                }
            )
            logger.info(f"[Tool 2] 💾 Saved to DynamoDB")
        except Exception as e:
            logger.warning(f"[Tool 2] ⚠️ DynamoDB save failed: {str(e)}")
        
        result = {
            "success": True,
            "rfp_id": rfp_id,
            "s3_location": f"s3://{S3_BUCKET}/{s3_key}",
            "supplier_count": len(supplier_ids),
            "timestamp": timestamp
        }
        
        logger.info(f"[Tool 2] ✅ RFP generated: {rfp_id}")
        
        return _response(200, result)
        
    except Exception as e:
        logger.error(f"[Tool 2] ❌ Error: {str(e)}", exc_info=True)
        return _response(500, {"error": str(e), "success": False})


def _generate_rfp_document(rfp_id: str, requirement: str, supplier_ids: List[str], timestamp: str) -> str:
    """Generate structured RFP document"""
    content = f"""RFP DOCUMENT
============
RFP ID: {rfp_id}
Created: {timestamp}
Status: Active
Deadline: 2026-09-30

REQUIREMENT:
{requirement}

TARGET SUPPLIERS:
"""
    for supplier_id in supplier_ids:
        content += f"\n- {supplier_id}"
    
    content += "\n\nSTATUS: Pending Responses\n"
    
    return content


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format Lambda response"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }
