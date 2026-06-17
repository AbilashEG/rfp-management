# AgentCore Runtime Deployment - Step by Step

**Current State**: RFP agent running in Lambda container (7 functions)  
**Target State**: RFP agent running in AWS AgentCore Runtime  
**Duration**: ~30 minutes

---

## Prerequisites

- [ ] AWS CLI configured (us-east-1)
- [ ] Node.js 18+ installed
- [ ] AgentCore CLI available
- [ ] 7 Lambda functions deployed as containers
- [ ] DynamoDB tables seeded
- [ ] S3 bucket ready
- [ ] Bedrock model access: amazon.nova-pro-v1:0

---

## STEP 1: Install AgentCore CLI

### On Windows

```bash
npm install -g @aws/agentcore
```

### Verify Installation

```bash
agentcore --version
```

Expected output:
```
AgentCore CLI version 1.x.x
```

### If npm not found

Install Node.js from: https://nodejs.org/
- Download LTS version
- Run installer
- Restart terminal
- Try npm again

---

## STEP 2: Navigate to Project Root

```bash
cd "c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT"
```

Verify you're in the right location:
```bash
ls -la | grep -E "(RFP-main|agentcore|lambda)"
```

Expected files to see:
- RFP-main/ (directory)
- agentcore.yaml (file we created)
- setup-*.sh scripts

---

## STEP 3: Create AgentCore Project Structure

Option A: Use agentcore command (creates scaffolding)
```bash
agentcore create --name rfp-supplier-agent --framework strands --language python
```

Option B: Manual project setup
Create these directories:
```bash
mkdir -p agentcore-project/tools
mkdir -p agentcore-project/config
mkdir -p agentcore-project/handlers
```

Copy agentcore.yaml to agentcore-project/:
```bash
cp agentcore.yaml agentcore-project/
```

---

## STEP 4: Verify agentcore.yaml Configuration

```bash
cat agentcore.yaml
```

Verify these sections exist:
- ✅ name: rfp-supplier-agent
- ✅ runtime: framework=strands, model=amazon.nova-pro-v1:0
- ✅ memory: enabled=true, ttl_days=30
- ✅ identity: provider=cognito
- ✅ observability: enabled=true
- ✅ policy: human_approval enabled
- ✅ gateway: mcp tools registered (6 tools)

If missing any section, add it from STEP 3 template.

---

## STEP 5: Test Configuration Syntax

```bash
agentcore validate agentcore.yaml
```

Expected output:
```
✓ Configuration valid
✓ All 6 tools registered
✓ Model access verified (amazon.nova-pro-v1:0)
✓ Region configured (us-east-1)
```

If errors appear, fix according to error message and re-validate.

---

## STEP 6: Start Local AgentCore Dev Server

### Start the server

```bash
agentcore dev --config agentcore.yaml
```

Expected output:
```
[INFO] Starting AgentCore Dev Server
[INFO] Framework: Strands Agents
[INFO] Model: amazon.nova-pro-v1:0
[INFO] Memory: DynamoDB agentcore-memory-v2
[INFO] Tools: 6 registered
[INFO] Ready on http://localhost:8080
```

### Keep terminal open

Leave this running in one terminal. Open a **NEW terminal** for next step.

---

## STEP 7: Test Agent Locally

In a **new terminal**:

```bash
cd "c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT"

agentcore invoke --local '{"message": "We need 500 brake sensors by September 2026"}'
```

Expected flow:
```
[Step 1] Parsing requirement: brake sensors, qty 500, deadline 2026-09-30
[Step 2] Invoking supplier_lookup_tool...
  ✓ Found 3 suppliers
[Step 3] Invoking rfp_generator_tool...
  ✓ RFP created: RFP-20260617-XXXXX
[Step 4] Invoking email_dispatch_tool...
  ✓ Emails sent to 3 suppliers
[Step 5] Invoking proposal_fetch_tool...
  ✓ 3 proposals fetched
[Step 6] Invoking scoring_tool...
  ✓ Proposals scored
[Step 7] Invoking recommendation_tool...
  ✓ Top 2 recommendations generated
[Step 8] Approval decision...
  ✓ Auto-approved (cost < $10K threshold)

Result: SUCCESS
Top Recommendation: SupplierA (Score: 92/100)
Approval: Auto-approved
```

### If test succeeds ✅

Great! Your agent works locally in AgentCore Runtime emulation.

### If test fails ❌

Check error message and:
1. Verify agentcore.yaml tool references match Lambda names
2. Verify Lambda functions are deployed
3. Check DynamoDB tables exist
4. Review CloudWatch logs: `/aws/lambda/rfp-*`

---

