# KIRO PROJECT PROMPT
## Supplier RFP Management — Agentic AI Backend
### Phase 1: Backend Only (AWS Services + AgentCore)

---

## PROJECT CONTEXT

You are building a production-grade, fully serverless Agentic AI system
for Supplier RFP (Request for Proposal) Management in the
Automotive / Manufacturing industry. This is built on AWS Bedrock
AgentCore using the Strands Agents SDK. Zero EC2. All serverless.

This is a VP-level demo for Quadrasystems Pvt Ltd (AWS Partner).
The architecture must showcase all 6 AgentCore pillars:
Runtime, Memory, Gateway (MCP), Observability, Policy, Identity.

DO NOT generate any frontend code in this phase.
DO NOT use SAP, ERP, or any external enterprise system.
All data is mocked using DynamoDB tables you will create and seed.

---

## TECH STACK — EXACT VERSIONS

- **Runtime**: AWS Lambda (Python 3.12)
- **Agent Framework**: Strands Agents SDK (`strands-agents`, `strands-agents-tools`)
- **AgentCore**: Amazon Bedrock AgentCore (Runtime, Memory, Gateway, Observability, Policy, Identity)
- **LLM**: `anthropic.claude-sonnet-4-5` via Amazon Bedrock
- **Database**: Amazon DynamoDB (4 tables)
- **Storage**: Amazon S3
- **Email**: Amazon SES
- **Auth**: Amazon Cognito
- **Scheduling**: Amazon EventBridge
- **Monitoring**: Amazon CloudWatch
- **IaC**: AWS CDK (Python) — preferred. If CDK is complex for AgentCore, use boto3 setup scripts.
- **Region**: ap-south-1 (Mumbai)

---

## DYNAMODB TABLES — CREATE THESE EXACTLY

### Table 1: `rfp-suppliers`
- Partition Key: `supplier_id` (String)
- Attributes: `name`, `category`, `region`, `certifications` (List),
  `rating` (Number), `past_delivery_score` (Number),
  `contact_email`, `status` (active/inactive)

### Table 2: `rfp-requests`
- Partition Key: `rfp_id` (String)
- Sort Key: `created_at` (String, ISO timestamp)
- Attributes: `component_name`, `specs`, `quantity` (Number),
  `deadline`, `status` (draft/sent/evaluating/closed),
  `created_by`, `shortlisted_suppliers` (List)

### Table 3: `rfp-proposals`
- Partition Key: `proposal_id` (String)
- Sort Key: `rfp_id` (String)
- GSI: `rfp_id-index` on `rfp_id`
- Attributes: `supplier_id`, `price` (Number), `lead_time_days` (Number),
  `compliance_docs` (List), `quality_score` (Number),
  `submitted_at`, `status` (received/scored/shortlisted/rejected)

### Table 4: `rfp-scores`
- Partition Key: `score_id` (String)
- Sort Key: `proposal_id` (String)
- Attributes: `rfp_id`, `supplier_id`, `price_score` (Number),
  `quality_score` (Number), `delivery_score` (Number),
  `compliance_score` (Number), `total_score` (Number),
  `flags` (List), `recommendation` (String), `scored_at`

---

## SEED DATA — INSERT THIS INTO DYNAMODB

Seed `rfp-suppliers` with 8 mock suppliers:

