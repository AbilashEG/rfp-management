# Resource Mapping - AgentCore to AWS

## ARCHITECTURE MAPPING

```
LOCAL DEVELOPMENT
─────────────────────────────────────────
agentcore dev → AgentCore Dev Server (localhost:8080)
    ↓
    ├─ agentcore_orchestrator.py (Strands Agent)
    │   └─ Uses: amazon.nova-pro-v1:0 (Bedrock)
    │
    └─ 6 MCP Tools (Local Routing)
        ├─ supplier_lookup_lambda → rfp-supplier-lookup (Lambda)
        ├─ rfp_generator_lambda → rfp-rfp-generator (Lambda)
        ├─ email_dispatch_lambda → rfp-email-dispatch (Lambda)
        ├─ proposal_fetch_lambda → rfp-proposal-fetch (Lambda)
        ├─ scoring_lambda → rfp-scoring (Lambda)
        └─ recommendation_lambda → rfp-recommendation (Lambda)
            ↓
            Data Layer
            ├─ DynamoDB: rfp-suppliers, rfp-requests, rfp-proposals, rfp-scores
            ├─ S3: rfp-documents-quadrasystems
            └─ Memory: agentcore-memory-v2


AWS PRODUCTION
─────────────────────────────────────────
agentcore deploy → AWS AgentCore Runtime
    ↓
    ┌─────────────────────────────────────────┐
    │ AgentCore Runtime Instance              │
    │ (Managed by AWS)                        │
    │                                         │
    │ ┌─ Agent Container ──────────────────┐ │
    │ │ agentcore_orchestrator.py          │ │
    │ │ (Strands Agent)                    │ │
    │ └────────────────────────────────────┘ │
    │                ↓                       │
    │ ┌─ Runtime Endpoint ─────────────────┐ │
    │ │ https://agentcore.us-east-1...     │ │
    │ │ /agents/rfp-supplier-agent         │ │
    │ └────────────────────────────────────┘ │
    │                ↓                       │
    │ ┌─ MCP Gateway ──────────────────────┐ │
    │ │ (Tool Router)                      │ │
    │ │                                    │ │
    │ │ Registered Tools:                  │ │
    │ │  • supplier_lookup_tool            │ │
    │ │  • rfp_generator_tool              │ │
    │ │  • email_dispatch_tool             │ │
    │ │  • proposal_fetch_tool             │ │
    │ │  • scoring_tool                    │ │
    │ │  • recommendation_tool             │ │
    │ └────────────────────────────────────┘ │
    │                ↓                       │
    │ ┌─ Pillars (Built-in) ───────────────┐ │
    │ │ ✓ Memory (30-day TTL)              │ │
    │ │ ✓ Identity (Cognito)               │ │
    │ │ ✓ Observability (X-Ray, CW)        │ │
    │ │ ✓ Policy (Human Approval)          │ │
    │ └────────────────────────────────────┘ │
    └─────────────────────────────────────────┘
                   ↓
            ┌──────┴──────────────┬──────────────┐
            ↓                     ↓              ↓
        MCP Tool 1-6          DynamoDB        S3
        (Lambda)              Tables          Bucket
        
        ├─ rfp-supplier-lookup        → rfp-suppliers
        ├─ rfp-rfp-generator          → rfp-requests
        ├─ rfp-email-dispatch         → (email)
        ├─ rfp-proposal-fetch         → rfp-proposals
        ├─ rfp-scoring                → rfp-scores
        └─ rfp-recommendation         → (recommendations)
                                          +
                                      rfp-documents-
                                      quadrasystems
```

---

## FILE-TO-RESOURCE MAPPING

### Source Code → AgentCore Runtime

| Source File | Maps To | AgentCore Component | AWS Resource |
|---|---|---|---|
| `agentcore_orchestrator.py` | Agent Logic | Runtime Container | EC2 (managed) |
| `agentcore_memory.py` | Memory Service | Memory Pillar | DynamoDB table |
| `config.py` | Configuration | Runtime Settings | Parameter Store |
| `requirements.txt` | Dependencies | Container Image | ECR |

