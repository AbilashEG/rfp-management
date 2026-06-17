# AgentCore Runtime Deployment Guide

## What This Guide Covers

This guide walks you through deploying the RFP agent **from Lambda to AWS AgentCore Runtime**.

**Before you start**: The agent code and Lambda tools are already built and tested. This guide focuses on:
1. Installing AgentCore CLI
2. Creating AgentCore project structure
3. Registering the 6 Lambda tools as MCP gateway
4. Enabling Memory, Identity, Observability, and Policy
5. Deploying to AWS AgentCore Runtime
6. Testing end-to-end

---

## Architecture After Deployment

```
User Request
    ↓
AgentCore Runtime (Strands Agent running here)
    ↓
MCP Gateway (routes tool calls)
    ↓
6 Lambda Tools (run in parallel)
    ├─ supplier_lookup_lambda
    ├─ rfp_generator_lambda
    ├─ email_dispatch_lambda
    ├─ proposal_fetch_lambda
    ├─ scoring_lambda
    └─ recommendation_lambda
    ↓
DynamoDB + S3 (data persistence)

Observability Layer:
├─ CloudWatch Logs (/agentcore/rfp-supplier-agent)
├─ X-Ray Traces (all tool calls)
├─ AgentCore Memory (DynamoDB agentcore-memory-v2)
└─ Cognito Identity (user tracking)
```

---

## Prerequisites

✅ AWS Account with these permissions:
- Lambda (read/invoke)
- DynamoDB (read/write)
- S3 (read/write)
- Bedrock (invoke models)
- IAM (create roles)
- CloudWatch (logs/metrics)
- X-Ray (tracing)
- Cognito (user pools)

✅ 7 Lambda functions already deployed:
- rfp-supplier-lookup-v2
- rfp-rfp-generator-v2
- rfp-email-dispatch-v2
- rfp-proposal-fetch-v2
- rfp-scoring-v2
- rfp-recommendation-v2
- rfp-agent-orchestrator-v2

✅ DynamoDB tables already seeded:
- agentcore-memory-v2 (for agent memory)
- rfp-suppliers
- rfp-requests
- rfp-proposals
- rfp-scores
- rfp-recommendations

✅ S3 bucket ready:
- rfp-documents-quadrasystems-v2

---

## Execution Steps

### STEP 1: Install AgentCore CLI

```bash
npm install -g @aws/agentcore
```

**Verify installation:**
```bash
agentcore --version
```

Expected output: `@aws/agentcore/X.Y.Z`

**Troubleshooting:**
- If `npm` command not found, install Node.js 18+
- If permission denied, use: `sudo npm install -g @aws/agentcore`

---

### STEP 2: Configure AWS Credentials

Ensure your AWS credentials are configured locally:

```bash
aws configure
```

When prompted:
- AWS Access Key ID: [your access key]
- AWS Secret Access Key: [your secret key]
- Default region: us-east-1
- Default output format: json

**Verify access:**
```bash
aws sts get-caller-identity
```

This should return your AWS Account ID.

---

### STEP 3: Verify Project Structure

The project should look like this:

```
RFP MANAGEMENT/
├── agentcore.yaml                    ← Agent configuration
├── RFP-main/
│   ├── agentcore_orchestrator.py    ← Agent entry point
│   ├── agentcore_memory.py
│   ├── config.py
│   ├── requirements.txt
│   └── lambda/
│       ├── supplier_lookup_lambda.py
│       ├── rfp_generator_lambda.py
│       ├── email_dispatch_lambda.py
│       ├── proposal_fetch_lambda.py
│       ├── scoring_lambda.py
│       └── recommendation_lambda.py
├── Dockerfile
└── .github/
    └── workflows/
        └── deploy-to-ecr.yml
```

**Verify all files exist:**
```bash
ls -la agentcore.yaml
ls -la RFP-main/agentcore_orchestrator.py
ls -la RFP-main/lambda/
```

---

### STEP 4: Start Local AgentCore Dev Server

This tests the agent locally before deploying to AWS.

```bash
agentcore dev
```

**Expected output:**
```
Starting AgentCore Development Server...
✓ Agent loaded: rfp-supplier-agent
✓ Framework: Strands
✓ Model: amazon.nova-pro-v1:0
✓ Memory: enabled (agentcore-memory-v2)
✓ Gateway: 6 MCP tools registered
✓ Observability: enabled
Dev server running at: http://localhost:8000
```

**Test the agent locally:**
```bash
agentcore invoke '{
  "message": "We need 500 brake sensors by Sept 2026. Category: sensors. Quantity: 500. Deadline: 2026-09-30."
}'
```

**Expected response:**
- Agent processes request through all 8 workflow steps
- Calls all 6 tools in sequence
- Returns top 2 supplier recommendations
- Session stored in agentcore-memory-v2

**Troubleshooting:**
- If tools fail, check DynamoDB tables are seeded
- If memory fails, check agentcore-memory-v2 exists
- If model fails, check Bedrock access in us-east-1

**CRITICAL**: Do NOT skip this step. If local test fails, the AWS deployment will also fail.

---

### STEP 5: Deploy Agent to AWS AgentCore Runtime

Once local testing passes, deploy to AWS:

```bash
agentcore deploy
```

