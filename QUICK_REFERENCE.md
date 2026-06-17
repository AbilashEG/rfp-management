# AgentCore Deployment - Quick Reference

Keep this handy while executing the deployment.

---

## Commands Cheat Sheet

### Installation & Setup

```bash
# Install AgentCore CLI (do this once)
npm install -g @aws/agentcore

# Verify installation
agentcore --version

# Configure AWS credentials (do this once)
aws configure

# Verify AWS access
aws sts get-caller-identity
```

### Local Development

```bash
# Start local dev server (keeps running)
agentcore dev

# In a NEW terminal - invoke agent locally
agentcore invoke '{"message": "We need 500 brake sensors by Sept 2026."}'

# Stop local dev server
# Press Ctrl+C in the terminal where agentcore dev is running
```

### AWS Deployment

```bash
# Deploy to AWS AgentCore Runtime
agentcore deploy

# Check deployment status
agentcore status

# Get agent details
agentcore info

# Get agent endpoint URL
agentcore get endpoint
```

### Monitoring & Logs

```bash
# View agent logs (local dev)
agentcore logs --follow

# View specific tool logs
agentcore logs --tool supplier_lookup_tool

# View X-Ray traces
agentcore traces

# View metrics
agentcore metrics
```

### Advanced Commands

```bash
# Add additional pillars
agentcore add memory
agentcore add identity
agentcore add evaluator
agentcore add api-gateway

# List all tools
agentcore list tools

# Test specific tool
agentcore invoke-tool supplier_lookup_tool '{"category": "sensors"}'

# Redeploy after changes
agentcore deploy

# Rollback to previous version
agentcore rollback

# Delete deployment (cleanup)
agentcore delete
```

---

## AWS Console Navigation

### Check Lambda Functions
```
AWS Console → Lambda → Functions
Filter: Region = us-east-1
Look for: rfp-*-v2 functions (7 total)
All should show: Package Type = Container
```

### Check DynamoDB Tables
```
AWS Console → DynamoDB → Tables
Filter: Region = us-east-1
Tables should exist:
- agentcore-memory-v2
- rfp-suppliers
- rfp-requests
- rfp-proposals
- rfp-scores
- rfp-recommendations
```

### Check Agent in AgentCore
```
AWS Console → Bedrock → Agents
Filter: Region = us-east-1
Agent name: rfp-supplier-agent
Status: ACTIVE
Tools Registered: 6/6
```

### Check Agent Logs
```
AWS Console → CloudWatch → Log Groups
Log Group: /agentcore/rfp-supplier-agent
Should see recent logs from agent executions
```

### Check Agent Traces
```
AWS Console → X-Ray → Service Map
Should show traces of agent calling 6 Lambda tools
```

### Check Cognito User Pool
```
AWS Console → Cognito → User Pools
Pool name: rfp-supplier-agent-pool (or similar)
Status: ACTIVE
```

---

## Files You Need

```
agentcore.yaml                         ← Agent configuration (READ THIS FIRST)
AGENTCORE_DEPLOYMENT.md                ← Step-by-step deployment guide
RESOURCE_MAPPING.md                    ← Resource mapping & architecture
EXECUTION_CHECKLIST.md                 ← Detailed checkbox list
QUICK_REFERENCE.md                     ← This file

RFP-main/
├── agentcore_orchestrator.py          ← Agent entry point
├── agentcore_memory.py                ← Memory handler
├── config.py                          ← Configuration
├── requirements.txt                   ← Dependencies
└── lambda/
    ├── supplier_lookup_lambda.py      ← Tool 1
    ├── rfp_generator_lambda.py        ← Tool 2
    ├── email_dispatch_lambda.py       ← Tool 3
    ├── proposal_fetch_lambda.py       ← Tool 4
    ├── scoring_lambda.py              ← Tool 5
    └── recommendation_lambda.py       ← Tool 6

Dockerfile                             ← Container image definition
README.md                              ← Project overview
```

---

## Execution Flow (7 Phases)

```
PHASE 1: SETUP (30 min)
├─ Install: npm install -g @aws/agentcore
├─ Configure: aws configure
└─ Verify: agentcore --version

PHASE 2: VERIFY (15 min)
├─ AWS Resources Exist
└─ Project Structure OK

PHASE 3: LOCAL TEST (20 min)
├─ agentcore dev (start server)
├─ agentcore invoke (test in new terminal)
└─ Ctrl+C to stop

⚠️ CRITICAL: If local test fails, AWS deployment will also fail

PHASE 4: DEPLOY (10-15 min)
├─ agentcore deploy
└─ Wait 5-10 minutes (do not interrupt)

PHASE 5: VERIFY (15 min)
├─ Check Agent in AWS Console
├─ Check 6 Tools Registered
├─ Check CloudWatch Logs
├─ Check X-Ray Traces
├─ Check DynamoDB Memory
└─ Check Cognito Identity

PHASE 6: TEST (10 min)
├─ Test in AWS Console
├─ Verify all tools called
├─ Verify response correct
└─ All pillars working

PHASE 7: API GATEWAY (5 min - optional)
├─ agentcore add api-gateway
├─ agentcore deploy
└─ Test via curl
```

---