### Lambda Tools → MCP Gateway

| Lambda File | Tool Name | Registered As | MCP Gateway |
|---|---|---|---|
| `supplier_lookup_lambda.py` | Supplier Lookup | `supplier_lookup_tool` | ✓ Registered |
| `rfp_generator_lambda.py` | RFP Generator | `rfp_generator_tool` | ✓ Registered |
| `email_dispatch_lambda.py` | Email Dispatch | `email_dispatch_tool` | ✓ Registered |
| `proposal_fetch_lambda.py` | Proposal Fetch | `proposal_fetch_tool` | ✓ Registered |
| `scoring_lambda.py` | Scoring | `scoring_tool` | ✓ Registered |
| `recommendation_lambda.py` | Recommendations | `recommendation_tool` | ✓ Registered |

### Configuration → Pillars

| agentcore.yaml Section | Maps To | AWS Resource | Status |
|---|---|---|---|
| `runtime` | Runtime Pillar | AgentCore Runtime | ✓ |
| `memory` | Memory Pillar | DynamoDB + TTL | ✓ |
| `identity.provider: cognito` | Identity Pillar | Cognito User Pool | ✓ |
| `observability` | Observability Pillar | X-Ray + CloudWatch | ✓ |
| `policy.human_approval` | Policy Pillar | Approval Queue/Workflow | ✓ |
| `gateway.mcp.tools` | Gateway Pillar | MCP Tool Registry | ✓ |

---

## DATA FLOW MAPPING

### Request → Response Flow

```
1. CLIENT REQUEST
   {"message": "Create RFP for sensors"}
   ↓

2. AGENTCORE RUNTIME
   agentcore_orchestrator.py executes
   ├─ Nova Pro LLM processes message
   ├─ Decides which tools to invoke
   └─ Routes through MCP Gateway
   ↓

3. MCP GATEWAY ROUTES
   ├─ Tool 1: supplier_lookup_tool
   │  └─ Invokes: rfp-supplier-lookup Lambda
   │     └─ Reads: rfp-suppliers DynamoDB table
   │
   ├─ Tool 2: rfp_generator_tool
   │  └─ Invokes: rfp-rfp-generator Lambda
   │     └─ Writes: rfp-requests table + S3
   │
   ├─ Tool 3: email_dispatch_tool
   │  └─ Invokes: rfp-email-dispatch Lambda
   │     └─ Sends: Emails via SES
   │
   ├─ Tool 4: proposal_fetch_tool
   │  └─ Invokes: rfp-proposal-fetch Lambda
   │     └─ Reads: rfp-proposals table
   │
   ├─ Tool 5: scoring_tool
   │  └─ Invokes: rfp-scoring Lambda
   │     └─ Writes: rfp-scores table
   │
   └─ Tool 6: recommendation_tool
      └─ Invokes: rfp-recommendation Lambda
         └─ Reads: rfp-scores table
   ↓

4. MEMORY PILLAR
   Session saved to agentcore-memory-v2
   ├─ Conversation history persisted
   ├─ TTL: 30 days auto-cleanup
   └─ Retrieved on next request
   ↓

5. OBSERVABILITY PILLAR
   ├─ X-Ray: Traces all Lambda calls
   ├─ CloudWatch: Logs each step
   └─ Metrics: Performance data
   ↓

6. POLICY PILLAR
   ├─ Check: approval_required = true?
   ├─ If yes: Send to approval workflow
   └─ If no: Auto-approve
   ↓

7. RESPONSE
   {"status": "SUCCESS", "rfp_id": "RFP-..."}
```

---

## DEPLOYMENT MAPPING

### What Gets Created

