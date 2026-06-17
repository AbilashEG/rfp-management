# AgentCore Runtime Deployment Checklist

Use this checklist to execute the deployment step by step.

---

## Phase 1: Preparation (30 minutes)

### Step 1A: Install AgentCore CLI
- [ ] Open terminal/command prompt
- [ ] Run: `npm install -g @aws/agentcore`
- [ ] Verify: `agentcore --version` (should show version number)
- [ ] Document version: `_________________`

**Expected output example:**
```
@aws/agentcore/1.2.3
```

**If failed:**
- [ ] Check Node.js is installed: `node --version` (should be 18+)
- [ ] If not: Install Node.js 18+ from nodejs.org
- [ ] Retry npm install

### Step 1B: Configure AWS Credentials
- [ ] Run: `aws configure`
- [ ] Enter AWS Access Key ID: `_________________`
- [ ] Enter AWS Secret Access Key: `_________________`
- [ ] Enter region: `us-east-1`
- [ ] Enter output format: `json`
- [ ] Verify: `aws sts get-caller-identity` (should show AWS Account ID)
- [ ] Document Account ID: `_________________`

**Expected output example:**
```json
{
  "UserId": "XXXXX:user@example.com",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/user@example.com"
}
```

**If failed:**
- [ ] Check AWS Access Key is active (not expired)
- [ ] Check IAM user has permissions

---

## Phase 2: Verification (15 minutes)

### Step 2A: Verify AWS Resources Exist

**Lambda Functions:**
- [ ] Open AWS Console: Services → Lambda
- [ ] Filter by region: `us-east-1`
- [ ] Verify these 7 functions exist:
  - [ ] rfp-supplier-lookup-v2 (should show Runtime: Python 3.12 Container)
  - [ ] rfp-rfp-generator-v2 (should show Runtime: Python 3.12 Container)
  - [ ] rfp-email-dispatch-v2 (should show Runtime: Python 3.12 Container)
  - [ ] rfp-proposal-fetch-v2 (should show Runtime: Python 3.12 Container)
  - [ ] rfp-scoring-v2 (should show Runtime: Python 3.12 Container)
  - [ ] rfp-recommendation-v2 (should show Runtime: Python 3.12 Container)
  - [ ] rfp-agent-orchestrator-v2 (main agent, should show Runtime: Python 3.12 Container)

**Note:** All should show "Container" as package type (not ZIP)

**DynamoDB Tables:**
- [ ] Open AWS Console: Services → DynamoDB
- [ ] Filter by region: `us-east-1`
- [ ] Verify these tables exist:
  - [ ] agentcore-memory-v2 (TTL: enabled, 30 days)
  - [ ] rfp-suppliers (items count: 8+)
  - [ ] rfp-requests (items count: 2+)
  - [ ] rfp-proposals (items count: 27+)
  - [ ] rfp-scores (may be empty)
  - [ ] rfp-recommendations (may be empty)

**S3 Bucket:**
- [ ] Open AWS Console: Services → S3
- [ ] Verify bucket exists:
  - [ ] rfp-documents-quadrasystems-v2

**IAM Role:**
- [ ] Open AWS Console: Services → IAM → Roles
- [ ] Verify role exists:
  - [ ] rfp-agent-execution-role-v2
  - [ ] Should have policies:
    - [ ] DynamoDB read/write
    - [ ] S3 read/write
    - [ ] CloudWatch Logs write
    - [ ] X-Ray write
    - [ ] Bedrock invoke model

**If any resource missing:**
- [ ] Check with team lead (resources might not be deployed yet)
- [ ] Do not proceed until all resources verified

### Step 2B: Verify Project Structure

- [ ] Navigate to project root: `cd "c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT"`
- [ ] Verify files exist:
  - [ ] `agentcore.yaml` (5+ KB)
  - [ ] `Dockerfile`
  - [ ] `README.md`
  - [ ] `RFP-main/agentcore_orchestrator.py`
  - [ ] `RFP-main/agentcore_memory.py`
  - [ ] `RFP-main/config.py`
  - [ ] `RFP-main/requirements.txt`
  - [ ] `RFP-main/lambda/supplier_lookup_lambda.py`
  - [ ] `RFP-main/lambda/rfp_generator_lambda.py`
  - [ ] `RFP-main/lambda/email_dispatch_lambda.py`
  - [ ] `RFP-main/lambda/proposal_fetch_lambda.py`
  - [ ] `RFP-main/lambda/scoring_lambda.py`
  - [ ] `RFP-main/lambda/recommendation_lambda.py`

**If any file missing:**
- [ ] Check GitHub repository: https://github.com/AbilashEG/rfp-management
- [ ] Pull latest code: `git pull origin main`
- [ ] Verify again

