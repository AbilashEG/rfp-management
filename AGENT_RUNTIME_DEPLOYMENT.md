# Agent Runtime Deployment & Gateway Integration

**Status**: Planning  
**Date**: 2026-06-17  
**Objective**: Deploy orchestrator agent with API Gateway + tool integration + observability

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     Client Application                           │
│                  (API Gateway HTTP Endpoint)                      │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP POST /process-rfp
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│              API Gateway + Cognito Authorization                 │
│                                                                  │
│  • Authentication: Cognito tokens                                │
│  • CORS: Enabled for web/mobile clients                          │
│  • Throttling: Rate limiting configured                          │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│      Orchestrator Agent (Lambda) - MAIN RUNTIME                  │
│                                                                  │
│  • Amazon Nova Pro (Bedrock) LLM                                 │
│  • Strands Agents SDK                                            │
│  • Conversation History (agentcore-memory-v2)                    │
│  • Tool Invocation Logic                                         │
│  • Approval Decision Making                                      │
│                                                                  │
│  ├─ X-Ray Tracing: Full request tracing                          │
│  ├─ CloudWatch Logs: Structured logging                          │
│  └─ Custom Metrics: Agent performance metrics                    │
└──────────────┬────────┬────────┬────────┬────────┬───────────────┘
               │        │        │        │        │
        ┌──────┴──┐ ┌──────────┐ ┌─────────────┐ ┌──────────────┐
        │ Sync    │ │ Parallel │ │ Sequential  │ │ Conditional │
        │ Invokes │ │ Invokes  │ │ Invokes     │ │ Invokes      │
        └──────┬──┘ └──────────┘ └─────────────┘ └──────────────┘
               │
       ┌───────┴────────────────────────────────────────┬──────────┐
       │                                                │          │
       ↓                                                ↓          ↓
┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌────────┐
│   Tool 1    │ │   Tool 2     │ │   Tool 3     │ │ Tool 4   │ │Tool 5-6│
│  Supplier   │ │ RFP          │ │ Email        │ │Proposal  │ │Score+  │
│  Lookup     │ │ Generator    │ │ Dispatch     │ │ Fetch    │ │Rec     │
└─────────────┘ └──────────────┘ └──────────────┘ └──────────┘ └────────┘
       │              │                 │              │           │
       └──────────────┼─────────────────┼──────────────┼───────────┘
                      │
       ┌──────────────┴──────────────────┐
       │                                 │
       ↓                                 ↓
┌──────────────────────┐      ┌──────────────────────┐
│   DynamoDB Tables    │      │    S3 Bucket         │
│                      │      │                      │
│ • rfp-suppliers      │      │ • rfp-documents      │
│ • rfp-requests       │      │ • RFP docs           │
│ • rfp-proposals      │      │ • Signed URLs        │
│ • rfp-scores         │      │                      │
│ • agentcore-memory   │      │                      │
└──────────────────────┘      └──────────────────────┘
```

---

## Phase 1: API Gateway Setup

### Step 1: Create HTTP API Gateway

```bash
# Create API Gateway
aws apigateway create-rest-api \
    --name rfp-agent-api \
    --description "RFP Agent Orchestrator API" \
    --region us-east-1

# Get API ID
API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='rfp-agent-api'].id" \
    --output text \
    --region us-east-1)

echo "API Gateway ID: $API_ID"
```

### Step 2: Create Resource & Method

```bash
# Get root resource
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --query "items[?path=='/'].id" \
    --output text \
    --region us-east-1)

# Create /process-rfp resource
RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_RESOURCE_ID \
    --path-part process-rfp \
    --region us-east-1 \
    --query 'id' \
    --output text)

# Create POST method
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --authorization-type AWS_IAM \
    --region us-east-1

# Link to Lambda
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:$ACCOUNT_ID:function:rfp-agentcore-orchestrator/invocations" \
    --region us-east-1
```

### Step 3: Deploy API

```bash
# Create deployment
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region us-east-1

# Get endpoint
echo "API Endpoint: https://$API_ID.execute-api.us-east-1.amazonaws.com/prod/process-rfp"
```

---

## Phase 2: Observability Setup

### Step 1: Enable X-Ray Tracing

**Update Lambda Configuration:**
```bash
aws lambda update-function-configuration \
    --function-name rfp-agentcore-orchestrator \
    --tracing-config Mode=Active \
    --region us-east-1
```

**X-Ray sampling rule:**
```bash
aws xray create-sampling-rule \
    --cli-input-json file://xray-sampling.json \
    --region us-east-1
```

**File: xray-sampling.json**
```json
{
  "SamplingRule": {
    "ruleName": "rfp-agent-sampling",
    "priority": 1000,
    "version": 1,
    "reservoirSize": 1,
    "fixedRate": 0.1,
    "urlPath": "*",
    "host": "*",
    "HTTPMethod": "*",
    "resourceARN": "arn:aws:xray:us-east-1:*:*",
    "serviceName": "rfp-agent",
    "serviceType": "*"
  }
}
```

### Step 2: CloudWatch Logs Configuration

**Update Lambda IAM Role:**
```bash
aws iam put-role-policy \
    --role-name rfp-agent-lambda-role \
    --policy-name CloudWatchLogsPolicy \
    --policy-document file://cloudwatch-policy.json
