#!/bin/bash
# STEP 2: Build, Tag, Push, and Update Lambda
# Copy-paste this ENTIRE command block into CloudShell

cd /tmp/supplier-rfp-agent

# Update the handler file with the new version (all 6 tools)
cat > lambda/rfp_agent_handler.py << 'HANDLER_EOF'
"""
AWS Lambda entry point for the RFP Agent.
Triggered by API Gateway (HTTP) or EventBridge (scheduled).
Full agent with all 6 tools and DynamoDB integration.
"""
import json
import logging
import time
import sys
import os
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Ensure /var/task root is on path for Lambda container
sys.path.insert(0, "/var/task")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
s3_client = boto3.client('s3', region_name=os.environ.get('REGION', 'us-east-1'))

# Table names
SUPPLIERS_TABLE = dynamodb.Table('rfp-suppliers')
REQUESTS_TABLE = dynamodb.Table('rfp-requests')
PROPOSALS_TABLE = dynamodb.Table('rfp-proposals')
SCORES_TABLE = dynamodb.Table('rfp-scores')
S3_BUCKET = 'rfp-documents-quadrasystems'


# ============================================================================
# TOOL 1: SUPPLIER LOOKUP
# ============================================================================
def tool_supplier_lookup(rfp_requirement: str) -> dict:
    """Lookup suppliers based on RFP requirement."""
    try:
        logger.info(f"[Tool 1] Supplier Lookup - Searching for suppliers...")
        
        # Query all suppliers from DynamoDB
        response = SUPPLIERS_TABLE.scan()
        suppliers = response.get('Items', [])
        
        # Filter suppliers based on requirement keywords
        relevant_suppliers = []
        keywords = rfp_requirement.lower().split()
        
        for supplier in suppliers:
            supplier_name = supplier.get('SupplierName', '').lower()
            capabilities = supplier.get('Capabilities', '').lower()
            score = sum(1 for kw in keywords if kw in supplier_name or kw in capabilities)
            
            if score > 0 or len(relevant_suppliers) < 4:  # Always include at least 4
                relevant_suppliers.append({
                    'SupplierID': supplier.get('SupplierID'),
                    'SupplierName': supplier.get('SupplierName'),
                    'Email': supplier.get('Email'),
                    'Capabilities': supplier.get('Capabilities'),
                    'PastPerformance': supplier.get('PastPerformance', 'Good'),
                    'RelevanceScore': score
                })
        
        # Sort by relevance and take top suppliers
        relevant_suppliers = sorted(relevant_suppliers, key=lambda x: x['RelevanceScore'], reverse=True)[:4]
        
        logger.info(f"[Tool 1] Found {len(relevant_suppliers)} relevant suppliers")
        return {
            'status': 'success',
            'supplier_count': len(relevant_suppliers),
            'suppliers': relevant_suppliers
        }
    except Exception as e:
        logger.error(f"[Tool 1] Error in supplier lookup: {str(e)}")
        return {'status': 'error', 'message': str(e), 'suppliers': []}


# ============================================================================
# TOOL 2: RFP GENERATION
# ============================================================================
def tool_rfp_generation(rfp_requirement: str, suppliers: list) -> dict:
    """Generate RFP document and save to S3 and DynamoDB."""
    try:
        logger.info(f"[Tool 2] RFP Generation - Creating RFP document...")
        
        rfp_id = f"RFP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        timestamp = datetime.now().isoformat()
        
        # Create RFP document content
        rfp_content = f"""
RFP DOCUMENT
============
RFP ID: {rfp_id}
Created: {timestamp}
Status: Active

REQUIREMENT:
{rfp_requirement}

TARGET SUPPLIERS:
"""
        for supplier in suppliers:
            rfp_content += f"\n- {supplier['SupplierName']} ({supplier['Email']})"
        
        rfp_content += "\n\nDEADLINE: 2026-09-30\nSTATUS: Pending Responses"
        
        # Save to S3
        s3_key = f"rfp-documents/{rfp_id}.txt"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=rfp_content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        # Save to DynamoDB
        REQUESTS_TABLE.put_item(
            Item={
                'RequestID': rfp_id,
                'CreatedAt': timestamp,
                'Requirement': rfp_requirement,
                'SupplierCount': len(suppliers),
                'Status': 'Active',
                'S3Location': s3_key
            }
        )
        
        logger.info(f"[Tool 2] RFP created: {rfp_id}")
        return {
            'status': 'success',
            'rfp_id': rfp_id,
            's3_location': s3_key,
            'supplier_count': len(suppliers)
        }
    except Exception as e:
        logger.error(f"[Tool 2] Error in RFP generation: {str(e)}")
        return {'status': 'error', 'message': str(e)}