```json
[
  {"supplier_id": "SUP001", "name": "BrakeTech Industries", "category": "brake_systems", "region": "Chennai", "certifications": ["ISO9001", "IATF16949"], "rating": 4.8, "past_delivery_score": 95, "contact_email": "rfp@braketech-mock.com", "status": "active"},
  {"supplier_id": "SUP002", "name": "PrecisionParts Co", "category": "brake_systems", "region": "Pune", "certifications": ["ISO9001"], "rating": 4.2, "past_delivery_score": 88, "contact_email": "rfp@precisionparts-mock.com", "status": "active"},
  {"supplier_id": "SUP003", "name": "AutoSensor Global", "category": "sensors", "region": "Bangalore", "certifications": ["ISO9001", "IATF16949", "ISO14001"], "rating": 4.9, "past_delivery_score": 98, "contact_email": "rfp@autosensor-mock.com", "status": "active"},
  {"supplier_id": "SUP004", "name": "SpeedMech Ltd", "category": "brake_systems", "region": "Mumbai", "certifications": ["ISO9001"], "rating": 3.8, "past_delivery_score": 72, "contact_email": "rfp@speedmech-mock.com", "status": "active"},
  {"supplier_id": "SUP005", "name": "NexaComponents", "category": "sensors", "region": "Hyderabad", "certifications": [], "rating": 3.5, "past_delivery_score": 65, "contact_email": "rfp@nexa-mock.com", "status": "active"},
  {"supplier_id": "SUP006", "name": "TitanForge Industries", "category": "structural_parts", "region": "Coimbatore", "certifications": ["ISO9001", "IATF16949"], "rating": 4.6, "past_delivery_score": 91, "contact_email": "rfp@titanforge-mock.com", "status": "active"},
  {"supplier_id": "SUP007", "name": "ElectroAuto Systems", "category": "sensors", "region": "Chennai", "certifications": ["ISO9001"], "rating": 4.1, "past_delivery_score": 84, "contact_email": "rfp@electroauto-mock.com", "status": "active"},
  {"supplier_id": "SUP008", "name": "OldParts Pvt Ltd", "category": "brake_systems", "region": "Delhi", "certifications": ["ISO9001"], "rating": 2.9, "past_delivery_score": 55, "contact_email": "rfp@oldparts-mock.com", "status": "active"}
]
```

---

## PROJECT FOLDER STRUCTURE — CREATE EXACTLY THIS

```
supplier-rfp-agent/
├── README.md
├── requirements.txt
├── setup/
│   ├── create_tables.py          # Creates all 4 DynamoDB tables
│   ├── seed_data.py              # Seeds supplier mock data
│   └── create_s3_bucket.py       # Creates S3 bucket for RFP docs
├── tools/
│   ├── __init__.py
│   ├── supplier_lookup_tool.py   # Tool 1: Query suppliers by category
│   ├── rfp_generator_tool.py     # Tool 2: Generate RFP document text
│   ├── email_dispatch_tool.py    # Tool 3: Send RFP via SES (mock mode)
│   ├── proposal_fetch_tool.py    # Tool 4: Fetch submitted proposals
│   ├── scoring_tool.py           # Tool 5: Score proposals multi-criteria
│   └── recommendation_tool.py   # Tool 6: Generate ranked recommendation
├── agent/
│   ├── __init__.py
│   ├── rfp_agent.py              # Main Strands Agent definition
│   ├── system_prompt.py          # Agent system prompt
│   └── agent_runner.py           # Local test runner
├── lambda/
│   ├── rfp_agent_handler.py      # Lambda entry point
│   └── Dockerfile                # For Lambda container deployment
├── infra/
│   ├── dynamodb_tables.py        # CDK stack for DynamoDB
│   ├── s3_bucket.py              # CDK stack for S3
│   ├── lambda_function.py        # CDK stack for Lambda
│   └── app.py                    # CDK app entry
├── tests/
│   ├── test_tools.py             # Unit tests per tool
│   └── test_agent_flow.py        # End-to-end flow test
└── config.py                     # All config: table names, region, bucket
```

---

## TASK 1 — CREATE `config.py`

```python
# config.py
REGION = "ap-south-1"
BEDROCK_MODEL_ID = "anthropic.claude-sonnet-4-5"

# DynamoDB
SUPPLIERS_TABLE = "rfp-suppliers"
REQUESTS_TABLE = "rfp-requests"
PROPOSALS_TABLE = "rfp-proposals"
SCORES_TABLE = "rfp-scores"

# S3
RFP_DOCS_BUCKET = "rfp-documents-quadrasystems"
RFP_DOCS_PREFIX = "rfp-docs/"

# SES
SES_SENDER_EMAIL = "rfp-agent@quadrasystems.com"
SES_MOCK_MODE = True  # Set False when SES is verified

# AgentCore
AGENTCORE_MEMORY_ID = ""     # Fill after AgentCore Memory creation
AGENTCORE_AGENT_ID = ""      # Fill after AgentCore Runtime creation

# Scoring Weights
PRICE_WEIGHT = 0.30
QUALITY_WEIGHT = 0.30
DELIVERY_WEIGHT = 0.20
COMPLIANCE_WEIGHT = 0.20
```

---

## TASK 2 — CREATE ALL 6 LAMBDA TOOLS