```

**File: cloudwatch-policy.json**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/aws/lambda/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 3: CloudWatch Metrics & Dashboards

**Custom Metrics to Track:**
- Agent execution time
- Tool invocation count
- Tool success/failure rate
- Memory usage
- DynamoDB read/write capacity
- Approval decision distribution

**Create Dashboard:**
```bash
aws cloudwatch put-dashboard \
    --dashboard-name rfp-agent-dashboard \
    --dashboard-body file://dashboard.json
```

---

## Phase 3: Memory & Conversation State

### Current Memory Implementation

**Table: agentcore-memory-v2**
```
Primary Key: session_id
Attributes:
  • session_id: String (UUID)
  • timestamp: String (ISO8601)
  • conversation_history: Map (list of messages)
  • current_rfp_context: Map (RFP data)
  • workflow_state: String (step_number)
  • user_id: String (from Cognito)
```

### Memory Operations

**1. Initialize Session:**
```python
def start_session(user_id: str, requirement: str) -> str:
    session_id = str(uuid.uuid4())
    memory_table.put_item(Item={
        "session_id": session_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "conversation_history": [],
        "current_rfp_context": {
            "requirement": requirement,
            "suppliers_found": [],
            "rfp_id": None
        },
        "workflow_state": "INITIALIZED",
        "ttl": int(time.time()) + (24 * 3600)  # 24hr expiry
    })
    return session_id
```

**2. Update Conversation:**
```python
def add_to_history(session_id: str, role: str, content: str):
    memory_table.update_item(
        Key={"session_id": session_id},
        UpdateExpression="SET conversation_history = list_append(conversation_history, :msg)",
        ExpressionAttributeValues={
            ":msg": [{
                "role": role,  # "user" or "assistant"
                "content": content,
                "timestamp": datetime.now().isoformat()
            }]
        }
    )
```

**3. Retrieve Session:**
```python
def get_session_context(session_id: str) -> Dict:
    response = memory_table.get_item(Key={"session_id": session_id})
    return response.get("Item", {})
```

---

## Phase 4: Tool Integration as Lambda Functions

### Current Tool Architecture

Each tool is already a separate Lambda function:
- `rfp-supplier-lookup`
- `rfp-rfp-generator`
- `rfp-email-dispatch`
- `rfp-proposal-fetch`
- `rfp-scoring`
- `rfp-recommendation`

### Orchestrator Tool Registration

**File: RFP-main/agentcore_orchestrator.py**
```python
from strands import Agent, tool
import boto3

# Define tool signatures for Strands Agent
@tool
def supplier_lookup(category: str, requirement: str) -> dict:
    """
    Find qualified suppliers for a procurement category.
    
    Args:
        category: Supplier category (e.g., 'sensors', 'brake_systems')
        requirement: Detailed requirement description
    
    Returns:
        Dictionary with supplier list and ratings
    """
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    response = lambda_client.invoke(
        FunctionName='rfp-supplier-lookup',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "body": json.dumps({"category": category, "requirement": requirement})
        })
    )
    return json.loads(response['Payload'].read())

# Similar for other 5 tools...

# Register with Agent
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
```

---

## Phase 5: Request/Response Flow

### Client Request

```json
POST /process-rfp HTTP/1.1
Authorization: Bearer cognito_token

{
  "body": {
    "cognito_token": "eyJhbGc...",
    "message": "Create RFP for sensors with budget $50000",
    "session_id": "optional-existing-session-id"
  }
}
```

### Orchestrator Processing

```
1. Extract cognito_token → Get user_id from Cognito
2. If session_id exists → Load conversation history
3. If new → Initialize new session with TTL
4. Pass requirement to Amazon Nova Pro (Bedrock)
5. Agent decides which tools to invoke
6. Invoke tools in parallel/sequence as needed
7. Update memory after each step
8. Return final result
```

### Agent Response

```json
{
  "statusCode": 200,
  "body": {
    "workflow_status": "SUCCESS",
    "rfp_id": "RFP-20260617-XXXXX",
    "session_id": "session-uuid",
    "workflow_id": "workflow-uuid",
    "user_email": "user@example.com",
    "requirement": "Create RFP for sensors",
    "timestamp": "2026-06-17T11:00:00.000000",
    "agent_output": "Full narrative of 8-step workflow...",
    "tools_invoked": [
      {"tool": "supplier_lookup", "status": "success"},
      {"tool": "rfp_generator", "status": "success"},
      ...
    ],
    "approval_decision": {
      "status": "auto_approved",
      "reason": "Cost within budget",
      "amount": "$8500"
    }
  }
}
```

---

## Phase 6: Monitoring & Alerting

### CloudWatch Alarms

**1. Lambda Execution Errors:**
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name rfp-agent-errors \
    --alarm-description "Alert on Lambda errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold
```