# ============================================================================
# TOOL 3: EMAIL DISPATCH
# ============================================================================
def tool_email_dispatch(rfp_id: str, suppliers: list) -> dict:
    """Send RFP emails to suppliers (mock mode)."""
    try:
        logger.info(f"[Tool 3] Email Dispatch - Sending RFP to {len(suppliers)} suppliers...")
        
        dispatch_results = []
        for supplier in suppliers:
            # In mock mode, just log the dispatch
            dispatch_results.append({
                'SupplierID': supplier['SupplierID'],
                'SupplierName': supplier['SupplierName'],
                'Email': supplier['Email'],
                'Status': 'Sent',
                'Timestamp': datetime.now().isoformat()
            })
            logger.info(f"[Tool 3] Email sent to {supplier['SupplierName']} ({supplier['Email']})")
        
        logger.info(f"[Tool 3] Dispatched RFP to {len(dispatch_results)} suppliers")
        return {
            'status': 'success',
            'rfp_id': rfp_id,
            'email_count': len(dispatch_results),
            'dispatch_results': dispatch_results
        }
    except Exception as e:
        logger.error(f"[Tool 3] Error in email dispatch: {str(e)}")
        return {'status': 'error', 'message': str(e)}


# ============================================================================
# TOOL 4: PROPOSAL FETCH
# ============================================================================
def tool_proposal_fetch(rfp_id: str, suppliers: list) -> dict:
    """Fetch proposals from suppliers (auto-generate mock if needed)."""
    try:
        logger.info(f"[Tool 4] Proposal Fetch - Retrieving proposals for {rfp_id}...")
        
        proposals = []
        for supplier in suppliers:
            # Check if proposal exists
            try:
                response = PROPOSALS_TABLE.get_item(
                    Key={
                        'ProposalID': f"{rfp_id}-{supplier['SupplierID']}"
                    }
                )
                proposal = response.get('Item')
            except:
                proposal = None
            
            # If not found, generate mock proposal
            if not proposal:
                proposal_id = f"{rfp_id}-{supplier['SupplierID']}"
                proposal = {
                    'ProposalID': proposal_id,
                    'RFP_ID': rfp_id,
                    'SupplierID': supplier['SupplierID'],
                    'SupplierName': supplier['SupplierName'],
                    'Price': round(1000 + (hash(supplier['SupplierID']) % 5000), 2),
                    'DeliveryTime': 30 + (hash(supplier['SupplierID']) % 30),
                    'Quality': round(75 + (hash(supplier['SupplierID']) % 25) / 1.0, 1),
                    'ComplianceCertifications': ['ISO 9001', 'RoHS', 'REACH'],
                    'SubmittedAt': datetime.now().isoformat()
                }
                
                # Save mock proposal to DynamoDB
                PROPOSALS_TABLE.put_item(Item=proposal)
            
            proposals.append(proposal)
        
        logger.info(f"[Tool 4] Retrieved {len(proposals)} proposals")
        return {
            'status': 'success',
            'rfp_id': rfp_id,
            'proposal_count': len(proposals),
            'proposals': proposals
        }
    except Exception as e:
        logger.error(f"[Tool 4] Error in proposal fetch: {str(e)}")
        return {'status': 'error', 'message': str(e), 'proposals': []}


