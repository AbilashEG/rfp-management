# AgentCore Setup Guide
## Complete Configuration of All 6 Pillars

---

## **Overview: What is AgentCore?**

Amazon Bedrock **AgentCore** is an orchestration platform for AI agents with 6 pillars:

| Pillar | Purpose | What We're Building |
|--------|---------|-------------------|
| **Runtime** | Executes agent logic | Runs the RFP Agent through Bedrock |
| **Memory** | Persists session state | Saves RFP_ID, supplier list, scores across calls |
| **Gateway (MCP)** | Tool interface | Exposes 6 RFP tools via Model Context Protocol |
| **Observability** | Logging & metrics | CloudWatch logs + metrics dashboard |
| **Policy** | Human approval gates | Approval required when risks detected |
| **Identity** | Authentication | Cognito user pools + token validation |

---

## **Pre-Setup Checklist**

Before starting AgentCore setup, ensure you have completed:

- ✅ DynamoDB tables created (4 tables)
- ✅ S3 bucket created
- ✅ Supplier data seeded
- ✅ Lambda IAM role created with permissions
- ✅ Docker image pushed to ECR
- ✅ Lambda function `rfp-agent-handler` deployed
- ✅ API Gateway created and deployed

If any of these are missing, complete the **AWS_DEPLOYMENT_GUIDE.md** first.

---

## **PHASE 1: AgentCore Memory Setup**

AgentCore Memory stores session-level data (RFP_ID, supplier_ids, approval status) across multiple agent invocations.

### Create Knowledge Base for Memory

Knowledge Bases in Bedrock store and retrieve structured session data.

```bash
MEMORY_ID=$(aws bedrock-agent create-knowledge-base \
  --name rfp-agent-memory \
  --description "Session memory for RFP Agent lifecycle data" \
  --knowledge-base-configuration type=VECTOR \
  --storage-configuration \
    type=OPENSEARCH,\
    opensearchServerlessConfiguration={collectionArn=arn:aws:aoss:us-east-1:689050397154:collection/rfp-agent-memory} \
  --region us-east-1 \
  --query 'knowledgeBase.knowledgeBaseId' \
  --output text)

echo "AgentCore Memory ID: $MEMORY_ID"
```

**Save this** as `AGENTCORE_MEMORY_ID` in config.py.

---

## **PHASE 2: AgentCore Runtime Setup**

The Runtime pillar creates the agent execution engine.

### Create AgentCore Agent

```bash
AGENT_ID=$(aws bedrock-agent create-agent \
  --agent-name supplier-rfp-agent \
  --agent-role-arn arn:aws:iam::689050397154:role/rfp-agent-lambda-role \
  --description "Intelligent Supplier RFP Management Agent for automotive industry" \
  --foundation-model amazon.nova-pro-v1:0 \
  --instruction "You are an intelligent Supplier RFP Management Agent for automotive and manufacturing procurement. Your job is to autonomously manage the full RFP lifecycle: find suppliers, generate RFP documents, dispatch via email, collect proposals, score them, and recommend top suppliers. Always follow the exact tool invocation sequence defined in your system prompt." \
  --region us-east-1 \
  --query 'agent.agentId' \
  --output text)

echo "AgentCore Agent ID: $AGENT_ID"
```

**Save this** as `AGENTCORE_AGENT_ID` in config.py.

---

## **PHASE 3: AgentCore Gateway (MCP) Setup**

Register the 6 tools via the Model Context Protocol (MCP) Gateway.

### Tool 1: Supplier Lookup

```bash
AGENT_ID="<your-agent-id>"

aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name SupplierLookupActionGroup \
  --description "Query suppliers by component category and region" \
  --function-schema '{
    "functions": [{
      "name": "supplier_lookup_tool",
      "description": "Queries DynamoDB to find active suppliers matching the given component category. Optionally filters by region.",
      "parameters": {
        "type": "object",
        "properties": {
          "category": {"type": "string", "description": "Component category (e.g., brake_systems, sensors)"},
          "region": {"type": "string", "description": "Optional AWS region filter"}
        },
        "required": ["category"]
      }
    }]
  }' \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1
```

### Tool 2: RFP Generator

```bash
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name RFPGeneratorActionGroup \
  --description "Generate structured RFP documents" \
  --function-schema '{
    "functions": [{
      "name": "rfp_generator_tool",
      "description": "Generates a structured RFP document, saves it to S3, and creates an RFP record in DynamoDB.",
      "parameters": {
        "type": "object",
        "properties": {
          "component_name": {"type": "string", "description": "Name of the component needed"},
          "specs": {"type": "string", "description": "Technical specifications"},
          "quantity": {"type": "integer", "description": "Number of units required"},
          "deadline": {"type": "string", "description": "Delivery deadline (YYYY-MM-DD)"},
          "supplier_ids": {"type": "array", "items": {"type": "string"}, "description": "List of supplier IDs"}
        },
        "required": ["component_name", "specs", "quantity", "deadline", "supplier_ids"]
      }
    }]
  }' \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1
```