Each tool must follow the Strands SDK `@tool` decorator pattern.
Return type must always be a plain dict with a `status` key.

### Tool 1: `tools/supplier_lookup_tool.py`

```python
from strands import tool
import boto3
import json
from config import SUPPLIERS_TABLE, REGION
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb", region_name=REGION)

@tool
def supplier_lookup_tool(category: str, region: str = None) -> dict:
    """
    Queries DynamoDB to find active suppliers matching the given
    component category. Optionally filters by region.
    Returns list of matching suppliers with their ratings and certifications.
    
    Args:
        category: Component category to search (e.g. brake_systems, sensors)
        region: Optional AWS region filter for supplier location
    
    Returns:
        dict with suppliers list and count
    """
    table = dynamodb.Table(SUPPLIERS_TABLE)
    filter_expr = Attr("status").eq("active") & Attr("category").eq(category)
    if region:
        filter_expr = filter_expr & Attr("region").eq(region)
    
    response = table.scan(FilterExpression=filter_expr)
    suppliers = response.get("Items", [])
    
    return {
        "status": "success",
        "count": len(suppliers),
        "suppliers": suppliers,
        "category": category
    }
```

### Tool 2: `tools/rfp_generator_tool.py`

```python
from strands import tool
import boto3
import json
from datetime import datetime
from config import REQUESTS_TABLE, RFP_DOCS_BUCKET, RFP_DOCS_PREFIX, REGION
import uuid

dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

@tool
def rfp_generator_tool(
    component_name: str,
    specs: str,
    quantity: int,
    deadline: str,
    supplier_ids: list
) -> dict:
    """
    Generates a structured RFP document for the given component requirement.
    Saves it to S3 and creates an RFP record in DynamoDB.
    
    Args:
        component_name: Name of the component needed (e.g. brake sensors)
        specs: Technical specifications string
        quantity: Number of units required
        deadline: Delivery deadline (YYYY-MM-DD)
        supplier_ids: List of supplier IDs to send this RFP to
    
    Returns:
        dict with rfp_id, s3_path, and rfp document content
    """
    rfp_id = f"RFP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    created_at = datetime.utcnow().isoformat()
    
    rfp_content = f"""
REQUEST FOR PROPOSAL — {rfp_id}
Generated: {created_at}
========================================

COMPONENT REQUIREMENT
Component Name : {component_name}
Specifications : {specs}
Quantity       : {quantity} units
Deadline       : {deadline}

SUBMISSION REQUIREMENTS
1. Unit price per component (INR)
2. Lead time in business days
3. Quality certifications held (ISO9001, IATF16949, etc.)
4. Past delivery performance metrics
5. Minimum order quantity
6. Warranty terms

EVALUATION CRITERIA
- Price          : 30%
- Quality Score  : 30%
- Delivery Time  : 20%
- Compliance     : 20%

Submit proposals via the supplier portal by {deadline}.
RFP Reference ID: {rfp_id}
    """.strip()

    s3_key = f"{RFP_DOCS_PREFIX}{rfp_id}.txt"
    try:
        s3.put_object(
            Bucket=RFP_DOCS_BUCKET,
            Key=s3_key,
            Body=rfp_content.encode("utf-8"),
            ContentType="text/plain"
        )
        s3_path = f"s3://{RFP_DOCS_BUCKET}/{s3_key}"
    except Exception as e:
        s3_path = f"mock-s3://{s3_key}"

    table = dynamodb.Table(REQUESTS_TABLE)
    table.put_item(Item={
        "rfp_id": rfp_id,
        "created_at": created_at,
        "component_name": component_name,
        "specs": specs,
        "quantity": quantity,
        "deadline": deadline,
        "status": "draft",
        "created_by": "rfp-agent",
        "shortlisted_suppliers": supplier_ids,
        "s3_path": s3_path
    })

    return {
        "status": "success",
        "rfp_id": rfp_id,
        "s3_path": s3_path,
        "rfp_content": rfp_content,
        "supplier_count": len(supplier_ids)
    }
```

### Tool 3: `tools/email_dispatch_tool.py`

