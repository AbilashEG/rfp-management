# 🚀 START HERE - AgentCore Deployment Guide

You have everything you need to deploy the RFP agent to AWS AgentCore Runtime.

This document tells you **exactly what to do** and **in what order**.

---

## ⏱️ Time Investment

- **Total time**: 60-85 minutes
- **Breakdown**:
  - Setup & verify: 25 minutes
  - Local test: 20 minutes *(CRITICAL - do not skip)*
  - AWS deployment: 15 minutes
  - Verification: 25 minutes

---

## 📚 What You Have

The following documents are ready in this folder:

| Document | What It Does | When to Read |
|----------|------------|--------------|
| `README.md` | Project overview | First (2 min) |
| `RESOURCE_MAPPING.md` | Architecture & how everything connects | Second (10 min) |
| `AGENTCORE_DEPLOYMENT.md` | Step-by-step deployment instructions | Third (during deployment) |
| `EXECUTION_CHECKLIST.md` | Detailed checkbox list for each step | Keep nearby during deployment |
| `QUICK_REFERENCE.md` | Commands cheat sheet | Reference while executing |
| `agentcore.yaml` | Agent configuration | Review once |

---

## 🎯 Your Mission

Deploy the RFP agent **FROM Lambda TO AWS AgentCore Runtime** with these 6 pillars:

1. ✅ **Runtime** - Agent runs inside Bedrock AgentCore (not Lambda)
2. ✅ **Memory** - Conversations stored in DynamoDB (30-day TTL)
3. ✅ **Gateway** - 6 Lambda tools registered as MCP
4. ✅ **Identity** - Users authenticate via Cognito
5. ✅ **Observability** - Logs in CloudWatch, traces in X-Ray
6. ✅ **Policy** - Human approval gates enabled

---

## 📋 Step-by-Step Plan

### STEP 1: Understand the Big Picture (5 minutes)

Read these sections **in this order**:

1. Read: `README.md` (full file)
2. Read: `RESOURCE_MAPPING.md` → "After AgentCore Deployment" section
3. Understand: The agent will run inside AWS, not on Lambda

**After this step**, you should understand:
- What the agent does (finds suppliers, generates RFPs, scores proposals)
- Where it runs (AWS Bedrock AgentCore Runtime)
- What the 6 pillars are (Runtime, Memory, Gateway, Identity, Observability, Policy)

---

### STEP 2: Prepare for Deployment (15 minutes)

Follow `AGENTCORE_DEPLOYMENT.md` → "Prerequisites" section:

**Install AgentCore CLI:**
```bash
npm install -g @aws/agentcore
```

**Verify installation:**
```bash
agentcore --version
```

**Configure AWS credentials:**
```bash
aws configure
```

**Verify AWS access:**
```bash
aws sts get-caller-identity
```

**Check all resources exist** (AWS Console):
- [ ] 7 Lambda functions in us-east-1 (all showing Container type)
- [ ] 6 DynamoDB tables (agentcore-memory-v2 + rfp-* tables)
- [ ] S3 bucket (rfp-documents-quadrasystems-v2)

---

### STEP 3: Test Agent Locally (20 minutes)

**⚠️ CRITICAL**: If local test fails, AWS deployment will fail. Do not skip.

Follow `AGENTCORE_DEPLOYMENT.md` → "Local Testing" section:

**Start dev server (Terminal 1):**
```bash
agentcore dev
```

Wait for: `✓ Dev server running at: http://localhost:8000`

**Test agent (Terminal 2 - NEW window):**
```bash
agentcore invoke '{
  "message": "We need 500 brake sensors by Sept 2026. Category: sensors. Quantity: 500. Deadline: 2026-09-30."
}'
```

**Expect:**
- Response status: "SUCCESS"
- Contains: rfp_id, suppliers_found, recommendations array
- DynamoDB shows new session in agentcore-memory-v2

**If test fails:**
- Check `QUICK_REFERENCE.md` for troubleshooting
- Do NOT proceed to AWS deployment

**Stop dev server (Terminal 1):**
```bash
Ctrl+C
```

---

### STEP 4: Deploy to AWS (15 minutes)

Follow `AGENTCORE_DEPLOYMENT.md` → "AWS Deployment" section:

**Deploy (this takes 5-10 minutes):**
```bash
agentcore deploy
```

**DO NOT interrupt this command.** Wait for:
```
✓ Deployment complete in X minutes

Agent Details:
├─ Agent ID: arn:aws:bedrock:...
├─ Runtime Endpoint: https://xxxxx...
├─ Tools Registered: 6/6
└─ Identity: Cognito enabled
```

**Save the endpoint URL** (you will need it later):
```
Endpoint: _________________________________
```

---

### STEP 5: Verify Everything Works (25 minutes)

Follow `EXECUTION_CHECKLIST.md` → "Phase 5: AWS Verification" section:

