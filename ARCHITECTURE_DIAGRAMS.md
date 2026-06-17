# Architecture Diagrams - AgentCore RFP Agent

Visual diagrams showing the agent architecture before and after AgentCore deployment.

---

## 1. Current State: Agent Inside Lambda

```
┌─────────────────────────────────────────────────────────────┐
│ AWS Lambda: rfp-agent-orchestrator-v2                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Strands Agent (agentcore_orchestrator.py)          │    │
│  ├────────────────────────────────────────────────────┤    │
│  │ • Processes RFP request                            │    │
│  │ • Calls all 6 tools directly                       │    │
│  │ • Returns recommendations                          │    │
│  └────────────────────────────────────────────────────┘    │
│                 ↓        ↓        ↓                         │
│        ┌────────┴────────┼────────┴───────┐                │
│        │                 │                 │                │
│  ┌─────▼─────┐    ┌──────▼──────┐   ┌────▼─────┐          │
│  │Tool Lambda│    │Tool Lambda  │   │Tool Lamb  │          │
│  │ 1        │    │ 2           │   │ 3       │          │
│  └───────────┘    └─────────────┘   └────────┘            │
│        +                 +                 +                │
│  (No MCP Gateway, Direct Lambda Calls)                     │
│  (No Memory Persistence, No Observability)                 │
│  (Agent inside Lambda = not scalable)                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Problems with this approach:**
- ❌ Agent runs inside Lambda (cold starts, timeouts)
- ❌ No MCP gateway routing
- ❌ No conversation memory persistence
- ❌ No unified observability
- ❌ No identity management
- ❌ No human approval gates
- ❌ Limited to Lambda 15-min timeout

---

## 2. Target State: Agent in AgentCore Runtime

```
┌─────────────────────────────────────────────────────────────┐
│ AWS Bedrock AgentCore Runtime (NEW - Agent runs here)       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ AGENT                                              │    │
│  │ (Strands Agents SDK + Amazon Nova Pro)            │    │
│  └────────────────────────────────────────────────────┘    │
│                        ↓                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │ MCP GATEWAY (Model Context Protocol)               │    │
│  │ • Routes tool calls to 6 Lambda functions          │    │
│  │ • Manages timeouts & retries                       │    │
│  │ • Handles tool responses                           │    │
│  └────────────────────────────────────────────────────┘    │
│     ↓    ↓    ↓    ↓    ↓    ↓                             │
│  ┌──┴──┬──┴──┬──┴──┬──┴──┬──┴──┬──┴──┐                    │
│  │Tool1│Tool2│Tool3│Tool4│Tool5│Tool6│ (6 Lambda Tools)  │
│  └─────┴─────┴─────┴─────┴─────┴─────┘                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
        ↓           ↓            ↓           ↓
   ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐
   │DynamoDB │ │   S3    │ │CloudWatch│ │  X-Ray   │
   │  Data   │ │Documents│ │  Logs    │ │ Traces   │
   └─────────┘ └─────────┘ └──────────┘ └──────────┘