# ============================================================================
# TOOL 5: SCORING
# ============================================================================
def tool_scoring(rfp_id: str, proposals: list) -> dict:
    """Score proposals using multi-criteria evaluation."""
    try:
        logger.info(f"[Tool 5] Scoring - Evaluating {len(proposals)} proposals...")
        
        # Scoring weights
        weights = {
            'price': 0.30,
            'quality': 0.30,
            'delivery': 0.20,
            'compliance': 0.20
        }
        
        # Normalize proposal data
        if proposals:
            max_price = max(p.get('Price', 1000) for p in proposals) or 1000
            min_delivery = min(p.get('DeliveryTime', 30) for p in proposals) or 30
        else:
            max_price = 1000
            min_delivery = 30
        
        scored_proposals = []
        for proposal in proposals:
            # Calculate individual scores (0-100)
            price_score = (1 - (proposal.get('Price', 1000) / max_price)) * 100 if max_price > 0 else 50
            quality_score = proposal.get('Quality', 80)
            delivery_score = (1 - (proposal.get('DeliveryTime', 30) / 60)) * 100  # Normalized to 60 days max
            compliance_score = 90 if proposal.get('ComplianceCertifications') else 60
            
            # Calculate weighted total score
            total_score = (
                price_score * weights['price'] +
                quality_score * weights['quality'] +
                delivery_score * weights['delivery'] +
                compliance_score * weights['compliance']
            )
            
            scored_data = {
                'ProposalID': proposal.get('ProposalID'),
                'SupplierName': proposal.get('SupplierName'),
                'Price': proposal.get('Price'),
                'Quality': proposal.get('Quality'),
                'DeliveryTime': proposal.get('DeliveryTime'),
                'Compliance': 'Yes' if proposal.get('ComplianceCertifications') else 'No',
                'ScoreBreakdown': {
                    'Price': round(price_score, 1),
                    'Quality': round(quality_score, 1),
                    'Delivery': round(delivery_score, 1),
                    'Compliance': round(compliance_score, 1)
                },
                'TotalScore': round(total_score, 1)
            }
            
            # Save score to DynamoDB
            SCORES_TABLE.put_item(
                Item={
                    'ScoreID': f"{rfp_id}-{proposal.get('SupplierID', 'unknown')}",
                    'RFP_ID': rfp_id,
                    'ProposalID': proposal.get('ProposalID'),
                    'TotalScore': scored_data['TotalScore'],
                    'ScoreBreakdown': json.dumps(scored_data['ScoreBreakdown']),
                    'ScoredAt': datetime.now().isoformat()
                }
            )
            
            scored_proposals.append(scored_data)
        
        # Sort by total score descending
        scored_proposals = sorted(scored_proposals, key=lambda x: x['TotalScore'], reverse=True)
        
        logger.info(f"[Tool 5] Scored {len(scored_proposals)} proposals")
        return {
            'status': 'success',
            'rfp_id': rfp_id,
            'scored_count': len(scored_proposals),
            'scored_proposals': scored_proposals
        }
    except Exception as e:
        logger.error(f"[Tool 5] Error in scoring: {str(e)}")
        return {'status': 'error', 'message': str(e), 'scored_proposals': []}


# ============================================================================
# TOOL 6: RECOMMENDATION
# ============================================================================
def tool_recommendation(rfp_id: str, scored_proposals: list) -> dict:
    """Generate Top-2 recommendations with risk analysis."""
    try:
        logger.info(f"[Tool 6] Recommendation - Generating top recommendations...")
        
        if not scored_proposals or len(scored_proposals) < 2:
            logger.warning("[Tool 6] Insufficient proposals for recommendation")
            return {
                'status': 'success',
                'rfp_id': rfp_id,
                'recommendation_count': 0,
                'recommendations': [],
                'approval_status': 'PENDING_REVIEW'
            }
        
        # Get top 2
        top_2 = scored_proposals[:2]
        
        recommendations = []
        for rank, proposal in enumerate(top_2, 1):
            risk_flags = []
            
            # Risk detection
            if proposal['Price'] > 3000:
                risk_flags.append('High Price')
            if proposal['DeliveryTime'] > 45:
                risk_flags.append('Long Delivery')
            if proposal['Compliance'] == 'No':
                risk_flags.append('Compliance Gap')
            if proposal['Quality'] < 80:
                risk_flags.append('Quality Concern')
            
            rec = {
                'Rank': rank,
                'SupplierName': proposal['SupplierName'],
                'ProposalID': proposal['ProposalID'],
                'TotalScore': proposal['TotalScore'],
                'Price': proposal['Price'],
                'DeliveryTime': proposal['DeliveryTime'],
                'Quality': proposal['Quality'],
                'Compliance': proposal['Compliance'],
                'Reasoning': f"Rank {rank} based on weighted scoring (Price 30%, Quality 30%, Delivery 20%, Compliance 20%)",
                'RiskFlags': risk_flags,
                'Recommendation': f"Consider for {'PRIMARY' if rank == 1 else 'BACKUP'} supplier"
            }
            recommendations.append(rec)
        
        logger.info(f"[Tool 6] Generated {len(recommendations)} recommendations")
        return {
            'status': 'success',
            'rfp_id': rfp_id,
            'recommendation_count': len(recommendations),
            'recommendations': recommendations,
            'approval_status': 'READY_FOR_APPROVAL'
        }
    except Exception as e:
        logger.error(f"[Tool 6] Error in recommendation: {str(e)}")
        return {'status': 'error', 'message': str(e), 'recommendations': []}


