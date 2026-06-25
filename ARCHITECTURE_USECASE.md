# Supplier RFP Management Agent
## Use Case Architecture — AWS Bedrock AgentCore

---

## 1. Use Case Overview

| Field | Detail |
|-------|--------|
| **Use Case Name** | Automated Supplier RFP Management |
| **Industry** | Automotive & Manufacturing Procurement |
| **AI Framework** | Strands Agents SDK |
| **Model** | Amazon Nova Pro (amazon.nova-pro-v1:0) |
| **Region** | us-east-1 |
| **AgentCore Runtime** | rfpsupplieragent-ODy0E42s5l |
| **AgentCore Gateway** | rfpmcpgateway-2lhpouzcif |

---

## 2. Problem Statement

Traditional procurement processes require procurement managers to:
- Manually search supplier databases
- Manually write RFP documents
- Manually email suppliers
- Manually collect and compare proposals
- Manually score and rank suppliers
- Manually generate recommendation reports

This takes **days to weeks** and is error-prone.

**This agent automates the entire process end-to-end in minutes.**

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AWS BEDROCK AGENTCORE                               │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    AGENTCORE RUNTIME                                │   │
│   │              rfpsupplieragent-ODy0E42s5l                           │   │
│   │                                                                     │   │
│   │   ┌─────────────────────────────────────────────────────────────┐   │   │
│   │   │            ARM64 Container (python:3.12-slim)               │   │   │
│   │   │                                                             │   │   │
│   │   │   ┌─────────────────────────────────────────────────────┐   │   │   │
│   │   │   │          Strands Agent Orchestrator                  │   │   │   │
│   │   │   │          agentcore_orchestrator.py                   │   │   │   │
│   │   │   │                                                     │   │   │   │
│   │   │   │   Model: Amazon Nova Pro (amazon.nova-pro-v1:0)     │   │   │   │
│   │   │   │   Port: 8080  │  Health: GET /ping → 200            │   │   │   │
│   │   │   │   Invoke: POST / → {"message": "..."}               │   │   │   │
│   │   │   └─────────────────────────────────────────────────────┘   │   │   │
│   │   └─────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    AGENTCORE GATEWAY                                │   │
│   │              rfpmcpgateway-2lhpouzcif                              │   │
│   │              (MCP Protocol — 6 registered tools)                   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   AgentCore Capabilities Used:                                              │
│   ✅ Runtime      — Managed ARM64 container hosting                         │
│   ✅ Gateway      — MCP tool registration & routing                         │
│   ✅ Observability — CloudWatch logs & traces                               │
│   ✅ Identity     — Workload identity (IAM role-based)                      │
│   ✅ Policy       — Human approval gate (approval_required flag)            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Complete System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         SUPPLIER RFP MANAGEMENT SYSTEM                               │
└──────────────────────────────────────────────────────────────────────────────────────┘

  PROCUREMENT MANAGER
  ┌─────────────────┐
  │ Natural Language │
  │ "We need 500    │
  │  brake sensors  │
  │  by Sept 2026"  │
  └────────┬────────┘
           │ invoke-agent-runtime API
           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          AWS BEDROCK AGENTCORE RUNTIME                              │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                    STRANDS AGENT (Amazon Nova Pro)                          │    │