┌─────────────────────────────────────────────────────────────┐
│ AGENTCORE PILLARS (AUTO-ENABLED)                            │
├─────────────────────────────────────────────────────────────┤
│ ✓ RUNTIME    - Agent hosted in managed service             │
│ ✓ GATEWAY    - MCP routing to 6 Lambda tools               │
│ ✓ MEMORY     - DynamoDB agentcore-memory-v2 (30-day TTL)   │
│ ✓ IDENTITY   - Cognito user pool (auto-created)            │
│ ✓ OBSERVABILITY - CloudWatch + X-Ray                       │
│ ✓ POLICY     - Human approval gates                         │
└─────────────────────────────────────────────────────────────┘
```

**Benefits of this approach:**
- ✅ Agent runs in managed AgentCore Runtime (no cold starts)
- ✅ MCP Gateway for tool routing
- ✅ Automatic conversation memory persistence
- ✅ Unified observability (CloudWatch + X-Ray)
- ✅ User identity management (Cognito)
- ✅ Human approval gates for sensitive ops
- ✅ No Lambda timeout limits
- ✅ Automatic scaling

---

## 3. Request Flow: Step by Step

```
┌────────────────────────────────────────────────────────────────┐
│ CLIENT REQUEST                                                  │
│ "We need 500 brake sensors by Sept 2026"                       │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 1: Request arrives at AgentCore Runtime Endpoint          │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 2: Agent receives request + loads context from memory    │
│         (Session history from DynamoDB agentcore-memory-v2)    │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 3: Agent (Strands + Nova Pro) analyzes request           │
│         "User wants: 500 sensors, deadline Sept 2026"         │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 4: Agent decides to call Tool 1                          │
│         tool_name: "supplier_lookup_tool"                     │
│         params: {category: "sensors", quantity: 500}          │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 5: MCP Gateway routes to Lambda Tool 1                   │
│         Invokes: rfp-supplier-lookup-v2                       │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 6: Tool 1 Lambda queries DynamoDB rfp-suppliers table    │
│         Returns: [supplier1, supplier2, supplier3, ...]       │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 7: MCP Gateway returns result to Agent                   │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 8: Agent calls Tool 2: rfp_generator_tool               │
│         params: {suppliers: [...], deadline: "2026-09-30"}    │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 9: Tool 2 Lambda                                         │
│         • Creates RFP document                                │
│         • Stores in S3 bucket                                 │
│         • Returns document URL                                │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 10: Agent calls Tool 3: email_dispatch_tool             │
│          params: {suppliers: [...], document_url: "..."}      │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 11: Tool 3 Lambda sends emails to suppliers              │
│          Returns: [email1_sent, email2_sent, ...]             │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 12: Agent calls Tool 4: proposal_fetch_tool             │
│          params: {rfp_id: "RFP-..."}                          │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 13: Tool 4 Lambda reads DynamoDB rfp-proposals table    │
│          Returns: [proposal1, proposal2, proposal3, ...]      │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 14: Agent calls Tool 5: scoring_tool                     │
│          params: {proposals: [...], criteria: {...}}          │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 15: Tool 5 Lambda                                        │
│          • Scores each proposal                               │
│          • Stores scores in DynamoDB rfp-scores table        │
│          • Returns scores array                               │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 16: Agent calls Tool 6: recommendation_tool             │
│          params: {scores: [...]}                              │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 17: Tool 6 Lambda                                        │
│          • Ranks suppliers                                    │
│          • Stores top 2 in DynamoDB rfp-recommendations      │
│          • Returns top 2 with reasoning                       │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 18: Agent stores session in DynamoDB agentcore-memory-v2│
│          Memory persists for 30 days                          │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 19: Agent returns final response to client               │
│          Response:                                            │
│          {                                                    │
│            "status": "SUCCESS",                               │
│            "rfp_id": "RFP-20260617-E999BE46",                │
│            "recommendations": [                               │
│              {supplier: "TechSupply Corp", score: 9.2, ...}  │
│              {supplier: "Global Components Inc", score: 8.9} │
│            ]                                                  │
│          }                                                    │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 20: X-Ray logs entire execution trace                    │
│          Shows all tool calls, durations, dependencies        │
└────────────┬─────────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────────┐
│ STEP 21: CloudWatch logs written with all operations          │
│          Log Group: /agentcore/rfp-supplier-agent             │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Flow: Before & After AgentCore

### BEFORE (Current - Agent in Lambda)

```
┌──────────────┐
│ User Request │
└──────┬───────┘
       ↓
┌────────────────────────────┐
│ Lambda: rfp-orchestrator-v2 │ (Agent here - 15 min timeout)
│                             │
│ ┌─────────────────────────┐ │
│ │ Agent                   │ │
│ │ • Orchestrates workflow │ │
│ │ • Direct tool calls     │ │
│ │ • No memory persistence │ │
│ │ • No observability      │ │
│ └─────────────────────────┘ │
└────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│ 6 Lambda Tools (called directly)         │
│ • No MCP gateway                         │
│ • No standardization                     │
│ • No retry logic                         │
└──────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│ Data Output (temporary, no persistence)  │
│ • No session history                     │
│ • No tracing                             │
│ • No centralized logs                    │
└──────────────────────────────────────────┘
```

**Issues:**
- Agent limited by Lambda 15-minute timeout
- No memory persistence between requests
- No unified observability
- Tool calls not standardized
- No identity management
- Manual approval process

### AFTER (Target - Agent in AgentCore Runtime)

