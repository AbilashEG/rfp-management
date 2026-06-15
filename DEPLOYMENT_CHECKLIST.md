# RFP Agent Deployment Checklist

Use this as a progress tracker as you deploy the backend infrastructure.

---

## **PHASE 1: AWS Stack Setup (Manual)**

### DynamoDB Tables
- [ ] `rfp-suppliers` table created
- [ ] `rfp-requests` table created  
- [ ] `rfp-proposals` table created with GSI `rfp_id-index`
- [ ] `rfp-scores` table created
- [ ] All tables showing in `aws dynamodb list-tables`

### S3 Bucket
- [ ] S3 bucket `rfp-documents-quadrasystems` created
- [ ] Bucket accessible via `aws s3 ls s3://rfp-documents-quadrasystems`

### Data Seeding
- [ ] Ran `python setup/seed_data.py`
- [ ] All 8 suppliers in `rfp-suppliers` table
- [ ] Verify: `aws dynamodb scan --table-name rfp-suppliers --query 'Items' | wc -l` shows 8

### IAM Setup
- [ ] Role `rfp-agent-lambda-role` created
- [ ] DynamoDB permissions attached
- [ ] S3 permissions attached
- [ ] Bedrock permissions attached
- [ ] SES permissions attached
- [ ] CloudWatch Logs permissions attached
- [ ] Verify: `aws iam get-role --role-name rfp-agent-lambda-role`

### ECR & Docker
- [ ] ECR repository `supplier-rfp-agent` created
- [ ] Docker image built: `docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .`
- [ ] Logged into ECR: `aws ecr get-login-password ... | docker login ...`
- [ ] Image pushed to ECR: `docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest`
- [ ] Verify: `aws ecr describe-images --repository-name supplier-rfp-agent --region us-east-1`

### Lambda Function
- [ ] Lambda function `rfp-agent-handler` created
- [ ] Function using ECR image
- [ ] Timeout set to 300+ seconds
- [ ] Memory set to 512 MB
- [ ] Environment variables set (REGION, BEDROCK_MODEL_ID)
- [ ] Verify: `aws lambda get-function --function-name rfp-agent-handler`

### API Gateway
- [ ] REST API created: `supplier-rfp-agent-api`
- [ ] Resource `/process-rfp` created
- [ ] POST method configured
- [ ] Lambda integration set up
- [ ] Deployment created and published to `prod` stage
- [ ] API endpoint working: `curl -X POST https://{API_ID}.execute-api.us-east-1.amazonaws.com/prod/process-rfp`
- [ ] Note API ID: _________________

---

## **PHASE 2: Local Testing (Before AgentCore)**

### Prerequisites
- [ ] Python 3.12+ installed
- [ ] `pip install -r requirements.txt` completed
- [ ] All dependencies installed successfully

### Unit Tests
- [ ] Run: `python -m pytest tests/test_tools.py -v`
  - [ ] test_supplier_lookup passes
  - [ ] test_rfp_generator passes
  - [ ] test_email_dispatch passes
  - [ ] test_proposal_fetch passes
  - [ ] test_scoring passes
  - [ ] test_recommendation passes

### Agent Flow Test
- [ ] Run: `python -m pytest tests/test_agent_flow.py -v`
  - [ ] Agent initializes successfully
  - [ ] Full lifecycle executes without errors
  - [ ] Output includes RFP_ID, supplier count, scores, recommendation

### Agent Runner
- [ ] Run: `python -m agent.agent_runner`
- [ ] Agent processes test RFP request
- [ ] Output includes:
  - [ ] Supplier lookup results
  - [ ] RFP_ID generated
  - [ ] Email dispatch confirmation
  - [ ] Proposal fetch results
  - [ ] Scoring results for each proposal
  - [ ] Top-2 recommendation with reasoning
  - [ ] Approval status (pending or approved)

---

## **PHASE 3: AgentCore Setup (New)**

