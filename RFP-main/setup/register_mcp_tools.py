"""
Register 5 RFP Lambda tools to AgentCore MCP Gateway via boto3 SDK.
Bypasses console UI schema validation bug.
"""

import boto3
import json
import sys

client = boto3.client("bedrock-agentcore", region_name="us-east-1")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Your Gateway ID (from: aws bedrock-agentcore list-gateways --region us-east-1)
GATEWAY_ID = "rfpmcpgateway-2lhpouzcif"

# Your AWS Account ID (from: aws sts get-caller-identity --query Account --output text)
ACCOUNT_ID = "689050397154"

# ============================================================================
# 5 TOOLS TO REGISTER (Supplier Lookup already registered, skip it)
# ============================================================================

TOOLS = [
    {
        "name": "rfp-generator-tool",
        "description": "Generates a structured RFP document for the given component requirement. Saves to S3 and creates RFP record in DynamoDB rfp-requests table.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rfp_id": {
                    "type": "string",
                    "description": "The RFP ID"
                },
                "requirement": {
                    "type": "string",
                    "description": "Full requirement description"
                },
                "supplier_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of supplier IDs to include in RFP"
                }
            },
            "required": ["rfp_id", "requirement", "supplier_ids"]
        },
        "lambdaArn": f"arn:aws:lambda:us-east-1:{ACCOUNT_ID}:function:rfp-rfp-generator"
    },
    {
        "name": "email-dispatch-tool",
        "description": "Dispatches RFP email to each supplier via Amazon SES. Runs in mock mode by default.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rfp_id": {
                    "type": "string",
                    "description": "The RFP reference ID"
                },
                "supplier_emails": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of supplier email addresses"
                }
            },
            "required": ["rfp_id", "supplier_emails"]
        },
        "lambdaArn": f"arn:aws:lambda:us-east-1:{ACCOUNT_ID}:function:rfp-email-dispatch"
    },
    {
        "name": "proposal-fetch-tool",
        "description": "Fetches submitted proposals for the given RFP from DynamoDB. Auto-generates mock proposals if none exist.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rfp_id": {
                    "type": "string",
                    "description": "The RFP ID to fetch proposals for"
                },
                "supplier_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Expected supplier IDs"
                }
            },
            "required": ["rfp_id", "supplier_ids"]
        },
        "lambdaArn": f"arn:aws:lambda:us-east-1:{ACCOUNT_ID}:function:rfp-proposal-fetch"
    },
    {
        "name": "scoring-tool",
        "description": "Scores each proposal using weighted multi-criteria: price 30%, quality 30%, delivery 20%, compliance 20%. Flags risks and saves to rfp-scores table.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rfp_id": {
                    "type": "string",
                    "description": "The RFP ID being evaluated"
                },
                "proposals": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of proposal dicts from proposal_fetch_tool"
                }
            },
            "required": ["rfp_id", "proposals"]
        },
        "lambdaArn": f"arn:aws:lambda:us-east-1:{ACCOUNT_ID}:function:rfp-scoring"
    },
    {
        "name": "recommendation-tool",
        "description": "Generates final ranked supplier recommendation. Returns top 2 suppliers with scores, reasoning, and flags. Sets approval_required if any risks detected.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rfp_id": {
                    "type": "string",
                    "description": "The RFP ID"
                },
                "scored_proposals": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of scored proposal dicts from scoring_tool"
                }
            },
            "required": ["rfp_id", "scored_proposals"]
        },
        "lambdaArn": f"arn:aws:lambda:us-east-1:{ACCOUNT_ID}:function:rfp-recommendation"
    }
]

# ============================================================================
# REGISTER TOOLS
# ============================================================================

def register_tools():
    """Register all 5 tools to the MCP Gateway"""
    success = []
    failed = []
    
    print(f"\n{'='*80}")
    print(f"Registering {len(TOOLS)} RFP tools to Gateway: {GATEWAY_ID}")
    print(f"{'='*80}\n")
    
    for tool in TOOLS:
        print(f"[*] Registering: {tool['name']}...")
        
        try:
            response = client.create_gateway_target(
                gatewayIdentifier=GATEWAY_ID,
                targetName=tool["name"],
                targetDescription=tool["description"],
                targetConfiguration={
                    "mcp": {
                        "lambda": {
                            "lambdaArn": tool["lambdaArn"],
                            "toolSchema": {
                                "inlinePayload": [
                                    {
                                        "name": tool["name"],
                                        "description": tool["description"],
                                        "inputSchema": tool["inputSchema"]
                                    }
                                ]
                            }
                        }
                    }
                }
            )
            
            print(f"    ✅ Registered successfully")
            print(f"    Target ID: {response.get('targetId', 'N/A')}\n")
            success.append(tool["name"])
            
        except Exception as e:
            print(f"    ❌ Registration failed")
            print(f"    Error: {str(e)}\n")
            failed.append({"tool": tool["name"], "error": str(e)})
    
    # Summary
    print(f"{'='*80}")
    print(f"REGISTRATION SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successfully registered: {len(success)}/{len(TOOLS)}")
    print(f"❌ Failed: {len(failed)}/{len(TOOLS)}\n")
    
    if success:
        print("Registered tools:")
        for tool in success:
            print(f"  ✅ {tool}")
    
    if failed:
        print("\nFailed tools:")
        for f in failed:
            print(f"  ❌ {f['tool']}")
            print(f"     Error: {f['error']}")
    
    print(f"{'='*80}\n")
    
    return len(failed) == 0

if __name__ == "__main__":
    success = register_tools()
    sys.exit(0 if success else 1)
