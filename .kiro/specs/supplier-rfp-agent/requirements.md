# Requirements Document

## Introduction

This document defines the requirements for the **Supplier RFP Management Agentic AI System** — a production-grade, fully serverless backend built on AWS Bedrock AgentCore with the Strands Agents SDK. The system automates the full Request for Proposal (RFP) lifecycle for the Automotive and Manufacturing industry, from supplier discovery through proposal scoring to ranked recommendations with human oversight.

This is Phase 1 (Backend Only) targeting a VP-level demo for Quadrasystems Pvt Ltd (AWS Partner). The system showcases all 6 Amazon Bedrock AgentCore pillars: Runtime, Memory, Gateway (MCP), Observability, Policy, and Identity. No frontend is included in this phase. All data is mocked using DynamoDB tables in ap-south-1.

---

## Glossary

- **RFP_Agent**: The Strands-based AI agent that orchestrates the full RFP lifecycle using 6 tools and Claude Sonnet 4.5 as the LLM.
- **Supplier_Lookup_Tool**: The Strands `@tool`-decorated function that queries active suppliers from DynamoDB by category and optional region.
- **RFP_Generator_Tool**: The Strands `@tool`-decorated function that generates a structured RFP document, saves it to S3, and records it in DynamoDB.
- **Email_Dispatch_Tool**: The Strands `@tool`-decorated function that dispatches RFP emails to suppliers via SES (or mock mode).
- **Proposal_Fetch_Tool**: The Strands `@tool`-decorated function that retrieves submitted proposals from DynamoDB, auto-generating mock proposals in demo mode.
- **Scoring_Tool**: The Strands `@tool`-decorated function that scores each proposal using weighted multi-criteria scoring.
- **Recommendation_Tool**: The Strands `@tool`-decorated function that generates a ranked Top-2 supplier recommendation with risk flags and human approval triggers.
- **Scoring_Engine**: The internal logic within Scoring_Tool that computes price, quality, delivery, and compliance scores.
- **Approval_Gate**: The AgentCore Policy-backed mechanism triggered when `approval_required` is `True` in a recommendation.
- **Lambda_Handler**: The AWS Lambda entry point (`rfp_agent_handler.py`) that receives API Gateway or EventBridge events and invokes the RFP_Agent.
- **CDK_Stack**: AWS CDK (Python) infrastructure-as-code stacks for DynamoDB, S3, and Lambda.
- **Mock_Mode**: SES email simulation mode (`SES_MOCK_MODE = True`) where emails are logged rather than sent.
- **RFP_ID**: A unique identifier for each RFP in the format `RFP-YYYYMMDD-XXXXXXXX`.
- **Proposal_ID**: A unique identifier for each supplier proposal in the format `PROP-XXXXXXXX`.
- **Score_ID**: A unique identifier for each scoring record in the format `SCORE-XXXXXXXX`.
- **Supplier_ID**: A string identifier for each supplier (e.g., `SUP001`–`SUP008`).
- **AgentCore**: Amazon Bedrock AgentCore service providing Runtime, Memory, Gateway, Observability, Policy, and Identity pillars.
- **IATF16949**: International Automotive Task Force quality management standard for automotive suppliers.
- **ISO9001**: International quality management system standard.
- **ISO14001**: International environmental management system standard.

---

## Requirements

### Requirement 1: Infrastructure and Configuration

**User Story:** As a DevOps engineer, I want all infrastructure defined as code with a single config source of truth, so that the system can be deployed consistently and all components reference the same table names, bucket names, and model IDs.

#### Acceptance Criteria