```
┌──────────────┐
│ User Request │
└──────┬───────┘
       ↓
┌────────────────────────────────────────────┐
│ AWS Bedrock AgentCore Runtime (NEW)        │
│                                             │
│ ┌──────────────────────────────────────┐  │
│ │ Agent (Strands + Nova Pro)           │  │
│ │ • No timeout limits                  │  │
│ │ • Managed scaling                    │  │
│ │ • Auto-recovery                      │  │
│ └──────────────────────────────────────┘  │
│              ↓                              │
│ ┌──────────────────────────────────────┐  │
│ │ MCP Gateway                          │  │
│ │ • Tool routing & standardization     │  │
│ │ • Retry logic (2-3 retries)         │  │
│ │ • Timeout management                │  │
│ └──────────────────────────────────────┘  │
└─┬──────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────┐
│ 6 Lambda Tools (via MCP)                 │
│ • Standardized interface                 │
│ • Parallel execution                     │
│ • Automatic retries                      │
│ • Timeout protection                     │
└──────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────┐
│ AWS Data & Observability Layer           │
│                                          │
│ ┌────────────┐  ┌────────────────────┐ │
│ │ DynamoDB   │  │ Memory Table       │ │
│ │ Tables     │  │ (30-day TTL)       │ │
│ │ • Suppliers│  │ • Session history  │ │
│ │ • Requests │  │ • Conversation ctx │ │
│ │ • Proposals│  │ • User identity    │ │
│ │ • Scores   │  └────────────────────┘ │
│ └────────────┘                          │
│                                          │
│ ┌────────────┐  ┌────────────────────┐ │
│ │ CloudWatch │  │ X-Ray              │ │
│ │ Logs       │  │ Traces             │ │
│ │ • All ops  │  │ • Tool execution   │ │
│ │ • Errors   │  │ • Dependencies     │ │
│ │ • Metrics  │  │ • Performance      │ │
│ └────────────┘  └────────────────────┘ │
│                                          │
│ ┌────────────┐  ┌────────────────────┐ │
│ │ S3         │  │ Cognito            │ │
│ │ Documents  │  │ Identity           │ │
│ │ • RFP docs │  │ • User auth        │ │
│ │ • Audit    │  │ • Sessions         │ │
│ └────────────┘  └────────────────────┘ │
└──────────────────────────────────────────┘
```

**Improvements:**
- ✅ No timeout limits (managed service)
- ✅ Memory persistence (30-day TTL)
- ✅ Unified observability (centralized logs & traces)
- ✅ Standardized tool interface (MCP)
- ✅ Identity management (Cognito)
- ✅ Approval gates (human review)
- ✅ Auto-scaling (managed service)

---

## 5. Pillar Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  AGENTCORE RUNTIME                        │
│                  (Bedrock Service)                        │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ PILLAR 1: RUNTIME                              │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ • Agent execution (Strands Framework)           │    │
│  │ • Model: amazon.nova-pro-v1:0                  │    │
│  │ • Managed by AWS (no Lambda timeout)            │    │
│  │ • Auto-scaling (5-10 instances)                │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ PILLAR 2: GATEWAY (MCP)                         │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ • Routes tool calls to 6 Lambda functions      │    │
│  │ • Tool 1: supplier_lookup_tool                 │    │
│  │ • Tool 2: rfp_generator_tool                   │    │
│  │ • Tool 3: email_dispatch_tool                  │    │
│  │ • Tool 4: proposal_fetch_tool                  │    │
│  │ • Tool 5: scoring_tool                         │    │
│  │ • Tool 6: recommendation_tool                  │    │
│  │ • Retry logic: 2-3 retries per tool            │    │
│  │ • Timeout: 30-60 seconds per tool              │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ PILLAR 3: MEMORY                               │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ • DynamoDB table: agentcore-memory-v2          │    │
│  │ • TTL: 30 days                                 │    │
│  │ • Stores: Session ID + Conversation History    │    │
│  │ • Persistence: Automatic (no code needed)      │    │
│  │ • Accessible across calls                      │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ PILLAR 4: IDENTITY                             │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ • Cognito User Pool (auto-created)             │    │
│  │ • User authentication                          │    │
│  │ • Token validation                             │    │
│  │ • Session management                           │    │
│  │ • MFA support (optional)                       │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ PILLAR 5: OBSERVABILITY                        │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ • CloudWatch Logs                              │    │
│  │   └─ Log Group: /agentcore/rfp-supplier-agent │    │
│  │   └─ Retention: 30 days                        │    │
│  │   └─ Structured logging enabled                │    │
│  │                                                 │    │
│  │ • X-Ray Tracing                                │    │
│  │   └─ Service Map (tool dependencies)           │    │
│  │   └─ Traces (execution paths)                  │    │
│  │   └─ Segments (tool calls)                     │    │
│  │                                                 │    │
│  │ • CloudWatch Metrics                           │    │
│  │   └─ agent_execution_time                      │    │
│  │   └─ tool_invocation_count                     │    │
│  │   └─ approval_decision_rate                    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ PILLAR 6: POLICY (Human Approval)              │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ • Human Approval Gates: ENABLED                │    │
│  │ • Trigger Field: approval_required             │    │
│  │ • Trigger Value: true                          │    │
│  │ • Timeout: 1 hour (3600 seconds)               │    │
│  │ • SQS Queue: approval queue (optional)         │    │
│  │ • When triggered:                              │    │
│  │   └─ Agent pauses execution                    │    │
│  │   └─ Sends notification to approver            │    │
│  │   └─ Waits for approval/rejection              │    │
│  │   └─ Continues or aborts based on response    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 6. Deployment Timeline

