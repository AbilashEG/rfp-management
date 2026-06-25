"""
RFP Management System - AgentCore Runtime Orchestrator
Calls 6 Lambda tools directly via boto3 (IAM auth, no MCP complexity)
Model: amazon.nova-pro-v1:0 | Region: us-east-1 | Port: 8080

Health check: GET /ping → 200 OK
Agent invoke: POST / → {"message": "..."} → JSON response
"""

import os
import json
import boto3
import logging
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import uuid

from strands import Agent
from strands.models import BedrockModel
from strands import tool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

REGION = os.environ.get("REGION", "us-east-1")
MODEL_ID = "amazon.nova-pro-v1:0"
PORT = int(os.environ.get("PORT", 8080))

SYSTEM_PROMPT = """
You are an RFP procurement agent.

Run these 6 tools in order using outputs from each as inputs to next:
1. supplier_lookup(category, rfp_id)
2. rfp_generator(rfp_id, requirement, supplier_ids)
3. email_dispatch(rfp_id, supplier_emails, docx_presigned_url)
4. proposal_fetch(rfp_id, supplier_ids)
5. scoring(rfp_id, proposals)
6. recommendation(rfp_id, scored_proposals)

Return: rfp_id, top 2 suppliers with scores, approval_required status.
"""

# ============================================================================
# LAMBDA TOOL INVOCATION (direct boto3, uses IAM role automatically)
# ============================================================================

lambda_client = boto3.client("lambda", region_name=REGION)

# Correct Lambda function names
LAMBDA_FUNCTIONS = {
    "supplier_lookup":  "rfp-supplier-lookup",
    "rfp_generator":    "rfp-rfp-generator",
    "email_dispatch":   "rfp-email-dispatch",
    "proposal_fetch":   "rfp-proposal-fetch",
    "scoring":          "rfp-scoring",
    "recommendation":   "rfp-recommendation"
}