## STEP 8: Deploy to AWS AgentCore Runtime

### Stop local dev server

In the terminal running `agentcore dev`, press `Ctrl+C` to stop.

### Deploy to AWS

```bash
agentcore deploy --config agentcore.yaml --region us-east-1
```

This automatically:
- [ ] Packages agent code
- [ ] Creates AgentCore Runtime instance on AWS
- [ ] Registers 6 MCP tools to AgentCore Gateway
- [ ] Enables Memory with 30-day TTL
- [ ] Enables Observability to CloudWatch
- [ ] Enables Identity via Cognito
- [ ] Enables Policy human approval gate

**Wait for deployment to complete** (~5-10 minutes)

### Deployment Output

Expected output:
```
[INFO] Packaging agent code...
[INFO] Creating AgentCore Runtime...
[INFO] Registering MCP tools...
[INFO] Configuring memory (DynamoDB)...
[INFO] Enabling observability...
[INFO] Enabling identity (Cognito)...
[INFO] Enabling policy gates...

✓ Deployment Complete!

Agent Name: rfp-supplier-agent
Agent ID: agent-20260617-abc123def456
Runtime Endpoint: https://agentcore.us-east-1.amazonaws.com/agents/rfp-supplier-agent
MCP Gateway Status: ✓ 6 tools registered
Memory Status: ✓ Enabled (30-day TTL)
Observability Status: ✓ CloudWatch integration active
Identity Status: ✓ Cognito enabled
Policy Status: ✓ Human approval enabled
```

**Save these values**:
- Agent ID: `agent-20260617-abc123def456`
- Runtime Endpoint: `https://agentcore.us-east-1.amazonaws.com/agents/rfp-supplier-agent`

---

## STEP 9: Verify AgentCore Deployment

### Test deployed agent

```bash
agentcore invoke agent-20260617-abc123def456 '{"message": "We need 500 brake sensors by September 2026"}'
```

Expected: Same successful workflow as local test

### Check AWS Console

1. **Bedrock Console**
   - Go to: https://console.aws.amazon.com/bedrock/
   - Look for: AgentCore → Agents → rfp-supplier-agent
   - Should show: Status = Active ✅

2. **AgentCore Runtime**
   - Check: All pillars show GREEN ✅
     - Runtime: Agent is hosted and responding
     - Gateway: 6 MCP tools registered
     - Memory: Session history persisting
     - Observability: Traces visible in CloudWatch
     - Policy: Approval gate shows in trace
     - Identity: Cognito auth active

3. **CloudWatch**
   - Log Group: `/agentcore/rfp-supplier-agent`
   - Should show: Agent execution logs
   - Should show: Tool invocation logs
   - Should show: Memory operations

4. **X-Ray**
   - Service map should show:
     - AgentCore Runtime
     - 6 MCP tools
     - Lambda functions
     - DynamoDB tables
     - S3 bucket

---

## STEP 10: Add AgentCore Pillars (Optional But Recommended)

### Add Memory Pillar (for conversation history)

```bash
agentcore add memory --agent-id agent-20260617-abc123def456
```

### Add Identity Pillar (for Cognito auth)

```bash
agentcore add identity --agent-id agent-20260617-abc123def456
```

### Add Evaluator Pillar (for output validation)

```bash
agentcore add evaluator --agent-id agent-20260617-abc123def456
```

### Redeploy with all pillars

```bash
agentcore deploy --config agentcore.yaml --region us-east-1 --update
```

---

## STEP 11: Verify All Pillars Active

Run comprehensive test:

```bash
agentcore invoke agent-20260617-abc123def456 \
  '{"message": "Create RFP for 100 industrial pumps. Budget: $40000. Deadline: 2026-08-31"}'
```

Check output contains:
- ✅ Step-by-step workflow execution
- ✅ All 6 tools invoked
- ✅ Session ID in response (memory working)
- ✅ Cognito token processed (identity working)
- ✅ Approval decision with reasoning (policy working)
- ✅ Tool execution trace IDs (observability working)

---

## STEP 12: Get AgentCore Runtime Endpoint

```bash
agentcore describe agent-20260617-abc123def456
```

Output will include:
```
Agent Details:
  Name: rfp-supplier-agent
  ID: agent-20260617-abc123def456
  Runtime Endpoint: https://agentcore.us-east-1.amazonaws.com/agents/rfp-supplier-agent
  Status: ACTIVE
  
Gateway:
  MCP Tools: 6 registered
  Tool Status: All healthy ✓

Memory:
  Table: agentcore-memory-v2
  TTL: 30 days
  Status: Enabled ✓

Observability:
  Log Group: /agentcore/rfp-supplier-agent
  X-Ray: Enabled ✓
  Metrics: Enabled ✓

Identity:
  Provider: Cognito
  Status: Enabled ✓

Policy:
  Human Approval: Enabled ✓
  Threshold: approval_required = true
```