1. THE CDK_Stack SHALL define all four DynamoDB tables (`rfp-suppliers`, `rfp-requests`, `rfp-proposals`, `rfp-scores`) with `PAY_PER_REQUEST` billing mode.
2. THE CDK_Stack SHALL define an S3 bucket named `rfp-documents-quadrasystems` in region `ap-south-1`.
3. THE CDK_Stack SHALL define a Lambda function using a container image with Python 3.12 runtime, memory of 512 MB, and a timeout of 300 seconds.
4. THE Lambda_Handler SHALL be configured to execute in region `ap-south-1`.
5. THE Lambda_Handler SHALL use the IAM execution role granting access to DynamoDB, S3, SES, and Bedrock — no AWS credentials SHALL be hardcoded in source files or environment variables.
6. WHEN the `rfp-proposals` table is created, THE CDK_Stack SHALL define a Global Secondary Index named `rfp_id-index` on the `rfp_id` attribute with `ProjectionType: ALL`.
7. THE CDK_Stack SHALL reference `config.py` for all table names, bucket name, model ID, region, SES sender email, and scoring weights — no inline string literals for these values SHALL appear outside `config.py`.
8. WHEN `SES_MOCK_MODE` is `True` in `config.py`, THE Email_Dispatch_Tool SHALL log the email payload (rfp_id, supplier_id, recipient email address) to stdout rather than invoking the SES `send_email` API.

---

### Requirement 2: Supplier Data Management

**User Story:** As a procurement manager, I want a curated supplier database seeded with automotive industry mock suppliers, so that the agent can look up qualified vendors for any component category without manual data entry.

#### Acceptance Criteria

1. WHEN the seed script is executed, THE System SHALL insert exactly 8 supplier records into the `rfp-suppliers` DynamoDB table.
2. THE System SHALL seed suppliers spanning three categories: `brake_systems` (4 suppliers), `sensors` (3 suppliers), and `structural_parts` (1 supplier).
3. WHEN a supplier record is seeded, THE System SHALL persist the following attributes: `supplier_id`, `name`, `category`, `region`, `certifications` (List), `rating` (Decimal, scale 1.0–5.0), `past_delivery_score` (Decimal, scale 0–100), `contact_email` (valid email address format), and `status`.
4. THE System SHALL seed suppliers with `status` set to `active` for all 8 records.
5. IF a supplier has no certifications, THEN THE System SHALL store an empty list for the `certifications` attribute.
6. THE System SHALL seed at least one supplier with `past_delivery_score` below 70 (on the 0–100 scale) to enable risk-flagging scenarios.
7. THE System SHALL seed at least one supplier with three certifications (`ISO9001`, `IATF16949`, `ISO14001`) to represent a fully compliant vendor.
8. IF the seed script is executed when supplier records already exist, THEN THE System SHALL upsert (overwrite) the records rather than failing or creating duplicates.

---

### Requirement 3: Supplier Lookup

**User Story:** As the RFP_Agent, I want to query active suppliers by component category and optionally by region, so that I can identify a shortlist of candidates before generating an RFP.

#### Acceptance Criteria

1. WHEN the Supplier_Lookup_Tool is called with a `category` parameter, THE Supplier_Lookup_Tool SHALL return only suppliers whose `category` attribute matches the provided value and whose `status` is `active`.
2. WHEN the Supplier_Lookup_Tool is called with both `category` and `region` parameters, THE Supplier_Lookup_Tool SHALL return only suppliers matching both the `category` and `region` attributes and whose `status` is `active`.
3. WHEN no suppliers match the query, THE Supplier_Lookup_Tool SHALL return a response with `status: "success"`, `count: 0`, and an empty `suppliers` list.
4. THE Supplier_Lookup_Tool SHALL return each matching supplier's `supplier_id`, `name`, `category`, `region`, `certifications`, `rating`, `past_delivery_score`, `contact_email`, and `status`.
5. THE Supplier_Lookup_Tool SHALL return a `count` field equal to the number of suppliers in the returned list.
6. IF a DynamoDB scan operation fails, THEN THE Supplier_Lookup_Tool SHALL raise an exception with an error message indicating the failure reason and return no partial supplier data.
7. IF the `category` parameter is missing or empty, THEN THE Supplier_Lookup_Tool SHALL return `{"status": "error", "message": "category parameter is required"}` without querying DynamoDB.

---

### Requirement 4: RFP Document Generation

**User Story:** As a procurement manager, I want a structured RFP document automatically generated and stored when I describe my component requirement, so that I don't need to manually author procurement documents.

#### Acceptance Criteria