**In AWS Console, verify each pillar:**

1. **Runtime Pillar** (Bedrock Console)
   - [ ] Agent name: rfp-supplier-agent
   - [ ] Status: ACTIVE
   - [ ] Framework: Strands
   - [ ] Model: amazon.nova-pro-v1:0

2. **Gateway Pillar** (Bedrock Console → Tools section)
   - [ ] All 6 tools registered:
     - [ ] supplier_lookup_tool
     - [ ] rfp_generator_tool
     - [ ] email_dispatch_tool
     - [ ] proposal_fetch_tool
     - [ ] scoring_tool
     - [ ] recommendation_tool

3. **Memory Pillar** (DynamoDB Console)
   - [ ] Table: agentcore-memory-v2
   - [ ] Has items with session data
   - [ ] TTL enabled (30 days)

4. **Identity Pillar** (Cognito Console)
   - [ ] User pool created: rfp-supplier-agent-pool
   - [ ] Status: ACTIVE

5. **Observability Pillar** (CloudWatch Console)
   - [ ] Log group: /agentcore/rfp-supplier-agent
   - [ ] Has recent log entries

6. **X-Ray Traces** (X-Ray Console)
   - [ ] Service map shows agent → 6 Lambda tools
   - [ ] Has recent traces

---

### STEP 6: Test in AWS Console (10 minutes)

Follow `EXECUTION_CHECKLIST.md` → "Phase 6: End-to-End Test" section:

**In Bedrock Console, test the agent:**
```json
{
  "message": "We need 500 brake sensors by Sept 2026."
}
```

**Expect success response with:**
- [ ] status: SUCCESS
- [ ] recommendations: 2 suppliers with scores
- [ ] DynamoDB populated with scores
- [ ] S3 has new RFP document
- [ ] X-Ray shows all 6 tool calls

---

### STEP 7: Optional - Setup API Gateway (5 minutes)

If you want to expose the agent via REST API:

```bash
agentcore add api-gateway
agentcore deploy
```

Get endpoint:
```bash
agentcore get endpoint
```

Test via curl:
```bash
curl -X POST https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "We need 500 brake sensors by Sept 2026."}'
```

---

## ✅ Success Checklist

After all steps, you should have:

- [ ] AgentCore CLI installed
- [ ] AWS credentials configured
- [ ] Local test passed
- [ ] Agent deployed to AWS
- [ ] 6 Lambda tools registered as MCP
- [ ] CloudWatch logs visible
- [ ] X-Ray traces visible
- [ ] DynamoDB memory working
- [ ] Cognito identity working
- [ ] End-to-end test passed
- [ ] API Gateway working (optional)

---

## 🆘 If Something Goes Wrong

**Troubleshooting flow:**

1. Check error message
2. Search `QUICK_REFERENCE.md` → "Common Errors & Fixes"
3. Check CloudWatch logs: `agentcore logs --follow`
4. Check AWS Console for specific service errors
5. Retry the failed step

**Common issues:**

| Issue | Fix |
|-------|-----|
| `agentcore: command not found` | `npm install -g @aws/agentcore` |
| Local test fails | Check CloudWatch logs, verify DynamoDB tables |
| AWS deployment times out | Wait 15+ min, Cognito creation is slow |
| Tools not registered | Re-run `agentcore deploy` |
| No logs in CloudWatch | Wait 5-10 minutes for logs to appear |

---

## 📞 Documentation Reference

- `README.md` - Project overview
- `RESOURCE_MAPPING.md` - Architecture & pillar mapping
- `AGENTCORE_DEPLOYMENT.md` - Full step-by-step guide
- `EXECUTION_CHECKLIST.md` - Detailed checkbox list
- `QUICK_REFERENCE.md` - Commands & troubleshooting
- `agentcore.yaml` - Configuration file

---

## 🎉 What You Will Have After Deployment

✅ RFP agent running on **AWS Bedrock AgentCore Runtime** (not Lambda)
✅ Agent calls **6 Lambda tools via MCP gateway**
✅ Conversations stored in **DynamoDB** with 30-day TTL
✅ Users authenticated via **Cognito**
✅ All operations logged to **CloudWatch**
✅ Tool execution traces in **X-Ray**
✅ Human approval gates ready for **sensitive operations**
✅ End-to-end RFP workflow **fully tested**

---

## 🚀 Ready to Start?

Follow this order:

1. **Read**: README.md (2 min)
2. **Read**: RESOURCE_MAPPING.md (10 min)
3. **Execute**: AGENTCORE_DEPLOYMENT.md steps 1-4 (45 min)
4. **Use**: EXECUTION_CHECKLIST.md during deployment (30 min)
5. **Reference**: QUICK_REFERENCE.md for commands (anytime)

---

**Total time from start to working agent: 60-85 minutes**

**Let's go! Start by reading README.md**