**Expected output:**
```
🚀 Deploying rfp-supplier-agent to AWS...

[1/5] Packaging agent code...                    ✓
[2/5] Creating AgentCore Runtime...              ✓
[3/5] Registering MCP tools to gateway...        ✓
[4/5] Configuring Memory, Identity, Policy...    ✓
[5/5] Initializing Observability...              ✓

✓ Deployment complete in 7m 45s

Agent Details:
├─ Agent ID: arn:aws:bedrock:us-east-1:ACCOUNT:agent/rfp-supplier-agent
├─ Runtime Endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/agent
├─ Memory: agentcore-memory-v2 (30-day TTL)
├─ Tools Registered: 6/6
├─ Observability: CloudWatch + X-Ray enabled
└─ Identity: Cognito enabled

Next Steps:
1. Verify all pillars (Step 6)
2. Test in AWS Console (Step 7)
3. Setup API Gateway (Step 8)
```

**WAIT**: Deployment takes 5-10 minutes. Do not proceed until you see "Deployment complete".

---

### STEP 6: Verify All Pillars in AWS Console

After deployment, verify each component is active.

**Open AWS Bedrock Console:**
- Region: us-east-1
- Service: Bedrock → Agents

**Verify Runtime Pillar:**
- Click on agent: `rfp-supplier-agent`
- Status: ACTIVE
- Framework: Strands
- Model: amazon.nova-pro-v1:0

**Verify Gateway Pillar (MCP Tools):**
- Scroll to "Tools" section
- Should see all 6 tools:
  - ✓ supplier_lookup_tool
  - ✓ rfp_generator_tool
  - ✓ email_dispatch_tool
  - ✓ proposal_fetch_tool
  - ✓ scoring_tool
  - ✓ recommendation_tool

**Verify Memory Pillar:**
- Open DynamoDB Console
- Table: `agentcore-memory-v2`
- Should see items being created as agent runs

**Verify Identity Pillar:**
- Open Cognito Console
- User Pool: `rfp-supplier-agent-pool` (auto-created)
- Users can log in to invoke agent

**Verify Observability Pillar:**
- Open CloudWatch Console
- Log Group: `/agentcore/rfp-supplier-agent`
- Should see agent logs

**Verify Policy Pillar:**
- In agent settings, check "Human Approval"
- Status: ENABLED
- Trigger: approval_required=true

---

### STEP 7: Test Agent in AWS Console

**In AWS Bedrock Console:**

Click "Test" or "Invoke" button.

**Send test request:**
```json
{
  "message": "We need 500 brake sensors by Sept 2026. Category: sensors. Quantity: 500. Deadline: 2026-09-30."
}
```

**Expected flow:**
1. Agent receives request
2. Invokes supplier_lookup tool → returns 5 suppliers
3. Invokes rfp_generator tool → creates RFP in S3
4. Invokes email_dispatch tool → sends emails
5. Waits for proposals in DynamoDB
6. Invokes proposal_fetch tool → reads proposals
7. Invokes scoring tool → scores each proposal
8. Invokes recommendation tool → returns top 2

**Response example:**
```json
{
  "status": "SUCCESS",
  "rfp_id": "RFP-20260617-E999BE46",
  "suppliers_found": 5,
  "recommendations": [
    {
      "supplier": "TechSupply Corp",
      "score": 9.2,
      "reason": "Best price + on-time delivery record"
    },
    {
      "supplier": "Global Components Inc",
      "score": 8.9,
      "reason": "Excellent quality + bulk discount"
    }
  ],
  "timestamp": "2026-06-17T14:32:00Z"
}
```

---

### STEP 8: Test via API Gateway (Optional)

To expose the agent as a REST API:

```bash
agentcore add api-gateway
agentcore deploy
```

This creates an HTTPS endpoint pointing to your AgentCore Runtime.

**Get the endpoint URL:**
```bash
agentcore get endpoint
```

**Test via curl:**
```bash
curl -X POST https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/agent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "We need 500 brake sensors by Sept 2026."
  }'
```

---

## Monitoring & Troubleshooting

### View Agent Logs

```bash
agentcore logs --follow
```

Or in AWS CloudWatch:
- Log Group: `/agentcore/rfp-supplier-agent`

### View Tool Execution Traces

```bash
agentcore traces --tool supplier_lookup_tool
```

Or in AWS X-Ray Console:
- Service Map shows MCP gateway → 6 Lambda tools

### Common Issues

**Issue**: Agent deployment times out after 10 minutes
- **Cause**: Cognito user pool creation slow
- **Fix**: Wait another 5 minutes, then check Cognito console

**Issue**: Tools not appearing in gateway
- **Cause**: Lambda functions not in same region (us-east-1)
- **Fix**: Verify all Lambdas deployed to us-east-1

**Issue**: Memory not persisting between sessions
- **Cause**: agentcore-memory-v2 table not created
- **Fix**: Manually create table with TTL=30 days

**Issue**: Human approval gate not working
- **Cause**: SQS queue not configured
- **Fix**: Run `agentcore add policy` and redeploy

---

## Next Steps

✅ Agent deployed to AgentCore Runtime
✅ All 6 Lambda tools registered as MCP gateway
✅ Memory, Identity, Observability, Policy all enabled
✅ End-to-end RFP workflow tested

**What's next?**
1. Create production user pool in Cognito
2. Add custom authentication logic
3. Set up approval workflow for RFP generation
4. Configure cost monitoring in CloudWatch
5. Create CI/CD pipeline for agent updates

---

## Support

For issues or questions:
- Check AWS Bedrock documentation: https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
- Check AgentCore CLI help: `agentcore --help`
- Check agent logs: `agentcore logs --follow`
