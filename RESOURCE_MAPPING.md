# Resource Mapping: Current State → AgentCore Runtime

This document maps all existing resources to AgentCore pillars.

---

## Current State (Before AgentCore Deployment)

```
Lambda Functions (Already Deployed):
├─ rfp-agent-orchestrator-v2 (entry point)
├─ rfp-supplier-lookup-v2 (tool 1)
├─ rfp-rfp-generator-v2 (tool 2)
├─ rfp-email-dispatch-v2 (tool 3)
├─ rfp-proposal-fetch-v2 (tool 4)
├─ rfp-scoring-v2 (tool 5)
└─ rfp-recommendation-v2 (tool 6)

DynamoDB Tables (Already Created):
├─ agentcore-memory-v2 (for agent memory - 30 day TTL)
├─ rfp-suppliers (seeded with 8 suppliers)
├─ rfp-requests (seeded with 2 RFPs)
├─ rfp-proposals (seeded with 27 proposals)
├─ rfp-scores (empty - will populate during workflow)
└─ rfp-recommendations (empty - will populate during workflow)

S3 Bucket (Already Created):
└─ rfp-documents-quadrasystems-v2 (for RFP documents)

Source Code (Ready to Deploy):
├─ RFP-main/agentcore_orchestrator.py (agent entry point)
├─ RFP-main/agentcore_memory.py (memory handler)
├─ RFP-main/config.py (configuration)
├─ RFP-main/requirements.txt (dependencies)
└─ RFP-main/lambda/ (6 tool Lambdas)
```

---

## After AgentCore Deployment

```
Bedrock AgentCore Runtime (NEW):
├─ Agent: rfp-supplier-agent
├─ Framework: Strands Agents SDK
├─ Model: amazon.nova-pro-v1:0
├─ Region: us-east-1
└─ Entry Point: RFP-main/agentcore_orchestrator.handler

┌────────────────────────────────────────────────────────┐
│              AGENT CORE PILLARS (NEW)                   │
├────────────────────────────────────────────────────────┤
│                                                         │
│  1. RUNTIME PILLAR (Agent Execution)                  │
│     ├─ Hosted in: AWS Bedrock AgentCore              │
│     ├─ Framework: Strands Agents                     │
│     ├─ Model: amazon.nova-pro-v1:0                  │
│     └─ Entry: agentcore_orchestrator.handler        │
│                                                         │
│  2. MEMORY PILLAR (Conversation History)             │
│     ├─ Table: agentcore-memory-v2                   │
│     ├─ TTL: 30 days                                 │
│     ├─ Persistence: DynamoDB (auto-enabled)         │
│     └─ Auto-cleanup: Enabled                        │
│                                                         │
│  3. GATEWAY PILLAR (MCP Tool Registration)           │
│     ├─ supplier_lookup_tool        → rfp-supplier-lookup-v2      │
│     ├─ rfp_generator_tool          → rfp-rfp-generator-v2        │
│     ├─ email_dispatch_tool         → rfp-email-dispatch-v2       │
│     ├─ proposal_fetch_tool         → rfp-proposal-fetch-v2       │
│     ├─ scoring_tool                → rfp-scoring-v2              │
│     └─ recommendation_tool         → rfp-recommendation-v2       │
│                                                         │
│  4. IDENTITY PILLAR (User Authentication)            │
│     ├─ Provider: Cognito (auto-created)              │
│     ├─ User Pool: rfp-supplier-agent-pool            │
│     ├─ Auto-create: Enabled                          │
│     └─ Token validation: Enabled                     │
│                                                         │
│  5. OBSERVABILITY PILLAR (Monitoring & Logging)      │
│     ├─ Tracing: X-Ray (CloudWatch Service Map)       │
│     ├─ Logs: CloudWatch /agentcore/rfp-supplier-agent│
│     ├─ Metrics: Custom namespace RFPAgent             │
│     ├─ Log Retention: 30 days                        │
│     ├─ Structured Logs: Enabled                      │
│     └─ Custom Metrics:                               │
│         ├─ agent_execution_time                      │
│         ├─ tool_invocation_count                     │
│         └─ approval_decision_rate                    │
│                                                         │
│  6. POLICY PILLAR (Human Approval Gates)             │
│     ├─ Human Approval: Enabled                       │
│     ├─ Trigger Field: approval_required              │
│     ├─ Trigger Value: true                           │
│     └─ Timeout: 1 hour (3600 seconds)                │
│                                                         │
└────────────────────────────────────────────────────────┘

MCP Gateway (Tool Routing):
├─ Routes tool calls from agent to Lambda functions
├─ Manages retries (2-3 per tool)
├─ Handles timeouts (30-60 sec per tool)
└─ Returns results back to agent

Data Flow:
┌─────────────────────────────────────────────────────────┐
│ 1. User sends request to AgentCore Runtime endpoint    │
│ 2. Agent (Strands) receives request                    │
│ 3. Agent analyzes request (AWS Nova Pro)               │
│ 4. Agent calls Tool 1: supplier_lookup                 │
│    └─ MCP Gateway routes to rfp-supplier-lookup-v2     │
│    └─ Lambda queries rfp-suppliers table               │
│    └─ Returns suppliers to agent                       │
│ 5. Agent calls Tool 2: rfp_generator                   │
│    └─ MCP Gateway routes to rfp-rfp-generator-v2       │
│    └─ Lambda creates RFP, stores in S3                 │
│    └─ Returns document URL to agent                    │
│ 6. Agent calls Tool 3: email_dispatch                  │
│    └─ MCP Gateway routes to rfp-email-dispatch-v2      │
│    └─ Lambda sends emails to suppliers                 │
│    └─ Returns confirmation to agent                    │
│ 7. Agent calls Tool 4: proposal_fetch                  │
│    └─ MCP Gateway routes to rfp-proposal-fetch-v2      │
│    └─ Lambda reads rfp-proposals table                 │
│    └─ Returns proposals to agent                       │
│ 8. Agent calls Tool 5: scoring                         │
│    └─ MCP Gateway routes to rfp-scoring-v2             │
│    └─ Lambda scores proposals, stores in rfp-scores    │
│    └─ Returns scores to agent                          │
│ 9. Agent calls Tool 6: recommendation                  │
│    └─ MCP Gateway routes to rfp-recommendation-v2      │
│    └─ Lambda generates ranking, stores in rfp-recommendations │
│    └─ Returns top 2 suppliers to agent                 │
│ 10. Agent stores session in agentcore-memory-v2        │
│ 11. Agent returns recommendations to user              │
│ 12. X-Ray traces entire flow (observability)           │
│ 13. CloudWatch logs all operations                     │
└─────────────────────────────────────────────────────────┘
```

