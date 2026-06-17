# 🚀 START HERE - Deploy Agent to AWS AgentCore Runtime

**Current State**: RFP agent in Lambda container  
**Target State**: RFP agent in AWS AgentCore Runtime  
**Time**: ~30 minutes

---

## What is AgentCore Runtime?

AgentCore is AWS's managed runtime for autonomous agents. Instead of running your agent logic IN Lambda, it runs in AgentCore's optimized runtime while Lambda functions serve as MCP tools.

**Key difference**:
- ❌ **Before**: Orchestrator runs in Lambda (`rfp-agentcore-orchestrator`)
- ✅ **After**: Orchestrator runs in AgentCore Runtime; Lambda tools via MCP Gateway

---

## 5-Minute Action Plan

### 1. Install AgentCore CLI

```bash
npm install -g @aws/agentcore
agentcore --version
```

### 2. Test Agent Locally

```bash
cd "c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT"
agentcore dev --config agentcore.yaml
# In another terminal:
agentcore invoke --local '{"message": "We need 500 sensors by Sept 2026"}'
```

Expected: Agent executes all 8 workflow steps

### 3. Deploy to AWS

```bash
agentcore deploy --config agentcore.yaml --region us-east-1
# Wait ~5-10 minutes
```

Expected: Deployment successful, agent active

### 4. Verify in AWS Console

Go to: AWS Bedrock → AgentCore → Agents → rfp-supplier-agent

Check all pillars GREEN ✅:
- Runtime: Active
- Gateway: 6 tools registered
- Memory: Enabled
- Observability: Active
- Policy: Human approval enabled
- Identity: Cognito active

### 5. Get Endpoint & Test

```bash
agentcore describe rfp-supplier-agent
# Copy the Runtime Endpoint
agentcore invoke agent-ID '{"message": "Create RFP for sensors"}'
```

**Done!** Agent is now in AgentCore Runtime.

---

## Detailed 14-Step Guide

For complete step-by-step instructions with troubleshooting, see:
**`AGENTCORE_DEPLOYMENT_STEPS.md`**

Each step includes:
- What to run
- Expected output
- What to check
- How to fix if it fails

---

## Configuration Files

### `agentcore.yaml` 
Production configuration with:
- ✅ Framework: Strands Agents
- ✅ Model: amazon.nova-pro-v1:0
- ✅ Memory: DynamoDB (30-day TTL)
- ✅ Identity: Cognito
- ✅ Observability: X-Ray + CloudWatch
- ✅ Policy: Human approval gates
- ✅ Gateway: 6 MCP tools

No changes needed - ready to use.

---

## Architecture After Deployment

```
Client Request
    ↓
AgentCore Runtime (NEW)
├─ Agent orchestration
├─ Strands SDK execution
├─ LLM calls to Bedrock
└─ Tool calling via MCP Gateway
    ↓
Lambda Functions (Tools)
├─ rfp-supplier-lookup
├─ rfp-generator
├─ email-dispatch
├─ proposal-fetch
├─ scoring
└─ recommendation
    ↓
Backend Services
├─ DynamoDB
└─ S3
    ↓
Observability
├─ CloudWatch
└─ X-Ray
```

---

## Key Constraints

🔒 **MUST DO**:
- [ ] Test locally BEFORE deploying
- [ ] Use us-east-1 region
- [ ] Use amazon.nova-pro-v1:0 model
- [ ] Keep agentcore.yaml in project root
- [ ] Verify all 6 Lambda tools deployed first

🚫 **DO NOT**:
- [ ] Skip Step 6 (local dev test)
- [ ] Deploy without local verification
- [ ] Skip AWS console verification
- [ ] Modify Lambda tool code
- [ ] Run API Gateway setup before AgentCore verified

---

## Success Metrics

✅ **After Deployment You Should See**:
- AgentCore console shows "ACTIVE" status
- All 6 tools listed in Gateway
- X-Ray service map shows agent → tools → backend
- CloudWatch logs: `/agentcore/rfp-supplier-agent`
- Agent responds to requests in < 30 seconds
- All workflow steps execute
- Conversation history persists (memory)

---

## Troubleshooting Quick Links

| Problem | Solution |
|---------|----------|
| `agentcore: command not found` | Run `npm install -g @aws/agentcore` |
| Local test fails | Check Lambda functions deployed, DynamoDB tables exist |
| Deploy timeout | Check AWS credentials, internet connection |
| Tools not found | Verify Lambda names in agentcore.yaml match actual functions |
| Slow response | Increase Lambda memory, check tool timeouts |

For detailed troubleshooting, see Step 14 in `AGENTCORE_DEPLOYMENT_STEPS.md`

---

## Files Ready to Use

| File | Purpose |
|------|---------|
| `agentcore.yaml` | ✅ Production config (ready) |
| `AGENTCORE_DEPLOYMENT_STEPS.md` | ✅ Detailed guide (copy steps) |
| `AGENTCORE_DEPLOYMENT.md` | ✅ Architecture reference |

---

## Command Cheat Sheet

```bash
# Install
npm install -g @aws/agentcore

# Test locally
agentcore dev --config agentcore.yaml

# Invoke local
agentcore invoke --local '{"message": "test"}'

# Deploy
agentcore deploy --config agentcore.yaml --region us-east-1

# Test deployed
agentcore invoke agent-ID '{"message": "test"}'

# Describe agent
agentcore describe agent-ID

# View logs
agentcore logs agent-ID --follow

# Validate config
agentcore validate agentcore.yaml
```

---

## Next: After AgentCore is Deployed

Once AgentCore is verified running:

1. **Update API Gateway** (optional)
   - Currently not needed - AgentCore is standalone
   - Can add API Gateway later to expose endpoint

2. **Monitor Performance**
   - CloudWatch dashboard
   - X-Ray service map
   - Custom metrics

3. **Scale & Optimize**
   - Tune agent memory
   - Adjust tool timeouts
   - Load testing

---

## Questions?

**Full documentation**: `AGENTCORE_DEPLOYMENT_STEPS.md` (14 detailed steps)

**Architecture reference**: `AGENTCORE_DEPLOYMENT.md`

**Backend integration**: `BACKEND_INTEGRATION_COMPLETE.md`

**Container deployment**: `CONTAINER_DEPLOYMENT.md`

---

## One-Command Quick Start

After installing Node.js and npm:

```bash
cd "c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT" && \
npm install -g @aws/agentcore && \
agentcore --version && \
echo "✅ Ready! Run: agentcore dev --config agentcore.yaml"
```

Then follow Step 6-14 in `AGENTCORE_DEPLOYMENT_STEPS.md`

---

## GitHub Repository

All files committed to: https://github.com/AbilashEG/rfp-management

Latest commit: `666a1a7` - AgentCore deployment files

---

## Ready?

👉 **Next**: Open `AGENTCORE_DEPLOYMENT_STEPS.md` and follow each step

```bash
agentcore dev --config agentcore.yaml
# Then in new terminal:
agentcore invoke --local '{"message": "Create RFP for sensors"}'
```

Let's deploy! 🚀