```python
from strands import tool
import boto3
from config import SES_SENDER_EMAIL, SES_MOCK_MODE, REGION, SUPPLIERS_TABLE
from boto3.dynamodb.conditions import Key

ses = boto3.client("ses", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)

@tool
def email_dispatch_tool(rfp_id: str, supplier_ids: list, rfp_content: str) -> dict:
    """
    Dispatches RFP email to each supplier in the list.
    In mock mode, logs the email without actually sending.
    In live mode, sends via Amazon SES.
    
    Args:
        rfp_id: The RFP reference ID
        supplier_ids: List of supplier IDs to email
        rfp_content: The full RFP document text to include in email
    
    Returns:
        dict with dispatch results per supplier
    """
    table = dynamodb.Table(SUPPLIERS_TABLE)
    results = []

    for supplier_id in supplier_ids:
        response = table.get_item(Key={"supplier_id": supplier_id})
        supplier = response.get("Item", {})
        email = supplier.get("contact_email", "unknown@mock.com")
        name = supplier.get("name", supplier_id)

        if SES_MOCK_MODE:
            results.append({
                "supplier_id": supplier_id,
                "supplier_name": name,
                "email": email,
                "status": "mock_sent",
                "message": f"[MOCK] RFP {rfp_id} would be sent to {email}"
            })
        else:
            try:
                ses.send_email(
                    Source=SES_SENDER_EMAIL,
                    Destination={"ToAddresses": [email]},
                    Message={
                        "Subject": {"Data": f"RFP Invitation: {rfp_id}"},
                        "Body": {"Text": {"Data": rfp_content}}
                    }
                )
                results.append({
                    "supplier_id": supplier_id,
                    "supplier_name": name,
                    "email": email,
                    "status": "sent"
                })
            except Exception as e:
                results.append({
                    "supplier_id": supplier_id,
                    "email": email,
                    "status": "failed",
                    "error": str(e)
                })

    return {
        "status": "success",
        "rfp_id": rfp_id,
        "dispatched": len([r for r in results if r["status"] in ["sent", "mock_sent"]]),
        "results": results
    }
```

### Tool 4: `tools/proposal_fetch_tool.py`

```python
from strands import tool
import boto3
from config import PROPOSALS_TABLE, REGION
from boto3.dynamodb.conditions import Attr
from datetime import datetime, timedelta
import uuid
import random

dynamodb = boto3.resource("dynamodb", region_name=REGION)

@tool
def proposal_fetch_tool(rfp_id: str, supplier_ids: list) -> dict:
    """
    Fetches submitted proposals for the given RFP from DynamoDB.
    If no proposals exist yet (demo mode), auto-generates mock proposals
    for the provided supplier IDs so the demo can continue.
    
    Args:
        rfp_id: The RFP ID to fetch proposals for
        supplier_ids: Expected supplier IDs (used for mock generation)
    
    Returns:
        dict with proposals list
    """
    table = dynamodb.Table(PROPOSALS_TABLE)
    response = table.scan(
        FilterExpression=Attr("rfp_id").eq(rfp_id)
    )
    proposals = response.get("Items", [])

    if not proposals:
        # Demo mode: auto-generate mock proposals
        mock_prices = {"SUP001": 850, "SUP002": 720, "SUP003": 940,
                       "SUP004": 650, "SUP005": 590, "SUP006": 880,
                       "SUP007": 810, "SUP008": 480}
        mock_leads  = {"SUP001": 14, "SUP002": 21, "SUP003": 10,
                       "SUP004": 28, "SUP005": 35, "SUP006": 18,
                       "SUP007": 22, "SUP008": 45}
        mock_quality = {"SUP001": 92, "SUP002": 85, "SUP003": 97,
                        "SUP004": 70, "SUP005": 62, "SUP006": 90,
                        "SUP007": 83, "SUP008": 50}

        for sid in supplier_ids:
            proposal_id = f"PROP-{str(uuid.uuid4())[:8].upper()}"
            item = {
                "proposal_id": proposal_id,
                "rfp_id": rfp_id,
                "supplier_id": sid,
                "price": mock_prices.get(sid, random.randint(500, 1000)),
                "lead_time_days": mock_leads.get(sid, random.randint(10, 45)),
                "quality_score": mock_quality.get(sid, random.randint(50, 98)),
                "compliance_docs": ["ISO9001"] if sid not in ["SUP005", "SUP008"] else [],
                "submitted_at": datetime.utcnow().isoformat(),
                "status": "received"
            }
            table.put_item(Item=item)
            proposals.append(item)

    return {
        "status": "success",
        "rfp_id": rfp_id,
        "proposal_count": len(proposals),
        "proposals": proposals
    }
```

