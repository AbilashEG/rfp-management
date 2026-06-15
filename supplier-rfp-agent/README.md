# Supplier RFP Management — Agentic AI Backend

Production-grade, fully serverless Agentic AI system for Supplier RFP Management
in the Automotive / Manufacturing industry.
Built on **AWS Bedrock AgentCore** using the **Strands Agents SDK**. Zero EC2.

---

## Architecture

```
API Gateway → Lambda (rfp_agent_handler) → Strands Agent → 6 Tools → DynamoDB / S3 / SES
                                                         ↕
                                              Amazon Bedrock (Claude Sonnet 4.5)
```

**AgentCore Pillars:** Runtime · Memory · Gateway (MCP) · Observability · Policy · Identity

---

## Project Structure

```
supplier-rfp-agent/
├── config.py                  # Single source of truth for all config
├── requirements.txt
├── README.md
├── setup/
│   ├── create_tables.py       # Creates all 4 DynamoDB tables
│   ├── seed_data.py           # Seeds 8 mock automotive suppliers
│   └── create_s3_bucket.py    # Creates S3 bucket for RFP docs
├── tools/
│   ├── supplier_lookup_tool.py
│   ├── rfp_generator_tool.py
│   ├── email_dispatch_tool.py
│   ├── proposal_fetch_tool.py
│   ├── scoring_tool.py
│   └── recommendation_tool.py
├── agent/
│   ├── rfp_agent.py           # Strands Agent wiring all 6 tools
│   ├── system_prompt.py
│   └── agent_runner.py        # Local test runner
├── lambda/
│   ├── rfp_agent_handler.py   # Lambda entry point
│   └── Dockerfile
├── infra/
│   ├── app.py                 # CDK app entry
│   ├── dynamodb_tables.py
│   ├── s3_bucket.py
│   └── lambda_function.py
└── tests/
    ├── test_tools.py          # Unit tests (6 tools)
    └── test_agent_flow.py     # End-to-end lifecycle test
```

---

## Prerequisites

- AWS CLI configured (`aws configure`) — Region: `us-east-1`
- Python 3.12
- Node.js (for CDK)
- Docker (for Lambda container build)

```bash
pip install -r requirements.txt
npm install -g aws-cdk
```

---

## Execution Order

### Step 1 — Deploy Infrastructure

```bash
cd supplier-rfp-agent
cdk bootstrap aws://689050397154/us-east-1
cdk deploy --all --app "python infra/app.py"
```

### Step 2 — Seed Data

```bash
python setup/create_tables.py   # tables already exist — shows "already exists"
python setup/seed_data.py       # seeds 8 mock suppliers
```

### Step 3 — Build and Push Docker Image

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 689050397154.dkr.ecr.us-east-1.amazonaws.com

docker build -t supplier-rfp-agent -f lambda/Dockerfile .
docker tag  supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

### Step 4 — Fill AgentCore IDs in config.py

After creating AgentCore Memory and Runtime, update `config.py`:

```python
AGENTCORE_MEMORY_ID = "mem-xxxxxxxxxxxxxxxx"
AGENTCORE_AGENT_ID  = "agent-xxxxxxxxxxxxxxxx"
```

### Step 5 — Test Locally

```bash
python -m agent.agent_runner
```

### Step 6 — Run Tests

```bash
pip install moto pytest
pytest tests/ -v
```

---

## Agent Tool Flow

```
1. supplier_lookup_tool(category)          → finds active suppliers
2. rfp_generator_tool(specs, suppliers)    → creates RFP, saves to S3 + DynamoDB
3. email_dispatch_tool(rfp_id, suppliers)  → sends/mocks RFP emails via SES
4. proposal_fetch_tool(rfp_id)             → fetches or auto-generates proposals
5. scoring_tool(proposals)                 → scores: Price 30% Quality 30% Delivery 20% Compliance 20%
6. recommendation_tool(scored)             → Top-2 recommendation + approval gate
```

---

## Scoring Weights

| Criterion   | Weight |
|-------------|--------|
| Price       | 30%    |
| Quality     | 30%    |
| Delivery    | 20%    |
| Compliance  | 20%    |

---

## Sample Test Output

```
SUPPLIER RFP MANAGEMENT AGENT — TEST RUN
============================================================
[Invoking supplier_lookup_tool] category=sensors → 3 suppliers found
[Invoking rfp_generator_tool]   RFP-20260612-A3F9B2C1 created → s3://rfp-documents-quadrasystems/rfp-docs/...
[Invoking email_dispatch_tool]  3 mock emails dispatched
[Invoking proposal_fetch_tool]  3 proposals fetched (mock-generated)
[Invoking scoring_tool]         3 proposals scored
[Invoking recommendation_tool]  Top-2: AutoSensor Global (88.5) · ElectroAuto Systems (72.1)

FINAL AGENT RESPONSE:
  ✅ Recommendation: AutoSensor Global — Score 88.5/100
  ⚠️ HUMAN APPROVAL REQUIRED (NexaComponents flagged: NO_CERTIFICATIONS)
```