---

## Phase 3: Local Testing (20 minutes)

**⚠️ CRITICAL: DO NOT skip this phase. If local test fails, AWS deployment will also fail.**

### Step 3A: Start Local Development Server

- [ ] In terminal, navigate to project root
- [ ] Run: `agentcore dev`
- [ ] Wait 30-60 seconds for server to start
- [ ] Verify output includes:
  - [ ] ✓ Agent loaded: rfp-supplier-agent
  - [ ] ✓ Framework: Strands
  - [ ] ✓ Model: amazon.nova-pro-v1:0
  - [ ] ✓ Memory: enabled (agentcore-memory-v2)
  - [ ] ✓ Gateway: 6 MCP tools registered
  - [ ] ✓ Dev server running at: http://localhost:8000

**Note:** Keep this terminal window open. Open a NEW terminal for next step.

**If server fails to start:**
- [ ] Check error message
- [ ] Common issues:
  - [ ] Port 8000 already in use: `agentcore dev --port 9000`
  - [ ] Missing dependencies: `pip install -r RFP-main/requirements.txt`
  - [ ] Entry point wrong: Check `agentcore.yaml` line 7

### Step 3B: Test Agent Locally

- [ ] Open a NEW terminal (keep dev server running in first terminal)
- [ ] Run this command:
```bash
agentcore invoke '{
  "message": "We need 500 brake sensors by Sept 2026. Category: sensors. Quantity: 500. Deadline: 2026-09-30."
}'
```

- [ ] Wait 60-120 seconds for response
- [ ] Verify response includes:
  - [ ] ✓ status: "SUCCESS"
  - [ ] ✓ rfp_id: "RFP-YYYYMMDD-XXXXXXXX"
  - [ ] ✓ suppliers_found: 5+
  - [ ] ✓ recommendations array with 2 items
  - [ ] ✓ Each recommendation has supplier name + score

**Example success response:**
```json
{
  "status": "SUCCESS",
  "rfp_id": "RFP-20260617-E999BE46",
  "suppliers_found": 5,
  "recommendations": [
    {
      "supplier": "TechSupply Corp",
      "score": 9.2,
      "reason": "Best price + on-time delivery"
    },
    {
      "supplier": "Global Components Inc",
      "score": 8.9,
      "reason": "Excellent quality + bulk discount"
    }
  ]
}
```

**If test fails:**
- [ ] Check dev server logs (in first terminal)
- [ ] Common errors:
  - [ ] DynamoDB connection error: Check AWS credentials
  - [ ] S3 connection error: Check S3 bucket exists
  - [ ] Model error: Check Bedrock access in us-east-1
  - [ ] Memory table error: Check agentcore-memory-v2 exists
- [ ] Fix error and retry (run Step 3B again)
- [ ] Do not proceed to Phase 4 until this test passes

### Step 3C: Verify Memory Persistence

- [ ] In AWS Console, open DynamoDB
- [ ] Click table: `agentcore-memory-v2`
- [ ] Click "Explore table items"
- [ ] Verify items exist:
  - [ ] Should show 1+ items with session_id like "session-XXXXX"
  - [ ] Each item should have timestamp + conversation history

**If no items:**
- [ ] Memory not persisting (check error in dev server logs)
- [ ] Do not proceed to Phase 4

### Step 3D: Stop Local Server

- [ ] Go to first terminal (where `agentcore dev` is running)
- [ ] Press: `Ctrl+C` to stop server
- [ ] Verify output shows: "Server stopped"

---

## Phase 4: AWS Deployment (10-15 minutes)

**⚠️ This phase deploys to AWS. Costs will incur. Estimated: $1-2 for test deployment.**

### Step 4A: Deploy Agent to AWS

- [ ] In terminal, navigate to project root
- [ ] Run: `agentcore deploy`
- [ ] **DO NOT interrupt or close terminal**
- [ ] Wait 5-10 minutes for deployment to complete
- [ ] Monitor output for progress:
  - [ ] [1/5] Packaging agent code... ✓
  - [ ] [2/5] Creating AgentCore Runtime... ✓
  - [ ] [3/5] Registering MCP tools to gateway... ✓
  - [ ] [4/5] Configuring Memory, Identity, Policy... ✓
  - [ ] [5/5] Initializing Observability... ✓

**Expected final output:**
```
✓ Deployment complete in 7m 45s

Agent Details:
├─ Agent ID: arn:aws:bedrock:us-east-1:ACCOUNT:agent/rfp-supplier-agent
├─ Runtime Endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/agent
├─ Memory: agentcore-memory-v2 (30-day TTL)
├─ Tools Registered: 6/6
├─ Observability: CloudWatch + X-Ray enabled
└─ Identity: Cognito enabled
```