### Tool 5: `tools/scoring_tool.py`

```python
from strands import tool
import boto3
from config import SCORES_TABLE, REGION
from datetime import datetime
import uuid

dynamodb = boto3.resource("dynamodb", region_name=REGION)

PRICE_WEIGHT    = 0.30
QUALITY_WEIGHT  = 0.30
DELIVERY_WEIGHT = 0.20
COMPLIANCE_WEIGHT = 0.20

@tool
def scoring_tool(rfp_id: str, proposals: list) -> dict:
    """
    Scores each proposal using weighted multi-criteria scoring:
    Price 30%, Quality 30%, Delivery 20%, Compliance 20%.
    Flags risks: expired certs, poor delivery history, price anomalies.
    Saves scores to rfp-scores DynamoDB table.
    
    Args:
        rfp_id: The RFP ID being evaluated
        proposals: List of proposal dicts from proposal_fetch_tool
    
    Returns:
        dict with scored proposals, flags, and ranked list
    """
    if not proposals:
        return {"status": "error", "message": "No proposals to score"}

    prices   = [float(p.get("price", 999999)) for p in proposals]
    leads    = [float(p.get("lead_time_days", 99)) for p in proposals]
    min_p, max_p = min(prices), max(prices)
    min_l, max_l = min(leads), max(leads)

    table = dynamodb.Table(SCORES_TABLE)
    scored = []

    for p in proposals:
        price    = float(p.get("price", 999999))
        lead     = float(p.get("lead_time_days", 99))
        quality  = float(p.get("quality_score", 0))
        comp_docs = p.get("compliance_docs", [])

        price_score    = ((max_p - price) / (max_p - min_p + 1)) * 100
        delivery_score = ((max_l - lead) / (max_l - min_l + 1)) * 100
        quality_score  = quality
        compliance_score = 100 if len(comp_docs) >= 2 else (50 if len(comp_docs) == 1 else 0)

        total = (
            price_score    * PRICE_WEIGHT +
            quality_score  * QUALITY_WEIGHT +
            delivery_score * DELIVERY_WEIGHT +
            compliance_score * COMPLIANCE_WEIGHT
        )

        flags = []
        if len(comp_docs) == 0:
            flags.append("NO_CERTIFICATIONS — High compliance risk")
        if lead > 30:
            flags.append(f"LONG_LEAD_TIME — {lead} days exceeds 30-day threshold")
        if price < (min_p * 0.6):
            flags.append("PRICE_ANOMALY — Price unusually low, verify quality")
        if quality < 70:
            flags.append(f"LOW_QUALITY_SCORE — {quality}/100 below acceptable threshold")

        score_id = f"SCORE-{str(uuid.uuid4())[:8].upper()}"
        score_item = {
            "score_id": score_id,
            "proposal_id": p["proposal_id"],
            "rfp_id": rfp_id,
            "supplier_id": p["supplier_id"],
            "price_score":       round(price_score, 2),
            "quality_score":     round(quality_score, 2),
            "delivery_score":    round(delivery_score, 2),
            "compliance_score":  round(compliance_score, 2),
            "total_score":       round(total, 2),
            "flags":             flags,
            "recommendation":    "shortlist" if total >= 70 and not flags else "review",
            "scored_at":         datetime.utcnow().isoformat()
        }
        table.put_item(Item=score_item)
        scored.append({**score_item, "supplier_name": p.get("supplier_id")})

    scored.sort(key=lambda x: x["total_score"], reverse=True)

    return {
        "status": "success",
        "rfp_id": rfp_id,
        "scored_count": len(scored),
        "scored_proposals": scored,
        "top_supplier_id": scored[0]["supplier_id"] if scored else None
    }
```

### Tool 6: `tools/recommendation_tool.py`