### Knowledge Base (Memory)
- [ ] Created OpenSearch Serverless collection for memory storage
- [ ] Knowledge Base created via `aws bedrock-agent create-knowledge-base`
- [ ] Knowledge Base ID saved: **AGENTCORE_MEMORY_ID** = ___________________
- [ ] Verified in config.py

### Agent Registration (Runtime)
- [ ] Agent created via `aws bedrock-agent create-agent`
- [ ] Agent ID saved: **AGENTCORE_AGENT_ID** = ___________________
- [ ] Agent registered with foundation model `amazon.nova-pro-v1:0`
- [ ] Verified in config.py

### Tool Registration (Gateway/MCP)
- [ ] Tool 1: Supplier Lookup registered as action group
- [ ] Tool 2: RFP Generator registered as action group
- [ ] Tool 3: Email Dispatch registered as action group
- [ ] Tool 4: Proposal Fetch registered as action group
- [ ] Tool 5: Scoring registered as action group
- [ ] Tool 6: Recommendation registered as action group
- [ ] All 6 tools appear in agent description

### Policy Setup (Approval Gate)
- [ ] Approval gate role `rfp-approval-gate` created
- [ ] Policy rule configured: `halt-on-risk-flags`
- [ ] Policy attached to agent
- [ ] Tested: When `approval_required=True`, agent halts and waits for approval

### Observability
- [ ] CloudWatch Log Group `/aws/bedrock/rfp-agent` created
- [ ] Log retention set to 30 days
- [ ] CloudWatch Alarms created:
  - [ ] `rfp-tool-invocation-count`
  - [ ] `rfp-reasoning-duration`
  - [ ] `rfp-approval-gate-triggered`
- [ ] Agent tracing enabled

### Cognito (Identity)
- [ ] Cognito User Pool created: **COGNITO_USER_POOL_ID** = ___________________
- [ ] App Client created: **COGNITO_APP_CLIENT_ID** = ___________________
- [ ] Test user `procure-manager-01` created with permanent password
- [ ] Verified in config.py

### Lambda Updates
- [ ] `lambda/rfp_agent_handler.py` updated with Cognito token verification
- [ ] Bearer token validation implemented
- [ ] Lambda re-deployed
- [ ] Test: Calling API without token returns 401

---

## **PHASE 4: Integration Testing**

### Configuration
- [ ] All IDs filled in `config.py`:
  - [ ] AGENTCORE_MEMORY_ID
  - [ ] AGENTCORE_AGENT_ID
  - [ ] COGNITO_USER_POOL_ID
  - [ ] COGNITO_APP_CLIENT_ID

### Cognito Token Acquisition
- [ ] Run command to get token: `aws cognito-idp admin-initiate-auth ...`
- [ ] Token obtained and saved
- [ ] Token verified via: `python -c "import jwt; print(jwt.decode(...))"`

### API Integration Test
- [ ] Call API with Bearer token and valid RFP request
- [ ] Response status code: **200**
- [ ] Response includes:
  - [ ] RFP_ID
  - [ ] Supplier count matched
  - [ ] Proposals scored
  - [ ] Top-2 recommendation
  - [ ] Approval status

### Approval Gate Test
- [ ] Submit RFP that triggers approval_required=True
- [ ] Agent response indicates approval pending
- [ ] CloudWatch logs show policy rule triggered
- [ ] Metric `ApprovalGateTriggered` incremented

### End-to-End Workflow Test
- [ ] Submit procurement request for brake sensors
- [ ] Agent finds matching suppliers
- [ ] RFP generated and sent to suppliers
- [ ] Proposals auto-generated (demo mode)
- [ ] Proposals scored correctly:
  - [ ] Price scoring normalized
  - [ ] Quality score used directly
  - [ ] Delivery scoring normalized
  - [ ] Compliance scoring based on cert count
  - [ ] Total score = weighted average
- [ ] Risk flags generated appropriately
- [ ] Top-2 recommendation includes:
  - [ ] Supplier names and details
  - [ ] Individual dimension scores
  - [ ] Risk summary
  - [ ] Reasoning for each rank
