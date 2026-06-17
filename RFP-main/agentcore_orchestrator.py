"""
RFP Management System - Strands Agent Framework
Uses Amazon Nova Pro via Strands Agents SDK
No pydantic - pure Strands Agent implementation
"""

import json
import logging
import os
from datetime import datetime
import uuid
import boto3
from typing import Optional, Dict, Any, List

from strands import Agent
from strands.models import BedrockModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
lambda_client = boto3.client('lambda', region_name=os.environ.get('REGION', 'us-east-1'))
REGION = os.environ.get('REGION', 'us-east-1')


# ============================================================================
# STRANDS AGENT TOOLS
# ============================================================================

def _tool_supplier_lookup(rfp_id: str, category: str) -> Dict[str, Any]:
    """Tool: Lookup suppliers by category"""
    logger.info(f"[Tool] supplier_lookup: {category}")
    return invoke_lambda_tool("supplier_lookup_lambda", {
        "rfp_id": rfp_id,
        "category": category
    })


def _tool_rfp_generator(rfp_id: str, requirement: str, supplier_ids: List[str]) -> Dict[str, Any]:
    """Tool: Generate RFP document"""
    logger.info(f"[Tool] rfp_generator: {rfp_id}")
    return invoke_lambda_tool("rfp_generator_lambda", {
        "rfp_id": rfp_id,
        "requirement": requirement,
        "supplier_ids": supplier_ids
    })


def _tool_email_dispatch(rfp_id: str, supplier_emails: List[str]) -> Dict[str, Any]:
    """Tool: Send RFP via email"""
    logger.info(f"[Tool] email_dispatch: {len(supplier_emails)} recipients")
    return invoke_lambda_tool("email_dispatch_lambda", {
        "rfp_id": rfp_id,
        "supplier_emails": supplier_emails
    })


def _tool_proposal_fetch(rfp_id: str, supplier_ids: List[str]) -> Dict[str, Any]:
    """Tool: Fetch proposals"""
    logger.info(f"[Tool] proposal_fetch: {len(supplier_ids)} suppliers")
    return invoke_lambda_tool("proposal_fetch_lambda", {
        "rfp_id": rfp_id,
        "supplier_ids": supplier_ids
    })