```python
from strands import tool
import boto3
from config import SCORES_TABLE, SUPPLIERS_TABLE, REGION
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb", region_name=REGION)

@tool
def recommendation_tool(rfp_id: str, scored_proposals: list) -> dict:
    """
    Generates final ranked supplier recommendation based on scores.
    Returns Top 2 suppliers with full reasoning and risk summary.
    Flags any proposals that require human review before award.
    This tool output triggers the AgentCore Policy human approval gate.
    
    Args:
        rfp_id: The RFP ID
        scored_proposals: List of scored proposal dicts from scoring_tool
    
    Returns:
        dict with top2 recommendation, reasoning, flags, and approval_required flag
    """
    if not scored_proposals:
        return {"status": "error", "message": "No scored proposals provided"}

    sup_table = dynamodb.Table(SUPPLIERS_TABLE)
    top2 = scored_proposals[:2]
    recommendation_lines = []
    all_flags = []
    approval_required = False

    for rank, item in enumerate(top2, 1):
        sup_resp = sup_table.get_item(Key={"supplier_id": item["supplier_id"]})
        supplier = sup_resp.get("Item", {})
        flags = item.get("flags", [])
        all_flags.extend(flags)

        if flags:
            approval_required = True

        recommendation_lines.append({
            "rank": rank,
            "supplier_id": item["supplier_id"],
            "supplier_name": supplier.get("name", item["supplier_id"]),
            "region": supplier.get("region", "Unknown"),
            "total_score": item["total_score"],
            "price_score": item["price_score"],
            "quality_score": item["quality_score"],
            "delivery_score": item["delivery_score"],
            "compliance_score": item["compliance_score"],
            "certifications": supplier.get("certifications", []),
            "past_delivery": supplier.get("past_delivery_score", "N/A"),
            "flags": flags,
            "recommendation": item["recommendation"],
            "reasoning": (
                f"Ranked #{rank} with overall score {item['total_score']:.1f}/100. "
                f"Strong in: "
                f"{'quality' if item['quality_score'] > 80 else ''} "
                f"{'price' if item['price_score'] > 70 else ''} "
                f"{'delivery' if item['delivery_score'] > 70 else ''}. "
                + (f"RISKS: {'; '.join(flags)}" if flags else "No major risks identified.")
            )
        })

    return {
        "status": "success",
        "rfp_id": rfp_id,
        "top_2_recommendations": recommendation_lines,
        "all_flags": all_flags,
        "approval_required": approval_required,
        "approval_message": (
            "⚠️ HUMAN APPROVAL REQUIRED — One or more flagged risks detected. "
            "Procurement manager must review before contract award."
            if approval_required else
            "✅ No critical flags. Proceed to contract award pending manager confirmation."
        ),
        "total_evaluated": len(scored_proposals)
    }
```

---

## TASK 3 — CREATE THE STRANDS AGENT

### `agent/system_prompt.py`

```python
SYSTEM_PROMPT = """
You are an intelligent Supplier RFP Management Agent for the
Automotive and Manufacturing industry.

Your job is to autonomously manage the full RFP lifecycle:
1. Understand the procurement manager's component requirement
2. Find matching suppliers from the database
3. Generate a formal RFP document
4. Dispatch the RFP to shortlisted suppliers via email
5. Collect and evaluate submitted proposals
6. Score each proposal on price, quality, delivery, and compliance
7. Recommend the top 2 suppliers with full reasoning
8. Flag any risks and trigger human approval if needed

RULES:
- Always use supplier_lookup_tool first to find matching suppliers
- Always generate an RFP via rfp_generator_tool before dispatching
- Always score ALL proposals before recommending
- NEVER award a contract without calling recommendation_tool
- If approval_required is True in recommendation output, 
  always state clearly that human sign-off is needed
- Be precise with numbers, scores, and supplier names
- Summarize your reasoning clearly after each major step
"""
```

### `agent/rfp_agent.py`

```python
from strands import Agent
from strands_tools import use_aws

from tools.supplier_lookup_tool import supplier_lookup_tool
from tools.rfp_generator_tool import rfp_generator_tool
from tools.email_dispatch_tool import email_dispatch_tool
from tools.proposal_fetch_tool import proposal_fetch_tool
from tools.scoring_tool import scoring_tool
from tools.recommendation_tool import recommendation_tool
from agent.system_prompt import SYSTEM_PROMPT
from config import BEDROCK_MODEL_ID

rfp_agent = Agent(
    model=BEDROCK_MODEL_ID,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        supplier_lookup_tool,
        rfp_generator_tool,
        email_dispatch_tool,
        proposal_fetch_tool,
        scoring_tool,
        recommendation_tool,
    ]
)
```

### `agent/agent_runner.py`