│  │                                                                             │    │
│  │   Receives message → Plans workflow → Calls tools in order → Returns result │    │
│  │                                                                             │    │
│  │   Tool 1          Tool 2          Tool 3          Tool 4                   │    │
│  │   supplier_lookup → rfp_generator → email_dispatch → proposal_fetch        │    │
│  │                                                                             │    │
│  │                         Tool 5          Tool 6                             │    │
│  │                         scoring    →    recommendation                     │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│          │              │              │              │         │         │          │
└──────────┼──────────────┼──────────────┼──────────────┼─────────┼─────────┼──────────┘
           │ boto3        │ boto3        │ boto3        │boto3    │boto3    │boto3
           ▼              ▼              ▼              ▼         ▼         ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐  ┌──────────┐ ┌──────┐ ┌──────────┐
    │LAMBDA    │   │LAMBDA    │   │LAMBDA    │  │LAMBDA    │ │LAMBDA│ │LAMBDA    │
    │rfp-      │   │rfp-rfp-  │   │rfp-email-│  │rfp-      │ │rfp-  │ │rfp-      │
    │supplier- │   │generator │   │dispatch  │  │proposal- │ │scori-│ │recommenda│
    │lookup    │   │          │   │          │  │fetch     │ │ng    │ │tion      │
    │(x86_64)  │   │(x86_64)  │   │(x86_64)  │  │(x86_64)  │ │(x86) │ │(x86_64)  │
    └────┬─────┘   └────┬─────┘   └────┬─────┘  └────┬─────┘ └──┬───┘ └────┬─────┘
         │              │              │              │           │          │
         ▼              ▼         ▼    ▼              ▼           ▼          ▼
   ┌──────────┐  ┌──────────┐ ┌─────┐ ┌────────┐ ┌──────────┐ ┌──────┐  ┌──────────┐
   │DynamoDB  │  │S3 Bucket │ │SES  │ │DynamoDB│ │DynamoDB  │ │Dyna  │  │S3 Bucket │
   │rfp-      │  │rfp-docs- │ │Mock │ │rfp-    │ │rfp-      │ │moDB  │  │recommenda│
   │suppliers │  │quadrasys │ │Mode │ │proposals│ │proposals │ │rfp-  │  │tions/    │
   │          │  │.docx file│ │     │ │        │ │          │ │scores│  │.docx file│
   └──────────┘  └──────────┘ └──┬──┘ └────────┘ └──────────┘ └──────┘  └──────────┘
                                  │
                    ┌─────────────┘
                    ▼
              ┌──────────┐
              │Suppliers │
              │(via email│
              │with form │
              │link)     │
              └────┬─────┘
                   │ Submit Google Form
                   ▼
           ┌──────────────┐
           │Google Forms  │
           │ (per RFP)    │
           └──────┬───────┘
                  │ Apps Script Webhook
                  ▼
           ┌──────────────┐      ┌──────────┐
           │LAMBDA        │─────▶│DynamoDB  │
           │google_form_  │      │rfp-      │
           │lambda        │      │proposals │
           └──────────────┘      └──────────┘
```

---

## 5. Step-by-Step Agent Workflow

```
STEP 1 — INPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Procurement Manager types:
  "We need 500 brake sensors by 2026-09-30.
   Specs: ABS wheel speed sensor, IP67, CAN bus.
   Category: sensors."

  → Sent via AWS CLI / SDK to AgentCore Runtime


