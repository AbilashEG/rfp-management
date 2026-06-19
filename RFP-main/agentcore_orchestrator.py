"""
RFP Management System - AgentCore Runtime Orchestrator
Connects to AgentCore Gateway MCP for real tool execution
Model: amazon.nova-pro-v1:0 | Region: us-east-1 | Port: 8080
"""

import os
import json
import boto3
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REGION = "us-east-1"
MODEL_ID = "amazon.nova-pro-v1:0"
GATEWAY_URL = os.environ.get(
    "AGENTCORE_GATEWAY_URL",
    "https://rfpmcpgateway-2lhpouzcif.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
)

SYSTEM_PROMPT = """
You are a Supplier RFP Management Agent for Automotive and Manufacturing procurement.

You MUST call these tools in EXACTLY this order every time.
Do NOT simulate or hallucinate tool outputs.
ALWAYS call the actual tool and use its real response.

MANDATORY TOOL EXECUTION ORDER:
1. supplier_lookup_tool     — find suppliers by category from DynamoDB
2. rfp_generator_tool       — generate RFP document, save to S3 + DynamoDB
3. email_dispatch_tool      — send RFP via SES (mock mode)
4. proposal_fetch_tool      — fetch proposals from DynamoDB
5. scoring_tool             — score proposals: price 30%, quality 30%, delivery 20%, compliance 20%
6. recommendation_tool      — rank top 2, set approval_required if flags exist

RULES:
- NEVER skip a tool call
- NEVER make up supplier names, scores, or RFP IDs
- ALWAYS use real tool output for next step input
- If approval_required = True, ask human to confirm
- Always show the real RFP ID from rfp_generator_tool output
- Model = amazon.nova-pro-v1:0
- Region = us-east-1
"""


def run_rfp_agent(message: str) -> dict:
    """Run the RFP agent with real MCP Gateway tools."""
    try:
        model = BedrockModel(
            model_id="amazon.nova-pro-v1:0",
            region_name="us-east-1"
        )

        with MCPClient(lambda: streamablehttp_client(GATEWAY_URL)) as mcp_client:
            tools = mcp_client.list_tools()
            logger.info(f"Tools from Gateway: {[t.name for t in tools]}")

            agent = Agent(
                model=model,
                tools=tools,
                system_prompt=SYSTEM_PROMPT
            )

            response = agent(message)

            return {
                "status": "success",
                "response": str(response)
            }

    except Exception as e:
        logger.error(f"Agent error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


class RFPAgentHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            message = data.get("message", "")

            if not message:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(
                    {"error": "message field required"}
                ).encode())
                return

            logger.info(f"Processing RFP request: {message[:100]}")
            result = run_rfp_agent(message)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        logger.info(f"HTTP {format % args}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting RFP Agent on port {port}")
    logger.info(f"Gateway URL: {GATEWAY_URL}")
    server = HTTPServer(("0.0.0.0", port), RFPAgentHandler)
    server.serve_forever()