```python
"""
Local test runner — run this directly to test the full agent flow.
Usage: python -m agent.agent_runner
"""
from agent.rfp_agent import rfp_agent

TEST_PROMPT = """
We need 500 units of brake sensors for our new vehicle platform.
Specs: High-precision ABS wheel speed sensor, IP67 rated, 
operating temp -40°C to 125°C, connector type AMP Superseal.
Deadline: 2026-09-30.
Please find suppliers, generate and send the RFP, 
collect proposals, score them, and give me your top 2 recommendation.
"""

if __name__ == "__main__":
    print("=" * 60)
    print("SUPPLIER RFP MANAGEMENT AGENT — TEST RUN")
    print("=" * 60)
    response = rfp_agent(TEST_PROMPT)
    print("\nFINAL AGENT RESPONSE:")
    print(response)
```

---

## TASK 4 — SETUP SCRIPTS

### `setup/create_tables.py`

```python
"""
Run once to create all DynamoDB tables.
Usage: python setup/create_tables.py
"""
import boto3
from config import REGION, SUPPLIERS_TABLE, REQUESTS_TABLE, PROPOSALS_TABLE, SCORES_TABLE

dynamodb = boto3.client("dynamodb", region_name=REGION)

TABLES = [
    {
        "TableName": SUPPLIERS_TABLE,
        "KeySchema": [{"AttributeName": "supplier_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "supplier_id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST"
    },
    {
        "TableName": REQUESTS_TABLE,
        "KeySchema": [
            {"AttributeName": "rfp_id", "KeyType": "HASH"},
            {"AttributeName": "created_at", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "rfp_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"}
        ],
        "BillingMode": "PAY_PER_REQUEST"
    },
    {
        "TableName": PROPOSALS_TABLE,
        "KeySchema": [
            {"AttributeName": "proposal_id", "KeyType": "HASH"},
            {"AttributeName": "rfp_id", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "proposal_id", "AttributeType": "S"},
            {"AttributeName": "rfp_id", "AttributeType": "S"}
        ],
        "GlobalSecondaryIndexes": [{
            "IndexName": "rfp_id-index",
            "KeySchema": [{"AttributeName": "rfp_id", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"}
        }],
        "BillingMode": "PAY_PER_REQUEST"
    },
    {
        "TableName": SCORES_TABLE,
        "KeySchema": [
            {"AttributeName": "score_id", "KeyType": "HASH"},
            {"AttributeName": "proposal_id", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "score_id", "AttributeType": "S"},
            {"AttributeName": "proposal_id", "AttributeType": "S"}
        ],
        "BillingMode": "PAY_PER_REQUEST"
    }
]

for t in TABLES:
    try:
        dynamodb.create_table(**t)
        print(f"✅ Created: {t['TableName']}")
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠️  Already exists: {t['TableName']}")
```

### `setup/seed_data.py`

```python
"""
Seeds DynamoDB suppliers table with mock data.
Usage: python setup/seed_data.py
"""
import boto3
from decimal import Decimal
from config import REGION, SUPPLIERS_TABLE

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(SUPPLIERS_TABLE)

SUPPLIERS = [
    {"supplier_id": "SUP001", "name": "BrakeTech Industries", "category": "brake_systems", "region": "Chennai", "certifications": ["ISO9001", "IATF16949"], "rating": Decimal("4.8"), "past_delivery_score": Decimal("95"), "contact_email": "rfp@braketech-mock.com", "status": "active"},
    {"supplier_id": "SUP002", "name": "PrecisionParts Co", "category": "brake_systems", "region": "Pune", "certifications": ["ISO9001"], "rating": Decimal("4.2"), "past_delivery_score": Decimal("88"), "contact_email": "rfp@precisionparts-mock.com", "status": "active"},
    {"supplier_id": "SUP003", "name": "AutoSensor Global", "category": "sensors", "region": "Bangalore", "certifications": ["ISO9001", "IATF16949", "ISO14001"], "rating": Decimal("4.9"), "past_delivery_score": Decimal("98"), "contact_email": "rfp@autosensor-mock.com", "status": "active"},
    {"supplier_id": "SUP004", "name": "SpeedMech Ltd", "category": "brake_systems", "region": "Mumbai", "certifications": ["ISO9001"], "rating": Decimal("3.8"), "past_delivery_score": Decimal("72"), "contact_email": "rfp@speedmech-mock.com", "status": "active"},
    {"supplier_id": "SUP005", "name": "NexaComponents", "category": "sensors", "region": "Hyderabad", "certifications": [], "rating": Decimal("3.5"), "past_delivery_score": Decimal("65"), "contact_email": "rfp@nexa-mock.com", "status": "active"},
    {"supplier_id": "SUP006", "name": "TitanForge Industries", "category": "structural_parts", "region": "Coimbatore", "certifications": ["ISO9001", "IATF16949"], "rating": Decimal("4.6"), "past_delivery_score": Decimal("91"), "contact_email": "rfp@titanforge-mock.com", "status": "active"},
    {"supplier_id": "SUP007", "name": "ElectroAuto Systems", "category": "sensors", "region": "Chennai", "certifications": ["ISO9001"], "rating": Decimal("4.1"), "past_delivery_score": Decimal("84"), "contact_email": "rfp@electroauto-mock.com", "status": "active"},
    {"supplier_id": "SUP008", "name": "OldParts Pvt Ltd", "category": "brake_systems", "region": "Delhi", "certifications": ["ISO9001"], "rating": Decimal("2.9"), "past_delivery_score": Decimal("55"), "contact_email": "rfp@oldparts-mock.com", "status": "active"}
]

for s in SUPPLIERS:
    table.put_item(Item=s)
    print(f"✅ Seeded: {s['name']}")

print("\nAll suppliers seeded successfully.")
```