1. WHEN the RFP_Generator_Tool is invoked with `component_name`, `specs`, `quantity`, `deadline`, and `supplier_ids`, THE RFP_Generator_Tool SHALL generate a unique RFP_ID in the format `RFP-YYYYMMDD-XXXXXXXX` where `XXXXXXXX` is 8 uppercase hexadecimal characters.
2. WHEN the RFP_Generator_Tool is invoked, THE RFP_Generator_Tool SHALL produce an RFP document that includes: the RFP_ID, generation timestamp, component name, specifications, quantity, deadline, a list of submission requirements (price, lead time, certifications, delivery metrics, MOQ, warranty), and the evaluation criteria (Price 30%, Quality 30%, Delivery 20%, Compliance 20%).
3. WHEN the RFP document is generated, THE RFP_Generator_Tool SHALL upload it to the S3 bucket at key `rfp-docs/{RFP_ID}.txt` with `ContentType: text/plain`.
4. WHEN the S3 upload succeeds, THE RFP_Generator_Tool SHALL set `s3_path` to `s3://rfp-documents-quadrasystems/rfp-docs/{RFP_ID}.txt`.
5. IF the S3 upload fails, THEN THE RFP_Generator_Tool SHALL set `s3_path` to `mock-s3://rfp-docs/{RFP_ID}.txt`, include a `s3_warning` field in the response indicating the upload failure, and continue execution without raising an exception.
6. WHEN the RFP record is persisted, THE RFP_Generator_Tool SHALL write a record to the `rfp-requests` DynamoDB table with `status: "draft"`, `created_by: "rfp-agent"`, and `shortlisted_suppliers` set to the `supplier_ids` input list.
7. WHEN the RFP_Generator_Tool completes successfully, THE RFP_Generator_Tool SHALL return a dict containing `rfp_id` (string), `s3_path` (string), `rfp_content` (string), and `supplier_count` (integer equal to the length of the `supplier_ids` input list).
8. WHEN any two calls to RFP_Generator_Tool occur on the same calendar day, THE RFP_Generator_Tool SHALL return distinct `rfp_id` values for each call.
9. IF the DynamoDB `put_item` call fails after a successful S3 upload, THEN THE RFP_Generator_Tool SHALL raise an exception with an error message indicating the persistence failure.
10. IF any required input parameter (`component_name`, `specs`, `quantity`, `deadline`, or `supplier_ids`) is missing or empty, THEN THE RFP_Generator_Tool SHALL return `{"status": "error", "message": "missing required parameter: {parameter_name}"}` without invoking S3 or DynamoDB.

---

### Requirement 5: RFP Email Dispatch

**User Story:** As the RFP_Agent, I want to notify shortlisted suppliers of the new RFP via email, so that suppliers receive timely invitations to submit proposals.

#### Acceptance Criteria

1. WHEN the Email_Dispatch_Tool is called with `rfp_id`, `supplier_ids`, and `rfp_content`, THE Email_Dispatch_Tool SHALL attempt to dispatch one email per supplier in the `supplier_ids` list, processing each supplier independently so that a failure for one supplier does not block dispatch to others.
2. WHILE `SES_MOCK_MODE` is `True`, THE Email_Dispatch_Tool SHALL set each result's `status` to `"mock_sent"` and include a `[MOCK]` prefix message — no actual SES `send_email` call SHALL be made.
3. WHEN `SES_MOCK_MODE` is `False` and SES dispatch succeeds, THE Email_Dispatch_Tool SHALL set the result `status` to `"sent"`.
4. IF `SES_MOCK_MODE` is `False` and an SES API call throws an exception for a specific supplier, THEN THE Email_Dispatch_Tool SHALL set that supplier's result `status` to `"failed"` and include the exception message in `error` — it SHALL NOT raise an exception or stop processing remaining suppliers.
5. THE Email_Dispatch_Tool SHALL look up each supplier's `contact_email` and `name` from the `rfp-suppliers` DynamoDB table before dispatching.
6. IF a supplier_id is not found in DynamoDB, THEN THE Email_Dispatch_Tool SHALL use `"unknown@mock.com"` as the fallback email, the `supplier_id` string as the fallback name, and proceed with the dispatch attempt.
7. IF the DynamoDB `get_item` call throws an exception during supplier lookup, THEN THE Email_Dispatch_Tool SHALL set that supplier's result `status` to `"failed"`, include the exception message, and continue processing the remaining suppliers.
8. THE Email_Dispatch_Tool SHALL return a response dict containing: `rfp_id` (string), `dispatched` (integer equal to the count of results with `status` of `"sent"` or `"mock_sent"`), and `results` (list where each entry contains `supplier_id`, `email`, `status`, and optionally `error` or `message`).

