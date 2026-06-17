# AgentCore Execution Flow - Step by Step

## STEP 1: Install AgentCore CLI
```bash
npm install -g @aws/agentcore
agentcore --version
```
**Verify**: Version number prints

---

## STEP 2: Verify agentcore.yaml Exists
```bash
cat agentcore.yaml
```
**Verify**: File exists in project root with config

---

## STEP 3: Start Local Dev Server
```bash
agentcore dev --config agentcore.yaml
```
**Output Expected**:
```
[INFO] Starting AgentCore Dev Server
[INFO] Framework: Strands Agents
[INFO] Model: amazon.nova-pro-v1:0
[INFO] Tools: 6 registered
[INFO] Ready on http://localhost:8080
```
**Action**: Keep terminal open

---

## STEP 4: Test Agent Locally (NEW TERMINAL)
```bash
agentcore invoke --local '{"message": "We need 500 sensors by Sept 2026"}'
```
**Expected Output**:
```
[Step 1] Parse requirement → ✓
[Step 2] supplier_lookup → ✓ Found 3 suppliers
[Step 3] rfp_generator → ✓ RFP created
[Step 4] email_dispatch → ✓ Emails sent
[Step 5] proposal_fetch → ✓ Proposals fetched
[Step 6] scoring → ✓ Proposals scored
[Step 7] recommendation → ✓ Recommendations generated
[Step 8] Approval decision → ✓ Auto-approved

Status: SUCCESS
```
**If Fails**: Check Lambda functions deployed, DynamoDB tables exist

---

## STEP 5: Stop Dev Server
In first terminal: `Ctrl+C`

---

## STEP 6: Deploy to AWS AgentCore Runtime
```bash
agentcore deploy --config agentcore.yaml --region us-east-1
```
**Wait**: 5-10 minutes

**Expected Output**:
```
✓ Packaging agent code...
✓ Creating AgentCore Runtime...
✓ Registering 6 MCP tools...
✓ Configuring memory...
✓ Enabling observability...
✓ Deployment Complete!

Agent ID: agent-20260617-abc123
Runtime Endpoint: https://agentcore.us-east-1.amazonaws.com/agents/rfp-supplier-agent
Status: ACTIVE
```

**Save**:
- Agent ID: `agent-20260617-abc123`
- Endpoint: `https://agentcore.us-east-1.amazonaws.com/agents/rfp-supplier-agent`

---

## STEP 7: Test Deployed Agent
```bash
agentcore invoke agent-20260617-abc123 '{"message": "Create RFP for sensors"}'
```
**Expected**: Same SUCCESS response as Step 4

---

## STEP 8: Verify in AWS Console
Go to: **AWS Bedrock** → **AgentCore** → **Agents** → **rfp-supplier-agent**

**Check all PILLARS are GREEN**:
- ✅ **Runtime**: Agent hosted
- ✅ **Gateway**: 6 tools registered
  - supplier_lookup_tool
  - rfp_generator_tool
  - email_dispatch_tool
  - proposal_fetch_tool
  - scoring_tool
  - recommendation_tool
- ✅ **Memory**: DynamoDB enabled
- ✅ **Observability**: X-Ray active
- ✅ **Policy**: Human approval active
- ✅ **Identity**: Cognito active

---

## STEP 9: Verify MCP Tool Mapping
In AWS Console, check **Gateway** section shows:
```
Tool Name                Source              Status
supplier_lookup_tool     rfp-supplier-lookup ✓ Active
rfp_generator_tool       rfp-rfp-generator   ✓ Active
email_dispatch_tool      rfp-email-dispatch  ✓ Active
proposal_fetch_tool      rfp-proposal-fetch  ✓ Active
scoring_tool             rfp-scoring         ✓ Active
recommendation_tool      rfp-recommendation  ✓ Active
```

---

## STEP 10: Verify Memory Mapping
In AWS Console, check **Memory** section shows:
```
Table: agentcore-memory-v2
TTL: 30 days
Status: ✓ Enabled
Items: Session data persisting
```

Test by running agent twice with same user:
```bash
agentcore invoke agent-ID '{"user_id": "test-user", "message": "First request"}'
agentcore invoke agent-ID '{"user_id": "test-user", "message": "Second request"}'
```
**Verify**: Second response includes conversation history from first

---

## STEP 11: Verify Observability Mapping
In AWS Console:

**CloudWatch Logs**:
- Log Group: `/agentcore/rfp-supplier-agent`
- Logs appear after each invocation

**X-Ray**:
- Service Map shows: AgentCore → 6 Tools → DynamoDB/S3
- Each request traced end-to-end

**Test**: Run agent and immediately check logs/traces

---