## Success Criteria Checklist

✅ **Phase 1 Success**: CLI installed, AWS credentials configured
- `agentcore --version` returns version
- `aws sts get-caller-identity` returns Account ID

✅ **Phase 2 Success**: All resources exist
- 7 Lambda functions in us-east-1
- 6 DynamoDB tables exist
- S3 bucket exists
- Project files complete

✅ **Phase 3 Success**: Local test passes
- `agentcore dev` starts without errors
- `agentcore invoke` returns status: SUCCESS
- Response includes recommendations
- New items appear in DynamoDB

✅ **Phase 4 Success**: AWS deployment completes
- `agentcore deploy` finishes without errors
- Output shows "Deployment complete"
- Agent ID captured
- Runtime endpoint captured

✅ **Phase 5 Success**: All pillars verified
- Agent status: ACTIVE in AWS Console
- 6/6 tools registered
- CloudWatch logs exist
- X-Ray traces exist
- DynamoDB has memory items
- Cognito pool exists

✅ **Phase 6 Success**: End-to-end test passes
- Test request returns SUCCESS
- Response includes recommendations
- Tools show in X-Ray traces
- New data in DynamoDB tables
- New RFP in S3 bucket

✅ **Phase 7 Success** (optional): API Gateway works
- Endpoint URL obtained
- curl test returns response

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `agentcore: command not found` | `npm install -g @aws/agentcore` |
| `aws: command not found` | Install AWS CLI v2 |
| `Unable to find credentials` | Run `aws configure` |
| `Port 8000 already in use` | `agentcore dev --port 9000` |
| `Connection to Lambda failed` | Verify Lambda in us-east-1 |
| `DynamoDB table not found` | Create agentcore-memory-v2 |
| `Bedrock model not found` | Verify access to nova-pro in us-east-1 |
| `Deployment timeout` | Wait 15 min (Cognito is slow) |
| `Tools not registered` | Re-run `agentcore deploy` |
| `No logs in CloudWatch` | Wait 5-10 minutes to appear |

---

## Support Resources

**AWS Bedrock AgentCore Docs:**
https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html

**Strands Agents Framework:**
https://github.com/aws-samples/strands-agents-sdk

**Project Repository:**
https://github.com/AbilashEG/rfp-management

**Issue Investigation:**
1. Check CloudWatch logs for error details
2. Check X-Ray traces for tool failures
3. Verify DynamoDB table permissions
4. Verify Lambda function access
5. Contact AWS support if system-level

---

## Cost Estimate

```
Per test deployment (single RFP request):
├─ AgentCore Runtime: ~$0.05
├─ Tool invocations (6): ~$0.01
├─ Memory storage: <$0.01
└─ Observability: <$0.01

Total per test: ~$0.10

Monthly production (100k requests):
├─ AgentCore: ~$25
├─ Tool calls: ~$100
├─ Memory: ~$2
├─ Observability: ~$50
├─ Lambda tools: ~$25
└─ DynamoDB: ~$40

Total monthly: ~$250-400
```

---

## Timeline

```
Setup Phase (Phase 1):        5-10 min
  └─ npm install + aws configure

Verification Phase (Phase 2): 10-15 min
  └─ Click AWS Console, verify resources

Local Test (Phase 3):         15-20 min
  └─ agentcore dev + agentcore invoke

AWS Deployment (Phase 4):     10-15 min
  └─ agentcore deploy (wait 5-10 min)

AWS Verification (Phase 5):   10-15 min
  └─ Check AWS Console

End-to-End Test (Phase 6):    5-10 min
  └─ agentcore invoke in AWS Console

API Gateway (Phase 7):        5 min (optional)
  └─ agentcore add api-gateway

────────────────────────────────────────
Total Time: 60-85 minutes
```

---

## Pre-Deployment Checklist

Before you start:

- [ ] AWS Account access confirmed
- [ ] AWS credentials configured locally
- [ ] Node.js 18+ installed
- [ ] AWS CLI v2 installed
- [ ] 7 Lambda functions deployed to us-east-1
- [ ] 6 DynamoDB tables created and seeded
- [ ] S3 bucket created
- [ ] IAM role has required permissions
- [ ] All files present in project directory
- [ ] 1-2 hours available to complete deployment

---

## Documents to Read In Order

1. **Start here**: `README.md` (project overview)
2. **Architecture**: `RESOURCE_MAPPING.md` (understand the flow)
3. **Step-by-step**: `AGENTCORE_DEPLOYMENT.md` (detailed commands)
4. **Checklist**: `EXECUTION_CHECKLIST.md` (detailed checkbox steps)
5. **Quick ref**: `QUICK_REFERENCE.md` (this file)
6. **Config**: `agentcore.yaml` (verify settings)

---

## Success Video Summary

After all 7 phases:

✅ Agent deployed to AWS AgentCore Runtime
✅ 6 Lambda tools registered as MCP gateway
✅ Memory persisting in DynamoDB (30 day TTL)
✅ Identity enabled via Cognito
✅ Observability visible in CloudWatch + X-Ray
✅ Human approval gates configured
✅ End-to-end RFP workflow tested and working
✅ API Gateway endpoint (optional) ready

**You are ready to put the agent into production.**