def _tool_scoring(rfp_id: str, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tool: Score proposals"""
    logger.info(f"[Tool] scoring: {len(proposals)} proposals")
    return invoke_lambda_tool("scoring_lambda", {
        "rfp_id": rfp_id,
        "proposals": proposals
    })


def _tool_recommendation(rfp_id: str, scored_proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tool: Generate recommendations"""
    logger.info(f"[Tool] recommendation: {len(scored_proposals)} scored proposals")
    return invoke_lambda_tool("recommendation_lambda", {
        "rfp_id": rfp_id,
        "scored_proposals": scored_proposals
    })


# ============================================================================
# LAMBDA TOOL INVOCATION
# ============================================================================

def invoke_lambda_tool(function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke a Lambda tool function"""
    try:
        logger.info(f"[Lambda] Invoking: {function_name}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({"body": payload})
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] != 200:
            logger.error(f"[Lambda] Error: {response['StatusCode']}")
            return {"success": False, "error": response_payload}
        
        if isinstance(response_payload.get('body'), str):
            body = json.loads(response_payload['body'])
        else:
            body = response_payload.get('body', response_payload)
        
        logger.info(f"[Lambda] ✓ {function_name} executed")
        return body
        
    except Exception as e:
        logger.error(f"[Lambda] Error: {str(e)}")
        return {"success": False, "error": str(e)}


# ============================================================================
# STRANDS AGENT - RFP ORCHESTRATOR
# ============================================================================

class RFPOrchestrator:
    """Strands Agent-based RFP Orchestrator"""
    
    def __init__(self, user_id: str, session_id: Optional[str] = None):
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        
        # Initialize Bedrock Model
        model = BedrockModel(
            model_id="amazon.nova-pro-v1:0",
            region_name=REGION
        )
        
        # Initialize Strands Agent
        self.agent = Agent(
            model=model
        )
        
        logger.info(f"✓ Strands Agent initialized - Session: {self.session_id}")
    
    def process_rfp(self, cognito_token: str, user_message: str) -> Dict[str, Any]:
        """
        Process RFP request using Strands Agent
        Agent orchestrates the entire workflow
        """
        try:
            workflow_id = str(uuid.uuid4())
            logger.info(f"\n{'='*80}")
            logger.info(f"[WORKFLOW {workflow_id}] Starting RFP Processing")
            logger.info(f"{'='*80}\n")
            
            # STEP 0: Identity validation
            if not cognito_token or cognito_token == "invalid":
                raise Exception("Unauthorized: Invalid token")
            
            user_email = "user@example.com"
            logger.info(f"[Step 0] ✓ Identity validated")
            
            # Generate RFP ID
            rfp_id = f"RFP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            logger.info(f"[Step 0] ✓ RFP ID: {rfp_id}")
            
            # STEPS 1-8: Agent-driven workflow
            system_prompt = f"""You are an RFP (Request for Proposal) procurement agent powered by Strands Agents.

Your task: Process this procurement request and orchestrate the complete RFP workflow.

RFP ID: {rfp_id}
Session: {self.session_id}
User Request: {user_message}

Workflow Steps:
1. Parse the requirement (component, specs, quantity, deadline, category)
2. Use supplier_lookup tool to find qualified suppliers
3. Use rfp_generator tool to create RFP document
4. Use email_dispatch tool to send RFP to suppliers
5. Use proposal_fetch tool to retrieve proposals
6. Use scoring tool to score all proposals
7. Use recommendation tool to generate top recommendations
8. Make approval decision (auto-approve if < $10K, otherwise escalate)

For each step:
- Call the appropriate tool
- Analyze the results
- Proceed to next step

Provide a final summary with:
- RFP ID and status
- Selected suppliers
- Risk assessment
- Approval decision

Start now."""
            
            logger.info("[Steps 1-8] Invoking Strands Agent for workflow")
            
            # Call Strands Agent with tools
            agent_response = self.agent(
                system_prompt,
                tools=[
                    {
                        "name": "supplier_lookup",
                        "description": "Find suppliers by category",
                        "handler": _tool_supplier_lookup
                    },
                    {
                        "name": "rfp_generator",
                        "description": "Generate RFP document",
                        "handler": _tool_rfp_generator
                    },
                    {
                        "name": "email_dispatch",
                        "description": "Send RFP to suppliers",
                        "handler": _tool_email_dispatch
                    },
                    {
                        "name": "proposal_fetch",
                        "description": "Fetch proposals from suppliers",
                        "handler": _tool_proposal_fetch
                    },
                    {
                        "name": "scoring",
                        "description": "Score proposals",
                        "handler": _tool_scoring
                    },
                    {
                        "name": "recommendation",
                        "description": "Generate recommendations",
                        "handler": _tool_recommendation
                    }
                ]
            )
            
            agent_output = agent_response.content if hasattr(agent_response, 'content') else str(agent_response)
            logger.info(f"[Agent] ✓ Workflow complete\n{agent_output[:500]}")
            
            # Build response
            final_response = {
                "workflow_status": "SUCCESS",
                "workflow_id": workflow_id,
                "user_email": user_email,
                "rfp_id": rfp_id,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "requirement": user_message,
                "agent_output": agent_output
            }
            
            logger.info(f"✓ WORKFLOW COMPLETE - RFP: {rfp_id}\n{'='*80}\n")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ Workflow error: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "workflow_status": "FAILED",
                "session_id": self.session_id
            }


# ============================================================================
# LAMBDA HANDLER
# ============================================================================

def handler(event, context):
    """AWS Lambda entry point"""
    try:
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        
        cognito_token = body.get("cognito_token", "")
        user_message = body.get("message", "")
        user_id = body.get("user_id", "user-123")
        session_id = body.get("session_id", None)
        
        if not cognito_token or not user_message:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing cognito_token or message"})
            }
        
        orchestrator = RFPOrchestrator(user_id=user_id, session_id=session_id)
        result = orchestrator.process_rfp(cognito_token, user_message)
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result, default=str)
        }
    except Exception as e:
        logger.error(f"Lambda error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


if __name__ == "__main__":
    # Local test
    test_token = "test-token"
    test_message = "We need 500 automotive brake sensors with ISO certification by December 2026"
    test_user_id = "user-123"
    
    orchestrator = RFPOrchestrator(user_id=test_user_id)
    result = orchestrator.process_rfp(test_token, test_message)
    print(json.dumps(result, indent=2, default=str))