**Copy the Runtime Endpoint URL** - You'll need this next.

---

## STEP 13: Update API Gateway (ONLY AFTER AGENTCORE VERIFIED)

NOW that AgentCore is running, update API Gateway to point to it:

### Update setup-api-gateway.sh

Edit the file and change:
```bash
# OLD (Lambda ARN)
URI="arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_FUNCTION}/invocations"

# NEW (AgentCore Runtime Endpoint)
URI="https://agentcore.us-east-1.amazonaws.com/agents/rfp-supplier-agent"
```

### Create API Gateway pointing to AgentCore

```bash
bash setup-api-gateway.sh us-east-1
```

Now API Gateway will forward requests to AgentCore Runtime instead of Lambda.

---

## STEP 14: Test Complete Flow

```bash
# Get the API Gateway endpoint (from setup-api-gateway.sh output)
API_ENDPOINT="https://XXXXXXXX.execute-api.us-east-1.amazonaws.com/prod/process-rfp"

# Test it
curl -X POST $API_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "message": "Create RFP for 50 electric motors. Budget: $25000"
    }
  }'
```

Expected response:
```json
{
  "statusCode": 200,
  "body": {
    "workflow_status": "SUCCESS",
    "agent_id": "agent-20260617-abc123def456",
    "tools_invoked": 6,
    "recommendation": "Top supplier: SupplierX (Score: 94/100)",
    "approval_status": "auto_approved"
  }
}
```

---

## Deployment Checklist

### Pre-Deployment ✓
- [ ] AWS CLI configured
- [ ] Node.js/npm installed
- [ ] AgentCore CLI installed
- [ ] 7 Lambda functions deployed
- [ ] DynamoDB tables created
- [ ] S3 bucket ready
- [ ] agentcore.yaml created

### Deployment ✓
- [ ] Local dev test passed
- [ ] AgentCore deploy completed
- [ ] All 6 tools registered
- [ ] Agent responding
- [ ] AWS Console shows ACTIVE status

### Post-Deployment ✓
- [ ] All pillars GREEN in console
- [ ] Test agent invocation works
- [ ] CloudWatch logs flowing
- [ ] X-Ray traces captured
- [ ] API Gateway updated (if using)

---

## Troubleshooting

### Error: "Cannot find agentcore command"
```bash
npm install -g @aws/agentcore
agentcore --version
```

### Error: "Tool not found: supplier_lookup_tool"
Check agentcore.yaml:
- Verify tool name matches Lambda function
- Verify Lambda function deployed
- Verify Lambda role has permissions

### Error: "DynamoDB table not found"
```bash
aws dynamodb describe-table --table-name agentcore-memory-v2 --region us-east-1
```

### Error: "Bedrock model access denied"
```bash
aws bedrock list-foundation-models --region us-east-1 | grep amazon.nova-pro
```

### Slow agent response
Check:
1. Lambda function memory (should be 512MB)
2. DynamoDB capacity (on-demand is fine)
3. Tool timeout settings in agentcore.yaml
4. CloudWatch logs for slow steps

---

## Success Criteria

✅ AgentCore Agent deployed and active  
✅ 6 MCP tools registered and healthy  
✅ Memory persisting conversations  
✅ Observability capturing traces  
✅ Policy gates enforcing approvals  
✅ Identity managing Cognito tokens  
✅ Agent responding to requests < 30s  
✅ All workflow steps executing  

---

## Next Steps

1. ✅ **Now**: Agent running in AgentCore Runtime
2. **Next**: Monitor performance in CloudWatch
3. **Then**: Integrate Cognito authentication
4. **Finally**: Production load testing

---

## Key Differences: Lambda vs AgentCore Runtime

| Aspect | Lambda Orchestrator | AgentCore Runtime |
|--------|-------------------|-------------------|
| Host | Lambda container | AWS AgentCore managed runtime |
| Tool Coordination | Direct Lambda invokes | MCP Gateway |
| Memory | Session data in code | Automatic persistence |
| Observability | Manual setup | Built-in X-Ray + CloudWatch |
| Authorization | Lambda IAM | Cognito + Policy gates |
| Scalability | Cold starts possible | Always warm, auto-scaling |
| Cost | Per execution | Per concurrent agent |

---

## Questions?

Refer to:
- **AgentCore Architecture**: AWS Bedrock documentation
- **Strands SDK**: https://github.com/strands-ai/strands-agents
- **MCP Protocol**: https://spec.modelcontextprotocol.io/