# ============================================================================
# MAIN HANDLER - ORCHESTRATE ALL 6 TOOLS
# ============================================================================
def handler(event, context):
    start_time = time.time()
    invocation_id = context.aws_request_id if context else "local"

    # Parse body — API Gateway sends body as string or dict
    body = event.get("body", {})
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {}

    message = body.get("message", "").strip() if isinstance(body, dict) else ""

    # Structured log — invocation start
    logger.info(json.dumps({
        "event":          "invocation_start",
        "invocation_id":  invocation_id,
        "input_message":  message[:500],
    }))

    # Validate input
    if not message:
        logger.info(json.dumps({
            "event":            "invocation_complete",
            "invocation_id":    invocation_id,
            "response_status":  400,
        }))
        return _response(400, {"error": "message field required"})

    try:
        # Execute all 6 tools in sequence
        logger.info("[WORKFLOW] Starting RFP workflow...")
        
        # Tool 1: Supplier Lookup
        supplier_result = tool_supplier_lookup(message)
        suppliers = supplier_result.get('suppliers', [])
        
        if not suppliers:
            return _response(400, {"error": "No suppliers found for your requirement"})
        
        # Tool 2: RFP Generation
        rfp_result = tool_rfp_generation(message, suppliers)
        rfp_id = rfp_result.get('rfp_id', 'UNKNOWN')
        
        # Tool 3: Email Dispatch
        email_result = tool_email_dispatch(rfp_id, suppliers)
        
        # Tool 4: Proposal Fetch
        proposal_result = tool_proposal_fetch(rfp_id, suppliers)
        proposals = proposal_result.get('proposals', [])
        
        # Tool 5: Scoring
        scoring_result = tool_scoring(rfp_id, proposals)
        scored_proposals = scoring_result.get('scored_proposals', [])
        
        # Tool 6: Recommendation
        recommendation_result = tool_recommendation(rfp_id, scored_proposals)
        
        # Build final response
        final_response = {
            "workflow_status": "SUCCESS",
            "invocation_id": invocation_id,
            "rfp_id": rfp_id,
            "timestamp": datetime.now().isoformat(),
            "requirement": message,
            "tool_results": {
                "tool_1_supplier_lookup": {
                    "status": supplier_result.get('status'),
                    "supplier_count": supplier_result.get('supplier_count'),
                    "suppliers": [
                        {
                            "name": s['SupplierName'],
                            "capabilities": s['Capabilities'],
                            "email": s['Email']
                        } for s in suppliers
                    ]
                },
                "tool_2_rfp_generation": {
                    "status": rfp_result.get('status'),
                    "rfp_id": rfp_result.get('rfp_id'),
                    "s3_location": rfp_result.get('s3_location')
                },
                "tool_3_email_dispatch": {
                    "status": email_result.get('status'),
                    "email_count": email_result.get('email_count')
                },
                "tool_4_proposal_fetch": {
                    "status": proposal_result.get('status'),
                    "proposal_count": proposal_result.get('proposal_count')
                },
                "tool_5_scoring": {
                    "status": scoring_result.get('status'),
                    "scored_count": scoring_result.get('scored_count'),
                    "top_3_scores": [
                        {
                            "supplier": p['SupplierName'],
                            "score": p['TotalScore'],
                            "price": p['Price'],
                            "delivery_days": p['DeliveryTime']
                        } for p in scored_proposals[:3]
                    ]
                },
                "tool_6_recommendation": {
                    "status": recommendation_result.get('status'),
                    "recommendation_count": recommendation_result.get('recommendation_count'),
                    "approval_status": recommendation_result.get('approval_status'),
                    "recommendations": recommendation_result.get('recommendations', [])
                }
            },
            "summary": {
                "suppliers_contacted": supplier_result.get('supplier_count'),
                "proposals_received": proposal_result.get('proposal_count'),
                "recommended_supplier": recommendation_result.get('recommendations')[0]['SupplierName'] if recommendation_result.get('recommendations') else 'N/A',
                "next_step": "AWAITING_APPROVAL"
            }
        }
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(json.dumps({
            "event": "invocation_complete",
            "invocation_id": invocation_id,
            "response_status": 200,
            "duration_ms": duration_ms,
            "rfp_id": rfp_id
        }))
        
        return _response(200, final_response)
        
    except Exception as e:
        logger.error(json.dumps({
            "event": "agent_error",
            "invocation_id": invocation_id,
            "error": str(e),
        }))
        return _response(500, {"error": str(e), "type": type(e).__name__})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }

HANDLER_EOF

echo "✅ Handler file updated"

# Build Docker image
echo ""
echo "Building Docker image..."
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .

echo "✅ Docker image built"

# Tag for ECR
echo ""
echo "Tagging for ECR..."
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest

echo "✅ Tagged"

# Push to ECR
echo ""
echo "Pushing to ECR (this may take 2-5 minutes)..."
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest

echo "✅ Pushed to ECR"

# Update Lambda function
echo ""
echo "Updating Lambda function..."
aws lambda update-function-code \
  --function-name rfp-agent-handler \
  --image-uri 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest \
  --region us-east-1

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         ✅ STEP 2 COMPLETE - Lambda Updated!              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Next: Execute STEP 3 (Lambda test)"
echo "Then: Execute STEP 4 (API test)"