```
BEFORE AGENTCORE DEPLOYMENT:
─────────────────────────────────────────────────────────

Lambda Functions:         ✓ Deployed (container images)
DynamoDB Tables:          ✓ Created & seeded
S3 Bucket:               ✓ Ready
Agent Code:              ✓ Ready (agentcore_orchestrator.py)


AGENTCORE DEPLOYMENT PHASES:
─────────────────────────────────────────────────────────

Phase 1: Setup & Install
├─ npm install -g @aws/agentcore        [5 min]
├─ aws configure                        [5 min]
└─ Verify credentials                   [5 min]

Phase 2: Verify Prerequisites
├─ Check Lambda functions exist         [5 min]
├─ Check DynamoDB tables exist          [5 min]
└─ Check project structure              [5 min]

Phase 3: Local Development Test
├─ agentcore dev (start server)         [5 min]
├─ agentcore invoke (test agent)        [10 min]
├─ Verify memory persistence            [3 min]
└─ Stop dev server                      [2 min]

Phase 4: Deploy to AWS
├─ agentcore deploy                     [5-10 min WAIT]
├─ Create AgentCore Runtime             [2 min]
├─ Register MCP tools                   [1 min]
├─ Configure Memory pillar              [1 min]
├─ Configure Identity pillar            [1 min]
├─ Configure Observability pillar       [1 min]
└─ Configure Policy pillar              [1 min]

Phase 5: Verify All Pillars
├─ Check Runtime in AWS Console         [2 min]
├─ Check Gateway (6 tools)              [2 min]
├─ Check Memory (DynamoDB)              [2 min]
├─ Check Identity (Cognito)             [2 min]
├─ Check Observability (CW + X-Ray)    [3 min]
└─ Check Policy (approval gates)        [2 min]

Phase 6: End-to-End Test
├─ Test in AWS Console                  [5 min]
├─ Verify all tools called              [3 min]
└─ Verify response format               [2 min]

Phase 7: API Gateway (Optional)
├─ agentcore add api-gateway            [2 min]
├─ agentcore deploy                     [2-3 min]
└─ Test via curl                        [3 min]


TOTAL TIME:
─────────────────────────────────────────────────────────
Phase 1-3:  25 minutes
Phase 4:    15 minutes
Phase 5:    15 minutes
Phase 6:    10 minutes
Phase 7:    7 minutes (optional)
────────────────────────────────────────────────────────
TOTAL:      60-85 minutes


AFTER AGENTCORE DEPLOYMENT:
─────────────────────────────────────────────────────────

✅ Agent in AgentCore Runtime (not Lambda)
✅ 6 Lambda tools via MCP Gateway
✅ Memory in DynamoDB (30-day TTL)
✅ Identity in Cognito
✅ Logs in CloudWatch
✅ Traces in X-Ray
✅ Approval gates ready
✅ Production ready
```

---

## 7. Cost Comparison

### Before: Lambda-Based

```
Per RFP request:
├─ Lambda orchestrator:        $0.0000083  (128 MB, 10 sec)
├─ 6 Lambda tools:             $0.00025   (per call)
├─ DynamoDB reads:             $0.00001   (small data)
├─ DynamoDB writes:            $0.00002   (scores, recommendations)
└─ S3 storage:                 $0.000025  (per RFP doc)

Total per request:             ~$0.0003

Monthly (100k requests):
├─ Lambda execution:           $30
├─ Tool Lambdas:               $25
├─ DynamoDB:                   $20
└─ S3:                         $5
────────────────────────
Total:                         ~$80
```

### After: AgentCore Runtime

```
Per RFP request:
├─ AgentCore Runtime:          $0.00024   (managed service)
├─ MCP Tool Calls (6):         $0.0001    (per call)
├─ Memory storage:             $0.00001   (DynamoDB)
├─ Observability:              $0.00002   (CW/X-Ray)
└─ S3 storage:                 $0.000025  (per RFP doc)

Total per request:             ~$0.0004

Monthly (100k requests):
├─ AgentCore Runtime:          $240
├─ Tool Lambdas:               $100
├─ DynamoDB:                   $30
├─ CloudWatch/X-Ray:           $50
└─ S3:                         $5
────────────────────────
Total:                         ~$425
```

**Cost increase:** ~$350/month for production-grade infrastructure
**Value:** Memory, observability, identity, approval gates, no timeouts, auto-scaling

---