- [ ] Copy and save:
  - [ ] Agent ID: `_________________________________`
  - [ ] Runtime Endpoint: `_________________________________`

**If deployment fails:**
- [ ] Common errors:
  - [ ] Timeout (>15 min): Cognito creation slow, wait and retry
  - [ ] Tool registration failed: Check all Lambda functions in us-east-1
  - [ ] Memory table error: Check agentcore-memory-v2 exists
  - [ ] Permission denied: Check IAM credentials
- [ ] Check error message and fix, then retry: `agentcore deploy`

---

## Phase 5: AWS Verification (15 minutes)

### Step 5A: Verify Agent in AWS Console

- [ ] Open AWS Console: https://console.aws.amazon.com
- [ ] Navigate: Services → Bedrock → Agents
- [ ] Region: `us-east-1`
- [ ] Should see agent: `rfp-supplier-agent`
- [ ] Click on agent name to open details

**Verify Runtime Pillar:**
- [ ] Agent Status: ACTIVE ✓
- [ ] Framework: Strands ✓
- [ ] Model: amazon.nova-pro-v1:0 ✓

### Step 5B: Verify Gateway Pillar (Tools)

- [ ] In agent details page, scroll to "Tools" section
- [ ] Should see all 6 tools:
  - [ ] ✓ supplier_lookup_tool (Connected to rfp-supplier-lookup-v2)
  - [ ] ✓ rfp_generator_tool (Connected to rfp-rfp-generator-v2)
  - [ ] ✓ email_dispatch_tool (Connected to rfp-email-dispatch-v2)
  - [ ] ✓ proposal_fetch_tool (Connected to rfp-proposal-fetch-v2)
  - [ ] ✓ scoring_tool (Connected to rfp-scoring-v2)
  - [ ] ✓ recommendation_tool (Connected to rfp-recommendation-v2)

**If tools missing:**
- [ ] Check Lambda functions all deployed to us-east-1
- [ ] Check each Lambda has correct Docker container image
- [ ] Re-run: `agentcore deploy`

### Step 5C: Verify Memory Pillar

- [ ] Open AWS Console: DynamoDB
- [ ] Click table: `agentcore-memory-v2`
- [ ] Click "Explore table items"
- [ ] Should see items from local test + new items from AWS test
- [ ] Each item should have TTL timestamp

**If table is empty:**
- [ ] Memory not configured (re-run: `agentcore deploy`)

### Step 5D: Verify Identity Pillar

- [ ] Open AWS Console: Cognito
- [ ] Should see user pool: `rfp-supplier-agent-pool` (or similar)
- [ ] Status: ACTIVE ✓
- [ ] Can view user sign-in options and MFA settings

**If pool missing:**
- [ ] Identity not created (re-run: `agentcore deploy`)

### Step 5E: Verify Observability Pillar

- [ ] Open AWS Console: CloudWatch → Log Groups
- [ ] Should see log group: `/agentcore/rfp-supplier-agent`
- [ ] Click to open and view recent logs
- [ ] Should see agent execution logs with timestamps

- [ ] Open AWS Console: X-Ray → Service Map
- [ ] Should show traces:
  - [ ] Agent → supplier_lookup_tool
  - [ ] Agent → rfp_generator_tool
  - [ ] Agent → email_dispatch_tool
  - [ ] Agent → proposal_fetch_tool
  - [ ] Agent → scoring_tool
  - [ ] Agent → recommendation_tool

**If logs/traces missing:**
- [ ] Observability not fully initialized (re-run: `agentcore deploy`)
- [ ] May take 5-10 minutes to appear

### Step 5F: Verify Policy Pillar

- [ ] In agent details page, look for "Human Approval Settings"
- [ ] Status: ENABLED ✓
- [ ] Trigger Field: approval_required ✓
- [ ] Trigger Value: true ✓

**If policy missing:**
- [ ] Policy not configured (may need: `agentcore add policy && agentcore deploy`)

---

## Phase 6: End-to-End Test in AWS (10 minutes)

### Step 6A: Test Agent via AWS Console

- [ ] In Bedrock agent details page, click "Test" or "Invoke" button
- [ ] Send test request:
```json
{
  "message": "We need 500 brake sensors by Sept 2026. Category: sensors. Quantity: 500. Deadline: 2026-09-30."
}
```

- [ ] Click "Send"
- [ ] **Wait 60-120 seconds** for response
- [ ] Verify response format matches Step 3B success response

**Expected response:**
- [ ] ✓ status: "SUCCESS"
- [ ] ✓ rfp_id present
- [ ] ✓ suppliers_found: 5+
- [ ] ✓ recommendations array with 2 items