| Action | Creates | Maps To | Resource ID |
|---|---|---|---|
| `agentcore deploy` | AgentCore Runtime | Bedrock Agents | `agent-20260617-abc123` |
| MCP Registration | Tool Gateways (6x) | Lambda Invocation | `supplier_lookup_tool` etc |
| Memory Setup | DynamoDB Link | DynamoDB table | `agentcore-memory-v2` |
| Observability Setup | CloudWatch Logs | Log Group | `/agentcore/rfp-supplier-agent` |
| X-Ray Activation | Service Map | X-Ray Groups | `rfp-supplier-agent` |
| Identity Config | Cognito Integration | User Pool | `us-east-1_XXXXX` |
| Policy Setup | Approval Queue | SQS Queue | `rfp-approval-queue` |

---

## INVOCATION MAPPING

### How Requests Get Routed

```
CLIENT
  ↓
HTTP → https://agentcore.us-east-1.amazonaws.com/agents/rfp-supplier-agent
  ↓
API Gateway (if configured)
  OR
Direct AgentCore Endpoint
  ↓
AWS IAM (Authentication)
  ↓
Cognito (Identity Pillar)
  Validates token
  ↓
AgentCore Runtime
  ↓
Agent Logic (agentcore_orchestrator.py)
  ↓
Tool Selection (LLM Decision)
  ↓
MCP Gateway
  ↓
Tool Invocation (Parallel/Sequential)
  ├─ Lambda 1 → Results
  ├─ Lambda 2 → Results
  ├─ Lambda 3 → Results
  ├─ Lambda 4 → Results
  ├─ Lambda 5 → Results
  └─ Lambda 6 → Results
  ↓
Memory Pillar
  Save context to DynamoDB
  ↓
Policy Pillar
  Check approval gate
  ↓
Response Assembly
  ↓
Observability Pillar
  Log + Trace
  ↓
HTTP Response ← Client
```

---

## RESOURCE VERIFICATION

### What to Check After Deployment

| Pillar | AWS Console Path | Verify |
|---|---|---|
| **Runtime** | Bedrock → Agents | Status = ACTIVE |
| **Gateway** | Agent detail → Gateway | 6 tools listed |
| **Memory** | Agent detail → Memory | Table = agentcore-memory-v2, TTL = 30d |
| **Identity** | Agent detail → Identity | Provider = Cognito |
| **Observability** | Agent detail → Observability | X-Ray ✓, CloudWatch ✓ |
| **Policy** | Agent detail → Policy | Approval enabled ✓ |
| **Logs** | CloudWatch → Log Groups | `/agentcore/rfp-supplier-agent` exists |
| **Traces** | X-Ray → Service Map | Node for each tool visible |
| **Data** | DynamoDB | All 4 tables have items |

---

## MONITORING MAPPING

### Where to Monitor What

| Metric | Tool | Location | Check |
|---|---|---|---|
| Agent Status | AWS Console | Bedrock → Agents | ACTIVE |
| Tool Invocations | CloudWatch Logs | `/agentcore/rfp-supplier-agent` | "Tool invoked: supplier_lookup_tool" |
| Error Rate | CloudWatch Metrics | Custom namespace: RFPAgent | Error count |
| Latency | X-Ray | Service Map | Duration per tool |
| Requests/min | CloudWatch | Custom metrics | Request count |
| Memory Usage | CloudWatch | Lambda metrics | MB used |
| Memory Hits | DynamoDB | Metrics | Read/write operations |

---

## COST MAPPING

| Resource | Cost Driver | Estimated |
|---|---|---|
| AgentCore Runtime | Concurrent agents | $X per agent-hour |
| Lambda (6 tools) | Invocations + duration | Pay-per-invocation |
| DynamoDB | Read/write units | On-demand pricing |
| S3 | Storage + requests | GB stored + operations |
| X-Ray | Traces | Per 1M traces |
| CloudWatch | Logs + metrics | Per GB ingested |

---