## STEP 12: Verify Policy Mapping (Human Approval)
Agent automatically routes decisions to approval gate:

Test high-value request:
```bash
agentcore invoke agent-ID '{"message": "Create RFP for $500K budget"}'
```
**Expected**:
```
[Policy Gate] Approval required for high-value decision
Amount: $500,000
Status: PENDING_APPROVAL
```

---

## STEP 13: Verify Identity Mapping (Cognito)
Agent validates Cognito tokens:

Test with token:
```bash
agentcore invoke agent-ID \
  --cognito-token "eyJhbGc..." \
  '{"message": "Create RFP"}'
```
**Expected**: Request processed with user_id from token

---

## RESOURCE MAPPING TABLE

| Resource | Where it Maps | Verification |
|----------|---|---|
| **agentcore.yaml** | AgentCore Runtime config | AWS Console → Agent settings |
| **agentcore_orchestrator.py** | Agent logic | Executed in AgentCore Runtime |
| **supplier_lookup_lambda** | MCP tool #1 | Gateway → supplier_lookup_tool |
| **rfp_generator_lambda** | MCP tool #2 | Gateway → rfp_generator_tool |
| **email_dispatch_lambda** | MCP tool #3 | Gateway → email_dispatch_tool |
| **proposal_fetch_lambda** | MCP tool #4 | Gateway → proposal_fetch_tool |
| **scoring_lambda** | MCP tool #5 | Gateway → scoring_tool |
| **recommendation_lambda** | MCP tool #6 | Gateway → recommendation_tool |
| **agentcore-memory-v2** | Memory pillar | Memory tab → table name |
| **Cognito User Pool** | Identity pillar | Identity tab → provider |
| **X-Ray** | Observability pillar | Observability tab → tracing |
| **CloudWatch Logs** | Observability pillar | /agentcore/rfp-supplier-agent |
| **DynamoDB** | Data backend | Connected via tool Lambdas |
| **S3** | Document storage | Referenced in rfp_generator tool |

---

## EXECUTION CHECKLIST

- [ ] Step 1: AgentCore CLI installed
- [ ] Step 2: agentcore.yaml exists
- [ ] Step 3: Dev server started
- [ ] Step 4: Local test passed (SUCCESS)
- [ ] Step 5: Dev server stopped
- [ ] Step 6: Deployed to AWS (10 min wait)
- [ ] Step 7: Deployed agent test passed
- [ ] Step 8: All pillars GREEN in AWS Console
- [ ] Step 9: 6 tools registered in Gateway
- [ ] Step 10: Memory persisting conversations
- [ ] Step 11: X-Ray showing traces, CloudWatch showing logs
- [ ] Step 12: Policy gate triggering for high-value decisions
- [ ] Step 13: Cognito token validation working

---

## WHAT HAPPENS AT EACH STAGE

### Local Dev (Steps 3-4)
- Agent runs in local AgentCore emulation
- Uses real Lambda functions as MCP tools
- Connects to real DynamoDB/S3
- No actual AWS resources created yet

### Deployment (Step 6)
- Agent code packaged
- AgentCore Runtime instance created in AWS
- 6 MCP tools registered to gateway
- Memory table connected
- Observability enabled
- Policy gates configured
- Identity provider connected

### Verification (Steps 8-13)
- Agent responding from AWS
- All pillars active
- Tools callable
- Memory persisting
- Logs flowing
- Traces visible
- Approval gates working
- Auth tokens validated

---

## IF SOMETHING FAILS

| Error | Check |
|-------|-------|
| Dev server won't start | agentcore.yaml syntax, Node.js version |
| Local test fails | Lambda functions deployed, DynamoDB exists |
| Deploy timeout | AWS credentials, internet, region |
| Tools not found | Lambda names in agentcore.yaml match actual |
| Memory not persisting | DynamoDB table permissions, TTL set |
| Logs not appearing | CloudWatch log group exists, Lambda IAM role |
| Traces not showing | X-Ray enabled on Lambda, sampling rate correct |

---

## NEXT: PRODUCTION USE

Once all steps verified:

1. **Monitor** CloudWatch dashboard
2. **Review** X-Ray traces for performance
3. **Set** CloudWatch alarms for errors
4. **Load test** with realistic volume
5. **Document** runbooks for operations

---

## COMMANDS QUICK REFERENCE

```bash
# Install
npm install -g @aws/agentcore

# Dev
agentcore dev --config agentcore.yaml
agentcore invoke --local '{"message":"test"}'

# Deploy
agentcore deploy --config agentcore.yaml --region us-east-1

# Production
agentcore invoke agent-ID '{"message":"Create RFP"}'
agentcore describe agent-ID
agentcore logs agent-ID --follow

# Cleanup
agentcore delete agent-ID
```