- [ ] Approval required flag set based on risks

---

## **PHASE 5: Production Readiness**

### Performance
- [ ] Agent responds within 30 seconds (typical)
- [ ] No timeout errors on complex RFPs
- [ ] Lambda cold start impact measured: _____________ ms
- [ ] Memory utilization: _____________ MB (max)

### Reliability
- [ ] DynamoDB operations resilient to temporary failures
- [ ] S3 upload failures handled gracefully
- [ ] Tool failures don't block entire workflow
- [ ] Error logging comprehensive and queryable

### Security
- [ ] No AWS credentials in code or environment
- [ ] IAM role uses least-privilege permissions
- [ ] Cognito tokens validated on every invocation
- [ ] CloudWatch logs don't contain sensitive data (emails redacted)
- [ ] S3 bucket not publicly accessible

### Monitoring & Alerting
- [ ] CloudWatch Dashboard created for visibility
- [ ] Key metrics displayed:
  - [ ] Tool invocation count (per tool)
  - [ ] Agent reasoning duration
  - [ ] Approval gate triggers
  - [ ] Error rates
  - [ ] P99 latency
- [ ] Alarms configured for:
  - [ ] Errors > 5 in 5 min
  - [ ] Reasoning duration > 60s
  - [ ] Approval gate rate spike

### Documentation
- [ ] AWS_DEPLOYMENT_GUIDE.md reviewed and verified
- [ ] AGENTCORE_SETUP_GUIDE.md completed
- [ ] Runbook created for operational procedures
- [ ] Troubleshooting guide prepared
- [ ] Team trained on approval gate process

### Backup & Recovery
- [ ] DynamoDB point-in-time recovery enabled
- [ ] S3 versioning enabled for RFP documents
- [ ] ECR image tagged with version
- [ ] CDK state backed up

---

## **PHASE 6: Deployment to Production**

### Pre-Deployment
- [ ] Code review completed
- [ ] All tests passing
- [ ] Security audit completed
- [ ] Performance benchmarks acceptable
- [ ] Budget approved
- [ ] Change management ticket created

### Deployment
- [ ] Production environment created (separate from dev)
- [ ] All stacks deployed to production
- [ ] Configuration updated for production region/account
- [ ] Production Cognito users created
- [ ] Monitoring dashboards deployed

### Post-Deployment
- [ ] Smoke tests run (basic RFP request)
- [ ] End-to-end workflow tested in production
- [ ] Team notified of production URL
- [ ] Support documentation distributed
- [ ] Monitoring alerts active and verified

---

## **Notes & Progress Tracking**

### Key Dates
- AWS Stack Setup Started: _______________
- AWS Stack Setup Completed: _______________
- Local Testing Completed: _______________
- AgentCore Setup Started: _______________
- AgentCore Setup Completed: _______________
- Production Deployment Date: _______________

### API Details
- API ID: _______________
- API Endpoint: _______________
- API Key (if needed): _______________

### Cognito Details
- User Pool ID: _______________
- App Client ID: _______________
- Test User: procure-manager-01
- Test User Password: _______________

### AgentCore IDs
- Memory ID: _______________
- Agent ID: _______________
- Approval Gate Role ARN: _______________

### Issues Encountered & Resolutions

| Issue | Resolution | Date |
|-------|-----------|------|
| | | |
| | | |
| | | |

### Team Sign-Off

- [ ] DevOps Engineer: _______________ Date: ___
- [ ] QA Engineer: _______________ Date: ___
- [ ] Security Team: _______________ Date: ___
- [ ] Product Manager: _______________ Date: ___

---

**Status Summary:**

- [ ] Phase 1: AWS Stack (100%)
- [ ] Phase 2: Local Testing (100%)
- [ ] Phase 3: AgentCore Setup (___%)
- [ ] Phase 4: Integration Testing (___%)
- [ ] Phase 5: Production Ready (___%)
- [ ] Phase 6: Production Deployment (___%)

**Overall Progress: ____%**