**2. Tool Failure Rate:**
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name rfp-tool-failures \
    --alarm-description "Alert when tools fail" \
    --metric-name ToolFailureRate \
    --namespace rfp-agent \
    --statistic Average \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold
```

**3. DynamoDB Throttling:**
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name rfp-dynamodb-throttle \
    --alarm-description "Alert on DynamoDB throttling" \
    --metric-name UserErrors \
    --namespace AWS/DynamoDB \
    --statistic Sum \
    --period 60 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold
```

### X-Ray Service Map

Automatically shows:
- Orchestrator Lambda call flow
- Tool Lambda invocations
- DynamoDB query patterns
- S3 operations
- Bedrock API calls
- Error traces

---

## Phase 7: Performance Optimization

### Lambda Configuration

```bash
aws lambda update-function-configuration \
    --function-name rfp-agentcore-orchestrator \
    --timeout 300 \
    --memory-size 512 \
    --ephemeral-storage Size=10240 \
    --environment Variables="{REGION=us-east-1,LOG_LEVEL=INFO}" \
    --region us-east-1
```

### Reserved Concurrency

```bash
aws lambda put-function-concurrency \
    --function-name rfp-agentcore-orchestrator \
    --reserved-concurrent-executions 10 \
    --region us-east-1
```

### DynamoDB Optimization

**Add Global Secondary Index for fast lookups:**
```bash
aws dynamodb update-table \
    --table-name agentcore-memory-v2 \
    --global-secondary-index-updates \
    '[{
        "Create": {
            "IndexName": "user-id-timestamp-index",
            "Keys": [
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"}
            ],
            "Projection": {"ProjectionType": "ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
        }
    }]' \
    --region us-east-1
```

---

## Phase 8: Security Hardening

### Cognito Integration

**Update API Gateway with Cognito Authorizer:**
```bash
aws apigateway create-authorizer \
    --rest-api-id $API_ID \
    --name rfp-cognito-auth \
    --type COGNITO_USER_POOLS \
    --provider-arns "arn:aws:cognito-idp:us-east-1:$ACCOUNT_ID:userpool/us-east-1_XXXXXXXXX" \
    --identity-source "method.request.header.Authorization" \
    --region us-east-1
```

**Update POST method with authorizer:**
```bash
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --authorization-type CUSTOM \
    --authorizer-id $AUTHORIZER_ID \
    --region us-east-1
```

### IAM Role Least Privilege

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-east-1:*:foundation-model/amazon.nova-pro-v1:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/rfp-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-east-1:*:function:rfp-*"
    }
  ]
}
```

---

## Deployment Checklist

- [ ] Phase 1: API Gateway endpoint created
- [ ] Phase 2: X-Ray tracing enabled
- [ ] Phase 3: CloudWatch logs configured
- [ ] Phase 4: Memory table verified
- [ ] Phase 5: Tool invocation tested
- [ ] Phase 6: Monitoring & alerts set up
- [ ] Phase 7: Performance optimized
- [ ] Phase 8: Security hardened
- [ ] End-to-end test via API Gateway
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Pushed to GitHub

---

## Testing

### Test 1: Direct Lambda Invocation
```bash
aws lambda invoke \
    --function-name rfp-agentcore-orchestrator \
    --payload '{"body":"{\"cognito_token\":\"test\",\"message\":\"Create RFP\"}"}' \
    --region us-east-1 \
    response.json
```

### Test 2: Via API Gateway
```bash
curl -X POST https://$API_ID.execute-api.us-east-1.amazonaws.com/prod/process-rfp \
    -H "Authorization: Bearer $COGNITO_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "Create RFP for sensors"}'
```

### Test 3: Multi-turn Conversation
```bash
# First turn
curl ... -d '{"message": "Create RFP for sensors"}'
# Returns: session_id

# Second turn with same session
curl ... -d '{"session_id": "...", "message": "Add budget constraint $50K"}'
```

---

## Success Metrics

- ✅ API Gateway endpoint responds within 30s
- ✅ Agent processes 8 workflow steps
- ✅ Memory persists conversation history
- ✅ All 6 tools invoked successfully
- ✅ Observability captures all requests
- ✅ No errors in CloudWatch logs
- ✅ X-Ray traces show complete flow
- ✅ DynamoDB operations efficient

---

## Files to Create/Update

1. **Infrastructure Code**
   - `api-gateway-setup.sh` - API Gateway configuration
   - `observability-setup.sh` - X-Ray + CloudWatch
   - `memory-table-config.sh` - DynamoDB optimization

2. **Application Code**
   - `RFP-main/agentcore_orchestrator.py` - Update tool registration
   - `RFP-main/agentcore_memory.py` - Enhance memory operations

3. **Documentation**
   - `AGENT_RUNTIME_DEPLOYMENT.md` - This document
   - `API_GATEWAY_GUIDE.md` - API usage guide
   - `MONITORING_GUIDE.md` - Observability guide