---

## File to Resource Mapping

| Source File | Type | AWS Resource | Pillar |
|-------------|------|-------------|--------|
| `agentcore.yaml` | Config | Agent Configuration | All |
| `RFP-main/agentcore_orchestrator.py` | Code | Agent Runtime Entry | Runtime |
| `RFP-main/agentcore_memory.py` | Code | Memory Handler | Memory |
| `RFP-main/config.py` | Code | Configuration Loader | All |
| `RFP-main/lambda/supplier_lookup_lambda.py` | Tool | rfp-supplier-lookup-v2 | Gateway |
| `RFP-main/lambda/rfp_generator_lambda.py` | Tool | rfp-rfp-generator-v2 | Gateway |
| `RFP-main/lambda/email_dispatch_lambda.py` | Tool | rfp-email-dispatch-v2 | Gateway |
| `RFP-main/lambda/proposal_fetch_lambda.py` | Tool | rfp-proposal-fetch-v2 | Gateway |
| `RFP-main/lambda/scoring_lambda.py` | Tool | rfp-scoring-v2 | Gateway |
| `RFP-main/lambda/recommendation_lambda.py` | Tool | rfp-recommendation-v2 | Gateway |
| DynamoDB table | Data | agentcore-memory-v2 | Memory |
| DynamoDB table | Data | rfp-suppliers | Tool 1 Data |
| DynamoDB table | Data | rfp-requests | Tool 2 Data |
| DynamoDB table | Data | rfp-proposals | Tool 4 Data |
| DynamoDB table | Data | rfp-scores | Tool 5 Data |
| DynamoDB table | Data | rfp-recommendations | Tool 6 Data |
| S3 bucket | Storage | rfp-documents-quadrasystems-v2 | Tool 2 Storage |
| X-Ray service | Monitoring | Service Map | Observability |
| CloudWatch Logs | Monitoring | /agentcore/rfp-supplier-agent | Observability |
| Cognito | Identity | rfp-supplier-agent-pool | Identity |

---

## Execution Flow: Step by Step

### Phase 1: Before Deployment (Current State)

```
Lambda Orchestrator (rfp-agent-orchestrator-v2)
├─ Called manually via AWS Console
├─ Reads agent code from RFP-main/agentcore_orchestrator.py
├─ Calls individual tool Lambdas directly
├─ No MCP Gateway routing
├─ No agent memory persistence
└─ No observability (X-Ray/CloudWatch)
```

### Phase 2: Local Testing (Step 4)

```
Local AgentCore Dev Server
├─ Runs agentcore_orchestrator.py locally
├─ Emulates AWS Bedrock AgentCore Runtime
├─ Tests 6 MCP tools against real DynamoDB/S3
├─ Tests memory persistence
├─ Tests policy gates
└─ Tests observability logging
```

### Phase 3: After AWS Deployment (Step 5)