---

### Requirement 6: Proposal Collection

**User Story:** As the RFP_Agent, I want to retrieve all submitted proposals for an RFP and, in demo mode, auto-generate realistic mock proposals when none exist, so that scoring can proceed without waiting for real supplier submissions.

#### Acceptance Criteria

1. WHEN the Proposal_Fetch_Tool is called with an `rfp_id`, THE Proposal_Fetch_Tool SHALL scan the `rfp-proposals` DynamoDB table and return all records where `rfp_id` matches.
2. WHEN existing proposals are found in DynamoDB, THE Proposal_Fetch_Tool SHALL return them as-is without generating additional mock data.
3. IF no proposals exist for the given `rfp_id` in DynamoDB, THEN THE Proposal_Fetch_Tool SHALL auto-generate one mock proposal per supplier ID in the provided `supplier_ids` list.
4. WHEN a mock proposal is generated, THE Proposal_Fetch_Tool SHALL persist it to the `rfp-proposals` DynamoDB table with a unique `Proposal_ID` in format `PROP-XXXXXXXX`.
5. WHEN generating mock proposals, THE Proposal_Fetch_Tool SHALL use predefined mock values: `SUP005` and `SUP008` SHALL receive empty `compliance_docs` lists (represented as `[]`) to simulate non-compliant vendors.
6. WHEN generating mock proposals, THE Proposal_Fetch_Tool SHALL assign `status: "received"` to each generated proposal.
7. THE Proposal_Fetch_Tool SHALL return a dict containing `rfp_id` (string), `proposal_count` (integer equal to the length of the returned proposals list), and `proposals` (list of proposal dicts).
8. WHEN mock proposals are generated for `SUP003`, THE Proposal_Fetch_Tool SHALL assign `quality_score` of 97, `price` of 940 (INR), and `lead_time_days` of 10.
9. IF the `supplier_ids` list is empty and no proposals exist, THEN THE Proposal_Fetch_Tool SHALL return `{"status": "success", "rfp_id": rfp_id, "proposal_count": 0, "proposals": []}` without attempting to generate mock proposals.
10. IF the DynamoDB scan or `put_item` call raises an exception, THEN THE Proposal_Fetch_Tool SHALL return `{"status": "error", "message": "DynamoDB operation failed: {exception_message}"}` without partial results.

---

### Requirement 7: Multi-Criteria Proposal Scoring

**User Story:** As a procurement manager, I want each supplier proposal objectively scored across price, quality, delivery, and compliance dimensions, so that I can make data-driven award decisions.

#### Acceptance Criteria