---

## TASK 5 — REQUIREMENTS FILE

### `requirements.txt`

```
strands-agents>=0.1.0
strands-agents-tools>=0.1.0
boto3>=1.34.0
botocore>=1.34.0
aws-cdk-lib>=2.100.0
constructs>=10.0.0
```

---

## TASK 6 — LAMBDA HANDLER

### `lambda/rfp_agent_handler.py`

```python
"""
AWS Lambda entry point for the RFP Agent.
Triggered by API Gateway or EventBridge.
"""
import json
import sys
import os
sys.path.insert(0, "/var/task")

from agent.rfp_agent import rfp_agent

def handler(event, context):
    try:
        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)
        
        user_message = body.get("message", "")
        if not user_message:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "message field required"})
            }

        response = rfp_agent(user_message)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "status": "success",
                "response": str(response)
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
```

---

## EXECUTION ORDER — FOLLOW THIS EXACTLY

KIRO must execute these steps in strict order:

```
Step 1: Create config.py
Step 2: Create requirements.txt
Step 3: Create setup/create_tables.py
Step 4: Create setup/seed_data.py
Step 5: Create setup/create_s3_bucket.py (simple S3 create script)
Step 6: Create all 6 tool files in tools/
Step 7: Create agent/system_prompt.py
Step 8: Create agent/rfp_agent.py
Step 9: Create agent/agent_runner.py
Step 10: Create lambda/rfp_agent_handler.py
Step 11: Create README.md with setup + run instructions
Step 12: Run: python setup/create_tables.py
Step 13: Run: python setup/seed_data.py
Step 14: Run: python -m agent.agent_runner  (local test)
```

---

## CONSTRAINTS — MUST FOLLOW

1. DO NOT install or use LangChain — use Strands SDK only
2. DO NOT use EC2 — Lambda only
3. DO NOT hardcode AWS credentials — use IAM role / AWS CLI profile
4. DO NOT skip seed data — demo needs real supplier data in DynamoDB
5. DO NOT add frontend code in this phase
6. All DynamoDB table names must match config.py exactly
7. Every tool must use the `@tool` decorator from `strands`
8. SES_MOCK_MODE must default to True
9. Region must be ap-south-1
10. Model must be `anthropic.claude-sonnet-4-5`

---

## SUCCESS CRITERIA

After KIRO completes, running this command:

```bash
python -m agent.agent_runner
```

Must produce output showing:
- Supplier lookup results (4+ suppliers found)
- RFP document generated with an RFP-YYYYMMDD-XXXXXXXX ID
- Email dispatch confirmation (mock mode)
- Proposals fetched or auto-generated (mock mode)
- Scores table with price/quality/delivery/compliance breakdown
- Top 2 recommendation with reasoning
- Approval required flag if any risks detected

---

*Phase 2 (Frontend — Amplify Chat UI + Supplier Portal) will be a separate KIRO prompt after Phase 1 passes.*
```