### Tool 3: Email Dispatch

```bash
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name EmailDispatchActionGroup \
  --description "Dispatch RFP emails to suppliers" \
  --function-schema '{
    "functions": [{
      "name": "email_dispatch_tool",
      "description": "Dispatches RFP email to each supplier in the list",
      "parameters": {
        "type": "object",
        "properties": {
          "rfp_id": {"type": "string", "description": "The RFP reference ID"},
          "supplier_ids": {"type": "array", "items": {"type": "string"}, "description": "List of supplier IDs"},
          "rfp_content": {"type": "string", "description": "The full RFP document text"}
        },
        "required": ["rfp_id", "supplier_ids", "rfp_content"]
      }
    }]
  }' \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1
```

### Tool 4: Proposal Fetch

```bash
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name ProposalFetchActionGroup \
  --description "Fetch submitted supplier proposals" \
  --function-schema '{
    "functions": [{
      "name": "proposal_fetch_tool",
      "description": "Fetches submitted proposals for the given RFP from DynamoDB. Auto-generates mock proposals in demo mode.",
      "parameters": {
        "type": "object",
        "properties": {
          "rfp_id": {"type": "string", "description": "The RFP ID"},
          "supplier_ids": {"type": "array", "items": {"type": "string"}, "description": "Expected supplier IDs"}
        },
        "required": ["rfp_id", "supplier_ids"]
      }
    }]
  }' \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1
```

### Tool 5: Scoring

```bash
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name ScoringActionGroup \
  --description "Score proposals using multi-criteria evaluation" \
  --function-schema '{
    "functions": [{
      "name": "scoring_tool",
      "description": "Scores each proposal using weighted multi-criteria scoring: Price 30%, Quality 30%, Delivery 20%, Compliance 20%.",
      "parameters": {
        "type": "object",
        "properties": {
          "rfp_id": {"type": "string", "description": "The RFP ID"},
          "proposals": {"type": "array", "items": {"type": "object"}, "description": "List of proposal objects"}
        },
        "required": ["rfp_id", "proposals"]
      }
    }]
  }' \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1
```

### Tool 6: Recommendation

```bash
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name RecommendationActionGroup \
  --description "Generate ranked supplier recommendations" \
  --function-schema '{
    "functions": [{
      "name": "recommendation_tool",
      "description": "Generates final ranked Top-2 supplier recommendation with risk flags and human approval gate trigger",
      "parameters": {
        "type": "object",
        "properties": {
          "rfp_id": {"type": "string", "description": "The RFP ID"},
          "scored_proposals": {"type": "array", "items": {"type": "object"}, "description": "List of scored proposals"}
        },
        "required": ["rfp_id", "scored_proposals"]
      }
    }]
  }' \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1
```

---

## **PHASE 4: AgentCore Policy Setup (Human Approval Gate)**

Policy defines rules for human approval when risks are detected.

### Create Approval Gate Role

```bash
aws iam create-role \
  --role-name rfp-approval-gate \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "bedrock-agent.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --region us-east-1
```

### Create Policy Rule

```bash
AGENT_ID="<your-agent-id>"

aws bedrock-agent create-agent-policy \
  --agent-id $AGENT_ID \
  --policy-name RFPApprovalPolicy \
  --policy-definition '{
    "version": "1.0",
    "rules": [
      {
        "name": "halt-on-risk-flags",
        "description": "Require human approval when approval_required is True",
        "condition": "approval_required == true",
        "action": "HALT_AND_WAIT_FOR_APPROVAL"
      }
    ]
  }' \
  --region us-east-1
```

This ensures that whenever the Recommendation Tool sets `approval_required: True`, the agent halts and waits for a procurement manager to review and approve or reject.

---

## **PHASE 5: AgentCore Observability Setup**

Observability captures metrics, logs, and traces.

### Create CloudWatch Log Group

```bash
aws logs create-log-group \
  --log-group-name /aws/bedrock/rfp-agent \
  --region us-east-1

aws logs put-retention-policy \
  --log-group-name /aws/bedrock/rfp-agent \
  --retention-in-days 30 \
  --region us-east-1
```

### Create CloudWatch Metrics