STEP 2 — SUPPLIER LOOKUP (Tool 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Agent calls: supplier_lookup(category="sensors")
  Lambda queries: DynamoDB rfp-suppliers
  Returns: Top 5 suppliers by rating

  Example output:
  ┌────────┬──────────────────────┬────────┬──────────────────────────┐
  │ ID     │ Name                 │ Rating │ Email                    │
  ├────────┼──────────────────────┼────────┼──────────────────────────┤
  │ SUP005 │ Bosch Auto Parts     │  4.9   │ bosch@supplier.com       │
  │ SUP003 │ Continental Sensors  │  4.7   │ continental@supplier.com │
  │ SUP001 │ Delphi Technologies  │  4.5   │ delphi@supplier.com      │
  └────────┴──────────────────────┴────────┴──────────────────────────┘


STEP 3 — RFP DOCUMENT GENERATION (Tool 2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Agent calls: rfp_generator(rfp_id, requirement, supplier_ids)
  Lambda generates: Word .docx file with:
    - RFP ID header
    - Component specs table
    - Evaluation criteria (30/30/20/20)
    - Submission instructions
    - Google Form link
  Saves to: S3 rfp-documents-quadrasystems/rfp-documents/
  Returns: presigned URL (valid 7 days)

  Stored in DynamoDB rfp-requests:
  ┌──────────────────────┬────────────┬──────────┐
  │ RequestID            │ Status     │ DocxURL  │
  ├──────────────────────┼────────────┼──────────┤
  │ RFP-20260619-F8A56AB │ Active     │ https://…│
  └──────────────────────┴────────────┴──────────┘


STEP 4 — EMAIL DISPATCH (Tool 3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Agent calls: email_dispatch(rfp_id, supplier_emails,
                               google_form_url, docx_presigned_url)
  Lambda sends (mock mode): Email to each supplier containing:
    - RFP details (component, quantity, deadline)
    - Link to RFP .docx document
    - Link to Google Form for proposal submission
    - Evaluation criteria reminder

  [SES mock mode = TRUE — no real emails sent in demo]


STEP 5 — SUPPLIER PROPOSAL SUBMISSION (Google Form)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Supplier opens Google Form link
  Fills in: price, lead time, quality score, compliance docs
  Clicks Submit
  → Google Apps Script fires POST to google_form_lambda
  → Proposal stored in DynamoDB rfp-proposals


STEP 6 — PROPOSAL FETCH (Tool 4)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Agent calls: proposal_fetch(rfp_id, supplier_ids)
  Lambda reads: DynamoDB rfp-proposals
  Auto-generates mock proposals if table is empty (for demo)

  Example proposals:
  ┌────────┬────────┬───────────────┬──────────────┬─────────────┐
  │Supplier│ Price  │ Delivery Days │ Quality Score│ Compliance  │
  ├────────┼────────┼───────────────┼──────────────┼─────────────┤
  │ SUP005 │ $3,056 │     31 days   │     96/100   │ ISO 9001    │
  │ SUP003 │ $3,464 │     34 days   │     84/100   │ IATF 16949  │
  │ SUP001 │ $2,800 │     28 days   │     88/100   │ ISO 9001    │
  └────────┴────────┴───────────────┴──────────────┴─────────────┘


STEP 7 — SCORING (Tool 5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Agent calls: scoring(rfp_id, proposals)
  Lambda applies weighted formula:

  ┌─────────────────┬────────┬──────────────────────────────────┐
  │ Criteria        │ Weight │ How Scored                       │
  ├─────────────────┼────────┼──────────────────────────────────┤
  │ Price           │  30%   │ Lower price = higher score       │
  │ Quality Score   │  30%   │ Direct score (0-100)             │
  │ Delivery Time   │  20%   │ Fewer days = higher score        │
  │ Compliance      │  20%   │ Has certifications = 90 pts      │
  └─────────────────┴────────┴──────────────────────────────────┘

  Risk flags identified:
  - High Price (> $3,000)
  - Long Delivery (> 45 days)
  - Compliance Gap (no certifications)
  - Quality Concern (score < 80)

  Scores saved to DynamoDB rfp-scores


STEP 8 — RECOMMENDATION (Tool 6)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Agent calls: recommendation(rfp_id, scored_proposals)
  Lambda generates:
    - Top 2 ranked suppliers
    - .docx Recommendation Report (saved to S3)
    - approval_required flag

  Recommendation Report contains:
    - Full scores table per supplier
    - Risk flags analysis
    - Reasoning per supplier
    - Approval decision

  DynamoDB rfp-requests updated:
  ┌────────────────────────┬────────────────────┬───────────────┐
  │ RequestID              │ Status             │ AwardedTo     │
  ├────────────────────────┼────────────────────┼───────────────┤
  │ RFP-20260619-F8A56AB   │ pending_approval   │ (pending)     │
  │   (if risk flags)      │                    │               │
  │ RFP-20260619-XXXXXXXX  │ awarded            │ SUP005        │
  │   (if no risk flags)   │                    │               │
  └────────────────────────┴────────────────────┴───────────────┘


STEP 9 — HUMAN APPROVAL GATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  If approval_required = True:
    Agent responds: "HUMAN APPROVAL REQUIRED"
    Procurement manager reviews recommendation .docx
    Manager approves → DynamoDB updated to 'awarded'

  If approval_required = False:
    Agent auto-awards contract
    DynamoDB updated to 'awarded' automatically


STEP 10 — FINAL OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Agent returns to procurement manager:

  ✅ RFP ID: RFP-20260619-FCBAF14D
  📄 RFP Document: https://s3.amazonaws.com/...docx
  📊 Recommendation Report: https://s3.amazonaws.com/...docx

  🥇 Rank 1: SUP005 — Score: 66.3/100
     Risk: High Price — RECOMMENDED with review

  🥈 Rank 2: SUP003 — Score: 59.0/100
     Risk: High Price — BACKUP option

  ⚠️ HUMAN APPROVAL REQUIRED before contract award
```

---

## 6. AWS Services Used

```
┌────────────────────────────────────────────────────────────────────────┐
│                      AWS SERVICES ARCHITECTURE                         │
├────────────────────────┬───────────────────────────────────────────────┤
│ Service                │ Role                                          │
├────────────────────────┼───────────────────────────────────────────────┤
│ Bedrock AgentCore      │ Hosts the AI agent runtime (ARM64 container)  │
│ Runtime                │ Manages lifecycle, scaling, observability      │
├────────────────────────┼───────────────────────────────────────────────┤
│ Bedrock AgentCore      │ MCP protocol gateway for 6 tool functions     │
│ Gateway                │ Routes agent tool calls to Lambda             │
├────────────────────────┼───────────────────────────────────────────────┤
│ Amazon Bedrock         │ amazon.nova-pro-v1:0 foundation model         │
│                        │ Powers the agent's reasoning & planning       │
├────────────────────────┼───────────────────────────────────────────────┤
│ AWS Lambda (x6)        │ Individual tool functions (x86_64 containers) │
│                        │ supplier-lookup, rfp-generator, email,        │
│                        │ proposal-fetch, scoring, recommendation       │
├────────────────────────┼───────────────────────────────────────────────┤
│ AWS Lambda (x1)        │ google_form_lambda — webhook receiver         │
│                        │ Receives Google Form submissions              │
├────────────────────────┼───────────────────────────────────────────────┤
│ Amazon DynamoDB (x4)   │ rfp-suppliers — supplier master data          │
│                        │ rfp-requests  — RFP lifecycle tracking        │
│                        │ rfp-proposals — supplier proposal storage     │
│                        │ rfp-scores    — scoring results               │
├────────────────────────┼───────────────────────────────────────────────┤
│ Amazon S3              │ rfp-documents-quadrasystems bucket            │
│                        │ Stores RFP .docx files & recommendation .docx │
│                        │ Presigned URLs (7-day access)                 │
├────────────────────────┼───────────────────────────────────────────────┤
│ Amazon SES             │ Email dispatch (mock mode for demo)           │
│                        │ Sends RFP + Google Form link to suppliers     │
├────────────────────────┼───────────────────────────────────────────────┤
│ Amazon ECR             │ Docker image registry                         │
│                        │ ARM64 runtime image + 6 Lambda images         │
├────────────────────────┼───────────────────────────────────────────────┤
│ AWS IAM                │ rfp-agent-runtime-role                        │
│                        │ Grants runtime access to Lambda, DynamoDB, S3 │
├────────────────────────┼───────────────────────────────────────────────┤
│ Amazon CloudWatch      │ Runtime logs, Lambda logs, traces             │
│                        │ Full observability across all components      │
├────────────────────────┼───────────────────────────────────────────────┤
│ AWS CodeBuild          │ ARM64 Docker image builds                     │
│                        │ rfp-agent-arm64-build project                 │
├────────────────────────┼───────────────────────────────────────────────┤
│ API Gateway            │ HTTP endpoint for google_form_lambda          │
│ (planned)              │ Receives Google Apps Script webhooks          │
└────────────────────────┴───────────────────────────────────────────────┘
```

---

## 7. AgentCore Capabilities Highlighted

```
┌─────────────────────────────────────────────────────────────────────┐
│                  AGENTCORE CAPABILITIES USED                        │
├─────────────────┬───────────────────────────────────────────────────┤
│ Capability      │ How It's Used in This System                      │
├─────────────────┼───────────────────────────────────────────────────┤
│ Runtime         │ Hosts the Strands agent as a managed ARM64        │
│                 │ container. Handles scaling, health checks,        │
│                 │ and lifecycle management automatically.           │
├─────────────────┼───────────────────────────────────────────────────┤
│ Gateway (MCP)   │ 6 Lambda tools registered as MCP endpoints.      │
│                 │ Provides standardized tool interface for          │
│                 │ the Strands agent to discover and call tools.     │
├─────────────────┼───────────────────────────────────────────────────┤
│ Observability   │ All agent steps, tool calls, and Lambda           │
│                 │ invocations logged to CloudWatch.                 │
│                 │ Full trace from input to recommendation.          │
├─────────────────┼───────────────────────────────────────────────────┤
│ Identity        │ Workload identity (IAM role) automatically        │
│                 │ grants the runtime secure access to DynamoDB,    │
│                 │ S3, Lambda, and Bedrock without hardcoded keys.   │
├─────────────────┼───────────────────────────────────────────────────┤
│ Policy /        │ approval_required flag triggers human review      │
│ Human Approval  │ gate before contract is awarded.                  │
│                 │ Prevents auto-award when risk flags exist.        │
└─────────────────┴───────────────────────────────────────────────────┘
```

---

## 8. Data Flow Summary

```
INPUT                    PROCESSING                    OUTPUT
─────                    ──────────                    ──────

Natural language    →    Strands Agent           →    Structured response
requirement              (Nova Pro reasoning)          with:
                              │                        - RFP ID
                         6 tool calls                  - .docx RFP link
                         in sequence:                  - .docx report link
                              │                        - Top 2 suppliers
                    ┌─────────┴──────────┐             - Scores & flags
                    │                    │             - Approval decision
               DynamoDB              S3 Bucket
               (4 tables)            (.docx files)
```

---

## 9. Deployment Architecture

```
GITHUB REPOSITORY (AbilashEG/rfp-management)
         │
         │ git push
         ▼
AWS CODEBUILD (rfp-agent-arm64-build)
  ARM_CONTAINER → ARM64 native build
         │
         │ docker push
         ▼
AMAZON ECR (rfp-agent repository)
  Tags:
  ├── orchestrator-agentcore-arm64  (AgentCore Runtime)
  ├── supplier_lookup               (Lambda tool)
  ├── rfp_generator                 (Lambda tool)
  ├── email_dispatch                (Lambda tool)
  ├── proposal_fetch                (Lambda tool)
  ├── scoring                       (Lambda tool)
  └── recommendation                (Lambda tool)
         │
         ├── ARM64 image → AgentCore Runtime update
         │
         └── x86_64 images → Lambda function updates
```

---

## 10. Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                  IAM SECURITY MODEL                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  rfp-agent-runtime-role                             │
│  ├── lambda:InvokeFunction (6 Lambda functions)     │
│  ├── dynamodb:GetItem, PutItem, Scan, UpdateItem    │
│  │   (rfp-suppliers, rfp-requests, rfp-proposals,   │
│  │    rfp-scores)                                   │
│  ├── s3:PutObject, GetObject                        │
│  │   (rfp-documents-quadrasystems)                  │
│  ├── bedrock:InvokeModel                            │
│  │   (amazon.nova-pro-v1:0)                         │
│  └── logs:PutLogEvents (CloudWatch)                 │
│                                                     │
│  No hardcoded credentials anywhere                  │
│  All auth via IAM role assumption                   │
│  S3 access via presigned URLs (7-day expiry)        │
└─────────────────────────────────────────────────────┘
```

---

## 11. Business Value

| Metric | Before (Manual) | After (Agent) |
|--------|----------------|---------------|
| Time to send RFP | 2-3 days | < 2 minutes |
| Supplier search | Manual database lookup | Automated DynamoDB query |
| RFP document | Manual Word creation | Auto-generated .docx |
| Proposal scoring | Manual spreadsheet | Automated weighted scoring |
| Recommendation report | Manual preparation | Auto-generated .docx |
| Audit trail | Email threads | Full DynamoDB history |
| Human involvement | Every step | Only final approval |

---

## 12. GitHub Repository Structure

```
rfp-management/
├── RFP-main/
│   ├── agentcore_orchestrator.py    # Strands Agent + HTTP server
│   ├── requirements.txt             # Python dependencies
│   ├── config.py                    # Region, table names, S3 bucket
│   └── lambda/
│       ├── supplier_lookup_lambda.py     # Tool 1: Find suppliers
│       ├── rfp_generator_lambda.py       # Tool 2: Generate .docx RFP
│       ├── email_dispatch_lambda.py      # Tool 3: Send emails
│       ├── proposal_fetch_lambda.py      # Tool 4: Fetch proposals
│       ├── scoring_lambda.py             # Tool 5: Score proposals
│       ├── recommendation_lambda.py      # Tool 6: Recommend + .docx
│       └── google_form_lambda.py         # Webhook: Google Form → DynamoDB
├── Dockerfile                       # ARM64 AgentCore Runtime image
├── buildspec.yml                    # CodeBuild ARM64 build spec
├── agentcore.yaml                   # AgentCore configuration
└── cloudformation-deployment.yaml   # Full infrastructure as code
```

---

*Architecture Version: 2.0 | Date: June 2026 | Region: us-east-1*