**If test fails:**
- [ ] Check CloudWatch logs for errors
- [ ] Common issues:
  - [ ] Tool invocation timeout: Increase timeout in agentcore.yaml
  - [ ] DynamoDB error: Check table permissions
  - [ ] S3 error: Check bucket permissions
- [ ] Fix and retry

### Step 6B: Verify All Pillars Working Together

- [ ] Check CloudWatch logs (new entries should appear)
- [ ] Check X-Ray traces (new trace should appear)
- [ ] Check DynamoDB agentcore-memory-v2 (new session item)
- [ ] Check DynamoDB rfp-scores (new scores should be added)
- [ ] Check DynamoDB rfp-recommendations (new recommendation item)
- [ ] Check S3 rfp-documents-quadrasystems-v2 (new RFP document should be there)

**All pillars working when:**
- [ ] ✓ Agent executed request
- [ ] ✓ All 6 tools were called (visible in X-Ray)
- [ ] ✓ Data persisted to DynamoDB
- [ ] ✓ RFP document saved to S3
- [ ] ✓ Logs visible in CloudWatch
- [ ] ✓ Memory stored in agentcore-memory-v2

---

## Phase 7: Optional - Setup API Gateway (5 minutes)

**This step is optional. Only do this if you want to expose the agent via REST API.**

### Step 7A: Add API Gateway

- [ ] Run: `agentcore add api-gateway`
- [ ] Answer prompts:
  - [ ] Create public endpoint: yes
  - [ ] Enable authentication: yes (Cognito)
  - [ ] Enable rate limiting: yes
- [ ] Run: `agentcore deploy`
- [ ] Wait 2-3 minutes for API Gateway to be created

### Step 7B: Get API Endpoint

- [ ] Run: `agentcore get endpoint`
- [ ] Copy endpoint URL: `_________________________________`

### Step 7C: Test API via curl

- [ ] Run this command (replace URL with your endpoint):
```bash
curl -X POST https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/agent \
  -H "Content-Type: application/json" \
  -d '{
    "message": "We need 500 brake sensors by Sept 2026."
  }'
```

- [ ] Verify response matches previous test

---

## Final Checklist

- [ ] ✓ Phase 1: CLI installed and credentials configured
- [ ] ✓ Phase 2: All AWS resources verified to exist
- [ ] ✓ Phase 3: Local test passed (agent executed successfully)
- [ ] ✓ Phase 4: Agent deployed to AWS AgentCore Runtime
- [ ] ✓ Phase 5: All 6 pillars verified in AWS Console
- [ ] ✓ Phase 6: End-to-end test in AWS passed
- [ ] ✓ Phase 7 (optional): API Gateway endpoint created

---

## Troubleshooting Reference

| Phase | Issue | Solution |
|-------|-------|----------|
| 1 | npm: command not found | Install Node.js 18+ |
| 1 | AWS credentials error | Run `aws configure` with correct keys |
| 2 | Lambda function missing | Deploy Lambda to us-east-1 first |
| 2 | DynamoDB table missing | Create table with correct name |
| 3 | Dev server fails to start | Check port 8000 is available |
| 3 | Agent test fails | Check CloudWatch logs in dev server terminal |
| 3 | Memory not persisting | Verify agentcore-memory-v2 table exists |
| 4 | Deployment timeout | Wait 15+ minutes, Cognito creation is slow |
| 4 | Tools not registered | Check all 7 Lambdas deployed to us-east-1 |
| 5 | Tools missing in console | Re-run `agentcore deploy` |
| 5 | Logs not appearing | Wait 5-10 minutes for logs to propagate |
| 6 | Test request fails | Check CloudWatch logs for specific error |
| 7 | API Gateway fails | Ensure Cognito user pool created first |

---

## Next Steps After Successful Deployment

1. ✅ Monitor costs in AWS Billing dashboard
2. ✅ Set up CloudWatch alarms for errors
3. ✅ Create backup strategy for agent memory
4. ✅ Document approval workflow process
5. ✅ Train users on how to invoke agent
6. ✅ Set up CI/CD pipeline for agent updates
7. ✅ Plan for disaster recovery

---

## Contact & Support

- **Agent Status Dashboard**: AWS Bedrock Console → Agents → rfp-supplier-agent
- **Logs**: AWS CloudWatch → Log Groups → /agentcore/rfp-supplier-agent
- **Traces**: AWS X-Ray → Service Map
- **Repository**: https://github.com/AbilashEG/rfp-management

**For issues:**
1. Check CloudWatch logs
2. Check X-Ray traces
3. Verify DynamoDB table permissions
4. Verify Lambda functions are accessible
5. Contact AWS support if system-level issue