```bash
# Metric for tool invocations
aws cloudwatch put-metric-alarm \
  --alarm-name rfp-tool-invocation-count \
  --alarm-description "Count of RFP tool invocations" \
  --namespace RFPAgent/Tools \
  --metric-name InvocationCount \
  --statistic Sum \
  --period 60 \
  --evaluation-periods 1 \
  --threshold 0 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --region us-east-1

# Metric for agent reasoning duration
aws cloudwatch put-metric-alarm \
  --alarm-name rfp-reasoning-duration \
  --alarm-description "RFP Agent reasoning duration in milliseconds" \
  --namespace RFPAgent/Performance \
  --metric-name ReasoningDuration \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 30000 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --region us-east-1

# Metric for approval gate triggers
aws cloudwatch put-metric-alarm \
  --alarm-name rfp-approval-gate-triggered \
  --alarm-description "Count of times approval gate triggered" \
  --namespace RFPAgent/Policy \
  --metric-name ApprovalGateTriggered \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 0 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --region us-east-1
```

### Enable Agent Tracing

```bash
AGENT_ID="<your-agent-id>"

aws bedrock-agent update-agent \
  --agent-id $AGENT_ID \
  --enable-user-input true \
  --enable-trace true \
  --region us-east-1
```

---

## **PHASE 6: AgentCore Identity Setup (Cognito)**

Identity (backed by Cognito) ensures only authorized users invoke the agent.

### Create Cognito User Pool

```bash
USER_POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name rfp-agent-users \
  --policies '{
    "PasswordPolicy": {
      "MinimumLength": 8,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": false
    }
  }' \
  --region us-east-1 \
  --query 'UserPool.Id' \
  --output text)

echo "Cognito User Pool ID: $USER_POOL_ID"
```

### Create App Client

```bash
APP_CLIENT_ID=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-name rfp-agent-client \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --prevent-user-existence-errors ENABLED \
  --region us-east-1 \
  --query 'UserPoolClient.ClientId' \
  --output text)

echo "App Client ID: $APP_CLIENT_ID"
```

### Create Test User

```bash
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username procure-manager-01 \
  --temporary-password "TempPassword123!" \
  --message-action SUPPRESS \
  --region us-east-1

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username procure-manager-01 \
  --password "PermanentPassword123!" \
  --permanent \
  --region us-east-1
```

---

## **PHASE 7: Update Lambda to Use AgentCore Identity**

Modify `lambda/rfp_agent_handler.py` to verify Cognito tokens:

```python
import boto3
import json
from jose import jwt
import requests

cognito_client = boto3.client('cognito-idp', region_name='us-east-1')

def verify_cognito_token(token):
    """Verify the Cognito token in the Authorization header"""
    try:
        # Get public keys from Cognito
        user_pool_id = "us-east-1_xxxxxxxxx"  # from config.py
        keys_url = f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        keys = requests.get(keys_url).json()
        
        # Decode and verify JWT
        kid = jwt.get_unverified_header(token)['kid']
        key = next((k for k in keys['keys'] if k['kid'] == kid), None)
        
        if not key:
            return False
        
        payload = jwt.decode(token, key, algorithms=['RS256'])
        return payload
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None

def handler(event, context):
    # Extract Authorization header
    headers = event.get('headers', {})
    auth_header = headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return _response(401, {"error": "Unauthorized — Missing Bearer token"})
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    payload = verify_cognito_token(token)
    
    if not payload:
        return _response(401, {"error": "Unauthorized — Invalid token"})
    
    # Token is valid, proceed with agent invocation
    # ... rest of handler code
```

---

## **PHASE 8: Update config.py with AgentCore IDs**

After completing all setup steps, update your `config.py`:

```python
# config.py

REGION = "us-east-1"
BEDROCK_MODEL_ID = "amazon.nova-pro-v1:0"

# DynamoDB
SUPPLIERS_TABLE = "rfp-suppliers"
REQUESTS_TABLE  = "rfp-requests"
PROPOSALS_TABLE = "rfp-proposals"
SCORES_TABLE    = "rfp-scores"

# S3
RFP_DOCS_BUCKET = "rfp-documents-quadrasystems"
RFP_DOCS_PREFIX = "rfp-docs/"

# SES
SES_SENDER_EMAIL = "rfp-agent@quadrasystems.com"
SES_MOCK_MODE    = True

# Cognito (from Phase 6)
COGNITO_USER_POOL_ID  = "us-east-1_xxxxxxxxx"  # Your pool ID
COGNITO_APP_CLIENT_ID = "xxxxxxxxxxxxxxxx"     # Your app client ID

# ECR / Lambda
AWS_ACCOUNT_ID  = "689050397154"
ECR_URI         = "689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent"
LAMBDA_ROLE_ARN = "arn:aws:iam::689050397154:role/rfp-agent-lambda-role"

# AgentCore IDs (from Phase 1 & 2)
AGENTCORE_MEMORY_ID = "kb-xxxxxxxxxxxxxxxx"       # From Phase 1
AGENTCORE_AGENT_ID  = "agent-xxxxxxxxxxxxxxxx"    # From Phase 2

# Scoring Weights
PRICE_WEIGHT      = 0.30
QUALITY_WEIGHT    = 0.30
DELIVERY_WEIGHT   = 0.20
COMPLIANCE_WEIGHT = 0.20
```