1. WHEN the Scoring_Tool is invoked with a non-empty `proposals` list, THE Scoring_Engine SHALL compute a normalized `price_score` for each proposal where the lowest-priced proposal receives the highest score, using the formula `((max_price - price) / (max_price - min_price + 1)) * 100`.
2. WHEN the Scoring_Tool is invoked, THE Scoring_Engine SHALL compute a normalized `delivery_score` for each proposal where the shortest lead time receives the highest score, using the formula `((max_lead - lead) / (max_lead - min_lead + 1)) * 100`.
3. THE Scoring_Engine SHALL use the `quality_score` field directly from the proposal (range 0–100) as the quality dimension score. IF the `quality_score` value is outside the range 0–100, THEN THE Scoring_Engine SHALL clamp it to the nearest boundary (0 or 100) before use.
4. THE Scoring_Engine SHALL compute `compliance_score` as: 100 if the proposal has 2 or more `compliance_docs`, 50 if it has exactly 1, and 0 if it has none.
5. THE Scoring_Engine SHALL compute `total_score` as: `(price_score × 0.30) + (quality_score × 0.30) + (delivery_score × 0.20) + (compliance_score × 0.20)`.
6. WHEN a proposal has no `compliance_docs`, THE Scoring_Tool SHALL append `"NO_CERTIFICATIONS — High compliance risk"` to the `flags` list.
7. WHEN a proposal's `lead_time_days` exceeds 30, THE Scoring_Tool SHALL append a `"LONG_LEAD_TIME — {N} days exceeds 30-day threshold"` flag.
8. WHEN a proposal's `price` is less than 60% of the minimum price across all proposals, THE Scoring_Tool SHALL append `"PRICE_ANOMALY — Price unusually low, verify quality"` to the `flags` list.
9. WHEN a proposal's `quality_score` is below 70, THE Scoring_Tool SHALL append a `"LOW_QUALITY_SCORE — {N}/100 below acceptable threshold"` flag.
10. WHEN a proposal has no flags and a `total_score` >= 70, THE Scoring_Tool SHALL set `recommendation` to `"shortlist"`.
11. WHEN a proposal has one or more flags, or has a `total_score` below 70, THE Scoring_Tool SHALL set `recommendation` to `"review"`.
12. THE Scoring_Tool SHALL persist each score record to the `rfp-scores` DynamoDB table with a unique `Score_ID` in format `SCORE-XXXXXXXX`.
13. THE Scoring_Tool SHALL return the `scored_proposals` list sorted by `total_score` in descending order.
14. IF the `proposals` input list is empty, THEN THE Scoring_Tool SHALL return `{"status": "error", "message": "No proposals to score"}`.
15. WHEN all proposals have the same price, THE Scoring_Engine SHALL return a `price_score` of 0.0 for all proposals without raising a division-by-zero error, due to the `+1` denominator guard.
16. IF a DynamoDB `put_item` call fails when persisting a score record, THEN THE Scoring_Tool SHALL raise an exception identifying the failed `score_id` and the DynamoDB error message.

---

### Requirement 8: Supplier Recommendation with Human Approval Gate

**User Story:** As a procurement manager, I want a ranked Top-2 supplier recommendation with detailed reasoning and automatic escalation for human review when risks are detected, so that contract awards are both data-driven and safely governed.

#### Acceptance Criteria

1. WHEN the Recommendation_Tool is invoked with a non-empty `scored_proposals` list, THE Recommendation_Tool SHALL select the top 2 proposals by `total_score` (descending), with ties broken by `proposal_id` ascending, as the recommended suppliers.
2. THE Recommendation_Tool SHALL enrich each recommendation with supplier details (`name`, `region`, `certifications`, `past_delivery_score`) retrieved from the `rfp-suppliers` DynamoDB table using the proposal's `supplier_id`.
3. THE Recommendation_Tool SHALL produce a `reasoning` string for each recommended supplier that includes: the rank number, the `total_score` value, the name of the highest-scoring individual dimension, and a list of any risk flags (or "No major risks identified" if none).
4. A **flag** is defined as a risk indicator string appended to a proposal's `flags` list during the scoring phase (e.g., `"NO_CERTIFICATIONS"`, `"LONG_LEAD_TIME"`, `"PRICE_ANOMALY"`, `"LOW_QUALITY_SCORE"`).
5. WHEN any of the Top-2 proposals contain one or more flags, THE Recommendation_Tool SHALL set `approval_required` to `True`.
6. WHEN `approval_required` is `True`, THE Recommendation_Tool SHALL set `approval_message` to a string that communicates human approval is required and references the detected risk categories.
7. WHEN no flags are present in the Top-2 proposals, THE Recommendation_Tool SHALL set `approval_required` to `False` and `approval_message` to a string indicating no critical flags were detected.
8. THE Recommendation_Tool SHALL return a response dict containing: `top_2_recommendations` (list), `all_flags` (list), `approval_required` (boolean), `approval_message` (string), and `total_evaluated` (integer equal to the length of `scored_proposals`).
9. IF the `scored_proposals` input is empty, THEN THE Recommendation_Tool SHALL return `{"status": "error", "message": "No scored proposals provided"}`.
10. WHEN `approval_required` is `True`, THE RFP_Agent's final response SHALL contain a human sign-off notice before any contract award language.
11. IF the DynamoDB `get_item` call fails when fetching supplier details for enrichment, THEN THE Recommendation_Tool SHALL substitute `"Unknown"` for all enrichment fields and include a warning in the affected recommendation's `reasoning` string, rather than raising an exception.

