# RFP Management System - AWS AgentCore Agent

Production-ready RFP (Request for Proposal) management system powered by Amazon Nova Pro with Strands Agents SDK, deployed to AWS AgentCore Runtime.

---

## 🚀 Quick Start

**New user?** Follow these steps in order:

1. **Understand the architecture**: Read `RESOURCE_MAPPING.md` (5 min)
2. **Deployment guide**: Follow `AGENTCORE_DEPLOYMENT.md` (step-by-step)
3. **Detailed checklist**: Use `EXECUTION_CHECKLIST.md` (with checkboxes)
4. **Quick reference**: Keep `QUICK_REFERENCE.md` handy (commands)

---

## 📋 What This Is

This is an RFP agent that runs inside **AWS Bedrock AgentCore Runtime**. It intelligently manages RFP workflows:

- 🔍 **Find suppliers** by category and requirements
- 📄 **Generate RFPs** and store documents in S3
- 📧 **Send emails** to suppliers with RFP details
- 📥 **Fetch proposals** from suppliers
- ⭐ **Score proposals** using weighted criteria
- 🏆 **Recommend top 2 suppliers** with reasoning

---

## 🏗️ Architecture

```
Client Request
    ↓
AWS Bedrock AgentCore Runtime
(Agent executes here)
    ↓
MCP Gateway
(Routes tool calls)
    ↓
6 Lambda Tools (run in parallel):
├─ supplier_lookup_tool (read suppliers)
├─ rfp_generator_tool (create RFP)
├─ email_dispatch_tool (send emails)
├─ proposal_fetch_tool (read proposals)
├─ scoring_tool (score proposals)
└─ recommendation_tool (rank suppliers)
    ↓
AWS Services:
├─ DynamoDB (data persistence)
├─ S3 (document storage)
├─ CloudWatch (logs & metrics)
├─ X-Ray (tracing)
└─ Cognito (identity)
```

---

## 📚 Deployment Documents

| Document | Purpose | Read Time |
|----------|---------|-----------|
| `RESOURCE_MAPPING.md` | Architecture & resource mapping | 10 min |
| `AGENTCORE_DEPLOYMENT.md` | Step-by-step deployment guide | 15 min |
| `EXECUTION_CHECKLIST.md` | Detailed checkbox checklist | 20 min |
| `QUICK_REFERENCE.md` | Commands & quick reference | 5 min |
| `agentcore.yaml` | Agent configuration (verify this) | 5 min |

**Recommended reading order:**
1. RESOURCE_MAPPING.md
2. AGENTCORE_DEPLOYMENT.md
3. EXECUTION_CHECKLIST.md (follow during deployment)
4. QUICK_REFERENCE.md (keep nearby during execution)

---

## 🔧 Project Structure

```
RFP MANAGEMENT/
│
├── 📄 README.md (this file)
├── 📄 agentcore.yaml (agent configuration - MAIN CONFIG)
├── 📄 RESOURCE_MAPPING.md (architecture guide)
├── 📄 AGENTCORE_DEPLOYMENT.md (deployment guide)
├── 📄 EXECUTION_CHECKLIST.md (step-by-step checklist)
├── 📄 QUICK_REFERENCE.md (commands reference)
│
├── 🐳 Dockerfile (orchestrator container)
│
└── RFP-main/ (agent source code)
    ├── agentcore_orchestrator.py (AGENT ENTRY POINT)
    ├── agentcore_memory.py (memory handler)
    ├── config.py (configuration)
    ├── requirements.txt (dependencies: 3 only)
    │
    └── lambda/ (6 tool Lambda functions)
        ├── supplier_lookup_lambda.py
        ├── rfp_generator_lambda.py
        ├── email_dispatch_lambda.py
        ├── proposal_fetch_lambda.py
        ├── scoring_lambda.py
        └── recommendation_lambda.py
```

---

## 🚀 Deployment Summary

This is a **7-phase deployment** to AWS AgentCore Runtime:

| Phase | Task | Time |
|-------|------|------|
| 1 | Install AgentCore CLI + AWS credentials | 10 min |
| 2 | Verify AWS resources & project structure | 15 min |
| 3 | Local dev test (DO NOT SKIP) | 20 min |
| 4 | Deploy to AWS AgentCore Runtime | 10-15 min |
| 5 | Verify all pillars in AWS Console | 15 min |
| 6 | End-to-end test in AWS Console | 10 min |
| 7 | Setup API Gateway (optional) | 5 min |
| | **Total time** | **60-85 min** |

---

## 📋 AgentCore Pillars

After deployment, the agent has **6 pillars**:

1. **Runtime Pillar** - Agent executes inside AWS Bedrock AgentCore
2. **Memory Pillar** - Conversations stored in DynamoDB (30-day TTL)
3. **Gateway Pillar** - 6 Lambda tools registered as MCP
4. **Identity Pillar** - Users authenticate via Cognito
5. **Observability Pillar** - Logs in CloudWatch, traces in X-Ray
6. **Policy Pillar** - Human approval gates for sensitive operations

---

## 💡 Key Technical Details

- **Framework**: Strands Agents SDK (for AI orchestration)
- **Model**: Amazon Nova Pro v1 (foundation model)
- **Language**: Python 3.12
- **Deployment**: Container images (not ZIP)
- **Database**: DynamoDB
- **Storage**: S3
- **Region**: us-east-1 (fixed)

---

## ✅ Prerequisites

Before you start:

- ✅ AWS Account with IAM permissions
- ✅ AWS credentials configured locally
- ✅ Node.js 18+ installed (for AgentCore CLI)
- ✅ 7 Lambda functions already deployed to us-east-1
- ✅ 6 DynamoDB tables created and seeded
- ✅ S3 bucket created
- ✅ IAM role with Lambda → DynamoDB/S3 access

---

## 🎯 Next Steps

1. **Read first**: `RESOURCE_MAPPING.md` (understand architecture)
2. **Follow**: `AGENTCORE_DEPLOYMENT.md` (step-by-step guide)
3. **Use checklist**: `EXECUTION_CHECKLIST.md` (detailed steps)
4. **Reference**: `QUICK_REFERENCE.md` (commands)

---

## 📞 Support

**Troubleshooting:**
- Check `QUICK_REFERENCE.md` for common errors
- View CloudWatch logs: `agentcore logs --follow`
- Check X-Ray traces for tool execution

**Documentation:**
- AWS Bedrock Agents: https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
- Project Repository: https://github.com/AbilashEG/rfp-management

---

## 🎉 Success Criteria

After deployment, you will have:

✅ Agent running inside AWS AgentCore Runtime (not Lambda)
✅ 6 Lambda tools registered as MCP gateway
✅ Memory persisting in DynamoDB (30-day TTL)
✅ User identity managed via Cognito
✅ All operations logged in CloudWatch
✅ Tool execution traces visible in X-Ray
✅ Human approval gates for sensitive operations
✅ End-to-end RFP workflow tested and working

---

**Ready to deploy? Start with: `RESOURCE_MAPPING.md`**