---

## **PHASE 9: Testing AgentCore**

### Test with Cognito Token

```bash
# Get token
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_xxxxxxxxx \
  --client-id xxxxxxxxxxxxxxxx \
  --auth-flow ADMIN_USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=procure-manager-01,PASSWORD=PermanentPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.AccessToken' \
  --output text)

# Call API with token
API_ENDPOINT="https://{API_ID}.execute-api.us-east-1.amazonaws.com/prod/process-rfp"

curl -X POST $API_ENDPOINT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "We need 500 units of brake sensors for ABS systems. Specs: High-precision wheel speed sensor, IP67 rated, -40°C to 125°C operating range. Deadline: 2026-09-30."
  }'
```

### Expected Response

```json
{
  "response": "RFP lifecycle completed successfully.\n\nRFP-20250112-A1B2C3D4 generated.\n\nSupplier Lookup: Found 3 suppliers in sensors category.\n\nEmail Dispatch: Sent RFP to 3 suppliers (SUP003, SUP007, SUP005).\n\nProposal Fetch: Received 3 proposals.\n\nScoring Results:\n1. SUP003 (AutoSensor Global): 97.5/100 - SHORTLIST\n2. SUP007 (ElectroAuto Systems): 83.2/100 - REVIEW (Long lead time)\n3. SUP005 (NexaComponents): 62.1/100 - REVIEW (No certifications)\n\n⚠️ HUMAN APPROVAL REQUIRED — Risk flags detected in recommendations. Procurement manager must review before contract award.\n\nApproval Status: Pending Human Review"
}
```

---

## **Troubleshooting AgentCore Setup**

### Issue: "InvalidParameterException: OpenSearch configuration is invalid"
**Solution:** Create OpenSearch Serverless collection first:
```bash
aws opensearchserverless create-collection \
  --name rfp-agent-memory \
  --region us-east-1
```

### Issue: "Agent not found after creation"
**Solution:** Wait 10-15 seconds after agent creation, then verify:
```bash
aws bedrock-agent get-agent --agent-id $AGENT_ID --region us-east-1
```

### Issue: "Tool invocation timeout"
**Solution:** Increase Lambda timeout and memory:
```bash
aws lambda update-function-configuration \
  --function-name rfp-agent-handler \
  --timeout 600 \
  --memory-size 1024 \
  --region us-east-1
```

### Issue: "Cognito token verification fails"
**Solution:** Ensure the token hasn't expired and is being passed correctly:
```bash
# Decode token to verify claims
python -c "
import json, base64
token = 'YOUR_TOKEN_HERE'
parts = token.split('.')
payload = base64.urlsafe_b64decode(parts[1] + '==')
print(json.dumps(json.loads(payload), indent=2))
"
```

---

## **Verification Checklist**

- [ ] Knowledge Base created (AGENTCORE_MEMORY_ID saved)
- [ ] Agent registered with Bedrock (AGENTCORE_AGENT_ID saved)
- [ ] All 6 tools registered via MCP Gateway
- [ ] Policy approval gate configured
- [ ] CloudWatch logs and metrics configured
- [ ] Cognito User Pool created
- [ ] Cognito App Client created
- [ ] Test user created with permanent password
- [ ] Lambda updated with Cognito token verification
- [ ] config.py updated with all IDs
- [ ] Test invocation with Bearer token successful
- [ ] Risk flagging triggers approval gate
- [ ] Full RFP lifecycle completes end-to-end

---

## **Next Steps: Production Readiness**

After AgentCore setup is complete:

1. **Configure EventBridge** for scheduled RFP processing
2. **Set up SNS notifications** for approval gates
3. **Enable X-Ray tracing** for distributed tracing
4. **Create cost alerts** in AWS Billing
5. **Set up automated backups** for DynamoDB
6. **Implement auto-scaling** for Lambda concurrency
7. **Create runbooks** for operational procedures

---

## **Reference Materials**

- AWS Bedrock AgentCore Docs: https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
- Cognito User Pools: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pools.html
- CloudWatch Observability: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/