---

### Requirement 9: Full RFP Lifecycle Orchestration

**User Story:** As a procurement manager, I want to submit a single natural-language requirement and have the agent autonomously execute the full RFP lifecycle end-to-end, so that the procurement process is automated without manual tool invocation.

#### Acceptance Criteria

1. WHEN the RFP_Agent receives a procurement request message, THE RFP_Agent SHALL invoke Supplier_Lookup_Tool first to discover matching suppliers before any other action.
2. IF the Supplier_Lookup_Tool returns `count: 0`, THEN THE RFP_Agent SHALL halt the lifecycle, respond with a message indicating no matching suppliers were found for the specified category, and not invoke any further tools.
3. WHEN the RFP_Agent has identified suppliers, THE RFP_Agent SHALL invoke RFP_Generator_Tool with all shortlisted supplier IDs (the full set returned by Supplier_Lookup_Tool) to produce the RFP document before dispatching emails.
4. WHEN the RFP is generated, THE RFP_Agent SHALL invoke Email_Dispatch_Tool to notify all shortlisted supplier IDs; if individual dispatch failures occur, THE RFP_Agent SHALL continue and report the failed count in the final summary.
5. WHEN emails are dispatched, THE RFP_Agent SHALL invoke Proposal_Fetch_Tool; IF no real proposals exist for the RFP_ID, THE RFP_Agent SHALL proceed with the auto-generated mock proposals returned by the tool.
6. WHEN proposals are fetched, THE RFP_Agent SHALL invoke Scoring_Tool to score ALL proposals before generating a recommendation.
7. WHEN all proposals are scored, THE RFP_Agent SHALL invoke Recommendation_Tool to produce the final ranked output.
8. THE RFP_Agent SHALL use `anthropic.claude-sonnet-4-5` via Amazon Bedrock as the LLM for all reasoning steps.
9. THE RFP_Agent SHALL include a structured summary in its final response covering: matched suppliers count, RFP_ID, dispatch confirmation (sent count and failed count), proposal count, score breakdown for the top 2 suppliers, recommendation with approval status (`"approved"` or `"pending human review"`).
10. WHEN the RFP_Agent completes a full lifecycle run, THE System SHALL have at least one new record in each of the following DynamoDB tables: `rfp-requests` (the generated RFP), `rfp-proposals` (at least one proposal per shortlisted supplier), and `rfp-scores` (one score record per evaluated proposal).

---

### Requirement 10: Lambda Invocation Interface

**User Story:** As a backend integrator, I want the RFP Agent exposed as an AWS Lambda function with a standard HTTP-style interface, so that it can be triggered by API Gateway, EventBridge, or other AWS services.

#### Acceptance Criteria

1. WHEN the Lambda_Handler receives an event with a `body` containing a `message` field, THE Lambda_Handler SHALL invoke the RFP_Agent with that message string and return a 200 response.
2. WHEN the Lambda_Handler receives an event with a missing or empty `message` field, THE Lambda_Handler SHALL return a 400 response with `{"error": "message field required"}`.
3. WHEN the RFP_Agent raises an unhandled exception during processing, THE Lambda_Handler SHALL return a 500 response containing the exception message.
4. THE Lambda_Handler SHALL set the `Content-Type` response header to `application/json` and `Access-Control-Allow-Origin` to `*`.
5. THE Lambda_Handler SHALL handle both string-encoded and dict-decoded `body` formats from the API Gateway event payload.
6. WHERE the Lambda container image is deployed, THE Lambda_Handler SHALL resolve all module imports (`agent`, `tools`, `config`) relative to `/var/task`.

---

### Requirement 11: AgentCore Pillar Integration

**User Story:** As a VP-level audience member, I want the system to visibly demonstrate all 6 Amazon Bedrock AgentCore pillars, so that the demo clearly showcases the full platform capability.

#### Acceptance Criteria