def invoke_lambda(function_name: str, payload: dict) -> dict:
    """Invoke a Lambda function and return parsed response body."""
    try:
        logger.info(f"[Lambda] Invoking: {function_name}")
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps({"body": payload})
        )
        raw = json.loads(response["Payload"].read())
        # Handle both string and dict body
        body = raw.get("body", raw)
        if isinstance(body, str):
            body = json.loads(body)
        logger.info(f"[Lambda] ✓ {function_name} completed")
        return body
    except Exception as e:
        logger.error(f"[Lambda] ✗ {function_name} failed: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# STRANDS TOOLS (wrapping Lambda calls)
# ============================================================================

@tool
def supplier_lookup(category: str, rfp_id: str) -> str:
    """Find qualified suppliers from DynamoDB by category.
    
    Args:
        category: The product category to search for suppliers (e.g. 'sensors', 'brakes')
        rfp_id: The RFP identifier for this request
    
    Returns:
        JSON string with list of matching suppliers
    """
    result = invoke_lambda(LAMBDA_FUNCTIONS["supplier_lookup"], {
        "category": category,
        "rfp_id": rfp_id
    })
    return json.dumps(result)


@tool
def rfp_generator(rfp_id: str, requirement: str, supplier_ids: list) -> str:
    """Generate RFP document and save to S3 and DynamoDB.
    
    Args:
        rfp_id: The unique RFP identifier
        requirement: Full requirement description from the user
        supplier_ids: List of supplier IDs to include in the RFP
    
    Returns:
        JSON string with RFP document details and S3 location
    """
    result = invoke_lambda(LAMBDA_FUNCTIONS["rfp_generator"], {
        "rfp_id": rfp_id,
        "requirement": requirement,
        "supplier_ids": supplier_ids
    })
    return json.dumps(result)


@tool
def email_dispatch(rfp_id: str, supplier_emails: list, google_form_url: str = "", docx_presigned_url: str = "") -> str:
    """Send RFP documents to suppliers via SES with Google Form URL and .docx link (mock mode enabled).
    
    Args:
        rfp_id: The RFP identifier to dispatch
        supplier_emails: List of supplier email addresses
        google_form_url: Google Form URL for proposal submission (from rfp_generator response)
        docx_presigned_url: Presigned S3 URL for the RFP .docx document (from rfp_generator response)
    
    Returns:
        JSON string confirming dispatch status
    """
    result = invoke_lambda(LAMBDA_FUNCTIONS["email_dispatch"], {
        "rfp_id": rfp_id,
        "supplier_emails": supplier_emails,
        "google_form_url": google_form_url,
        "docx_presigned_url": docx_presigned_url
    })
    return json.dumps(result)


@tool
def proposal_fetch(rfp_id: str, supplier_ids: list) -> str:
    """Fetch supplier proposals from DynamoDB for an RFP.
    
    Args:
        rfp_id: The RFP identifier to fetch proposals for
        supplier_ids: List of supplier IDs to fetch proposals from
    
    Returns:
        JSON string with all proposals received
    """
    result = invoke_lambda(LAMBDA_FUNCTIONS["proposal_fetch"], {
        "rfp_id": rfp_id,
        "supplier_ids": supplier_ids
    })
    return json.dumps(result)


@tool
def scoring(rfp_id: str, proposals: list) -> str:
    """Score proposals using weighted criteria: price 30%, quality 30%, delivery 20%, compliance 20%.
    
    Args:
        rfp_id: The RFP identifier
        proposals: List of proposal objects to score
    
    Returns:
        JSON string with scored list containing supplier_id, total_score, risk_flags
    """
    result = invoke_lambda(LAMBDA_FUNCTIONS["scoring"], {
        "rfp_id": rfp_id,
        "proposals": proposals
    })
    # Return the scored list directly for recommendation
    return json.dumps(result.get("scored", result))

@tool
def recommendation(rfp_id: str, scored_proposals: list) -> str:
    """Generate top 2 supplier recommendations with risk flags and approval decision.
    
    Args:
        rfp_id: The RFP identifier
        scored_proposals: List of scored proposals with supplier_id, total_score, risk_flags
    
    Returns:
        JSON string with top2, approval_required, report_url
    """
    result = invoke_lambda(LAMBDA_FUNCTIONS["recommendation"], {
        "rfp_id": rfp_id,
        "scored_proposals": scored_proposals
    })
    return json.dumps({
        "top2":              result.get("recommendations", []),
        "approval_required": result.get("approval_required", True),
        "report_url":        result.get("recommendation_docx_url", "")
    })


# ============================================================================
# AGENT RUNNER
# ============================================================================

def run_rfp_agent(message: str) -> dict:
    """Run the RFP Strands Agent with all 6 Lambda tools."""
    try:
        logger.info("Initializing BedrockModel...")
        model = BedrockModel(
            model_id=MODEL_ID,
            region_name=REGION
            # DO NOT set max_tokens here.
            # max_tokens truncates tool-call JSON mid-generation → modelStreamErrorException.
            # Context size is already controlled by slim Lambda responses.
        )
        logger.info("✓ BedrockModel initialized")

        logger.info("Initializing Strands Agent with 6 tools...")
        agent = Agent(
            model=model,
            tools=[
                supplier_lookup,
                rfp_generator,
                email_dispatch,
                proposal_fetch,
                scoring,
                recommendation
            ],
            system_prompt=SYSTEM_PROMPT
        )
        logger.info("✓ Strands Agent initialized")

        # Generate RFP ID and inject into message
        rfp_id = f"RFP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        full_message = f"RFP ID: {rfp_id}\n\n{message}"

        logger.info(f"Running agent for RFP: {rfp_id}")
        response = agent(full_message)
        logger.info("✓ Agent completed successfully")

        return {
            "status": "success",
            "rfp_id": rfp_id,
            "response": str(response)
        }

    except Exception as e:
        logger.error(f"Agent error: {e}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# ============================================================================
# HTTP SERVER (AgentCore Runtime compatible)
# ============================================================================

class RFPAgentHandler(BaseHTTPRequestHandler):
    """HTTP handler for AgentCore Runtime.
    
    GET /ping   → 200 {"status": "ok"}     (AgentCore health check)
    GET /health → 200 {"status": "ok"}     (standard health check)
    POST /      → runs RFP agent workflow
    """

    def do_GET(self):
        """Health check endpoints - AgentCore uses /ping."""
        if self.path in ("/ping", "/health"):
            body = json.dumps({"status": "ok"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_POST(self):
        """Handle agent invocation requests."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            # Support both "message" and "prompt" fields
            message = data.get("message") or data.get("prompt") or data.get("input") or ""

            if not message:
                resp = json.dumps({"error": "message field required"}).encode()
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
                return

            logger.info(f"Received request: {message[:120]}")
            result = run_rfp_agent(message)

            resp = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        except Exception as e:
            logger.error(f"Handler error: {e}")
            resp = json.dumps({"error": str(e)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

    def log_message(self, format, *args):
        logger.info(f"HTTP {format % args}")


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("RFP Agent Runtime starting")
    logger.info(f"  Port    : {PORT}")
    logger.info(f"  Region  : {REGION}")
    logger.info(f"  Model   : {MODEL_ID}")
    logger.info(f"  Tools   : 6 Lambda functions (direct boto3)")
    logger.info("=" * 60)

    server = HTTPServer(("0.0.0.0", PORT), RFPAgentHandler)
    logger.info(f"✓ Listening on 0.0.0.0:{PORT}")
    logger.info("✓ Health check: GET /ping → 200 OK")
    server.serve_forever()