```
AWS Bedrock AgentCore Runtime
├─ Agent deployed to managed service
├─ MCP Gateway created and configured
├─ Tools auto-registered:
│  └─ supplier_lookup → rfp-supplier-lookup-v2
│  └─ rfp_generator → rfp-rfp-generator-v2
│  └─ email_dispatch → rfp-email-dispatch-v2
│  └─ proposal_fetch → rfp-proposal-fetch-v2
│  └─ scoring → rfp-scoring-v2
│  └─ recommendation → rfp-recommendation-v2
├─ Memory auto-enabled (agentcore-memory-v2)
├─ Identity auto-enabled (Cognito)
├─ Observability auto-enabled (X-Ray + CloudWatch)
├─ Policy auto-enabled (human approval gates)
└─ Agent runs inside AWS managed runtime
```

### Phase 4: Production Use

```
Client → API Gateway (optional) → AgentCore Runtime Endpoint
                                    ├─ Bedrock Agents (Nova Pro)
                                    ├─ MCP Gateway (6 tools)
                                    ├─ Memory (DynamoDB)
                                    ├─ Identity (Cognito)
                                    ├─ Policy (Approval gates)
                                    └─ Observability (X-Ray/CW)
```

---

## Prerequisites Check

Before deploying, verify all resources exist:

### AWS Resources (Already Created)

```bash
# Check Lambda functions exist
aws lambda list-functions --region us-east-1 | grep rfp

# Check DynamoDB tables exist
aws dynamodb list-tables --region us-east-1 | grep rfp

# Check S3 bucket exists
aws s3 ls | grep rfp-documents

# Check Bedrock model access
aws bedrock list-available-models --region us-east-1 | grep nova
```

### Source Code (Ready)

```bash
# Verify files exist
ls -la agentcore.yaml
ls -la RFP-main/agentcore_orchestrator.py
ls -la RFP-main/lambda/
```

### AWS Permissions

Verify your AWS user/role has:
- `bedrock:*` (for AgentCore Runtime)
- `lambda:InvokeFunction` (to call tools)
- `dynamodb:*` (for memory table)
- `s3:*` (for documents)
- `xray:*` (for tracing)
- `logs:*` (for CloudWatch)
- `cognito:*` (for identity)

---

## Deployment Commands Summary

```bash
# Step 1: Install CLI
npm install -g @aws/agentcore

# Step 2: Configure credentials
aws configure

# Step 3: Verify structure (manual check)

# Step 4: Local test
agentcore dev
agentcore invoke '{"message": "..."}'

# Step 5: Deploy to AWS
agentcore deploy

# Step 6: Verify pillars (manual AWS Console check)

# Step 7: Test in AWS Console (manual test)

# Step 8: Setup API Gateway (optional)
agentcore add api-gateway
agentcore deploy
```

---

## Troubleshooting Matrix

| Problem | Root Cause | Solution |
|---------|-----------|----------|
| `agentcore: command not found` | CLI not installed | Run: `npm install -g @aws/agentcore` |
| Local dev fails to load agent | File path wrong | Check `entry_point` in agentcore.yaml |
| Tools not registered | Lambda not in us-east-1 | Deploy all Lambdas to us-east-1 |
| Memory not persisting | Table doesn't exist | Create agentcore-memory-v2 table |
| Deployment times out | Cognito creation slow | Wait 10-15 min, check Cognito console |
| Tools return errors | DynamoDB tables not seeded | Run seed_data.py in RFP-main/setup |
| X-Ray traces missing | Observability disabled | Re-run `agentcore deploy` |
| Approval gate not working | SQS queue not configured | Run `agentcore add policy` |

---

## Cost Estimate (Monthly)

```
AgentCore Runtime:
├─ Agent Execution: $0.24/1M invocations
│  └─ Est. 100k/month = $24
├─ MCP Tool Calls: $0.10 per call
│  └─ 6 tools × 100k = $600
├─ Memory Storage: $1.25/GB/month
│  └─ Est. 1GB = $1.25
└─ Observability: $0.50/trace, $5/GB logs
   └─ Est. 1000 traces + 10GB logs = $550

Lambda Tool Functions:
├─ Invocations: 6 tools × 100k = $0.20
├─ Memory: 6 × 512MB × 100s = ~$25
└─ Data Transfer: ~$10

DynamoDB:
├─ On-Demand Read: ~$30
├─ On-Demand Write: ~$30
└─ Storage: ~$10

S3:
├─ Storage: ~$5
└─ Requests: ~$1

**Estimated Monthly Cost: ~$1,200**
```

---

## Next Steps

1. ✅ Verify all resources exist (prerequisite check above)
2. ✅ Follow AGENTCORE_DEPLOYMENT.md steps 1-8
3. ✅ Monitor cost in AWS Billing dashboard
4. ✅ Set up auto-scaling policies
5. ✅ Create backup strategy for agent memory
6. ✅ Document custom approval workflow