1. THE RFP_Agent SHALL be deployed on AgentCore Runtime, with a non-empty `AGENTCORE_AGENT_ID` stored in `config.py` confirming successful registration.
2. THE RFP_Agent SHALL integrate with AgentCore Memory so that the following session fields are persisted and retrievable across invocations: `rfp_id`, `supplier_ids`, `proposal_count`, and `approval_required` status.
3. THE System SHALL expose all 6 agent tools via AgentCore Gateway using the MCP (Model Context Protocol) interface, with each tool registered by its `@tool` decorator name.
4. THE System SHALL emit the following named metrics to AgentCore Observability (backed by CloudWatch): `ToolInvocationCount` (per tool name), `AgentReasoningDuration` (milliseconds per lifecycle run), and `ApprovalGateTriggered` (0 or 1 per run).
5. WHEN `approval_required` is `True` in a recommendation, THE System SHALL invoke the AgentCore Policy human approval gate, and the agent SHALL remain in a halted state (not proceed to contract language) until an approval or rejection response is received from the gate.
6. THE System SHALL use AgentCore Identity (backed by Amazon Cognito) for caller authentication; IF a request arrives without a valid Cognito token, THEN THE Lambda_Handler SHALL return a 401 response with `{"error": "Unauthorized"}` without invoking the RFP_Agent.

---

### Requirement 12: Observability and Monitoring

**User Story:** As a system operator, I want all agent actions and tool invocations logged and traceable, so that I can diagnose failures and monitor RFP processing performance.

#### Acceptance Criteria

1. THE Lambda_Handler SHALL emit a structured JSON log entry to Amazon CloudWatch Logs for every invocation containing at minimum: `invocation_id`, `input_message` (truncated to 500 characters), `response_status` (200/400/500), and `timestamp`.
2. WHEN a tool invocation fails with an exception, THE System SHALL log to CloudWatch Logs a structured entry containing: `tool_name`, `input_parameters` (with any email address values redacted), and `exception_message`.
3. THE System SHALL publish a `RFPLifecycleDuration` metric in milliseconds to the `RFPAgentMetrics` CloudWatch namespace with unit `Milliseconds`, recording the wall-clock time from first tool invocation to Recommendation_Tool completion for each full lifecycle run.
4. THE System SHALL use AgentCore Observability to emit a trace for each agent execution containing, at minimum, the ordered sequence of tool names invoked and the `total_score` values of the top 2 scored proposals.
5. WHEN an RFP lifecycle completes successfully, THE System SHALL emit a structured CloudWatch Logs entry containing `rfp_id`, `proposals_evaluated` (integer), and `approval_required` (boolean).

---

### Requirement 13: Project Structure and Packaging

**User Story:** As a developer, I want the project to follow a defined folder structure with a complete `requirements.txt` and `Dockerfile`, so that the system can be consistently built, packaged, and deployed.

#### Acceptance Criteria

1. THE System SHALL organize source files into the following top-level directories: `tools/`, `agent/`, `lambda/`, `infra/`, `setup/`, and `tests/`.
2. THE System SHALL include a `requirements.txt` pinning exact versions: `strands-agents==0.1.0`, `strands-agents-tools==0.1.0`, `boto3==1.34.0`, `botocore==1.34.0`, `aws-cdk-lib==2.100.0`, and `constructs==10.0.0`.
3. THE System SHALL include a `Dockerfile` in `lambda/` that packages the Lambda container image using a Python 3.12 base image, with CMD set to `lambda/rfp_agent_handler.handler` as the Lambda entry point.
4. THE `tools/` directory SHALL contain exactly 7 files: `__init__.py` plus one `.py` file for each of the 6 tools (`supplier_lookup_tool.py`, `rfp_generator_tool.py`, `email_dispatch_tool.py`, `proposal_fetch_tool.py`, `scoring_tool.py`, `recommendation_tool.py`).
5. THE `agent/` directory SHALL contain `__init__.py`, `rfp_agent.py`, `system_prompt.py`, and `agent_runner.py`.
6. THE `tests/` directory SHALL contain `test_tools.py` with at least one test function per tool covering the nominal (happy-path) execution, and `test_agent_flow.py` for end-to-end flow validation.
7. THE System SHALL include a `README.md` with setup instructions describing the required execution order: (1) deploy CDK infra, (2) run setup scripts to create tables and seed data, (3) invoke the agent runner, (4) run the test suite.
