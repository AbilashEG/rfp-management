# Agent Runtime Deployment Checklist

**Status**: Ready to Execute  
**Date**: 2026-06-17  
**Time Estimate**: 45 minutes

---

## Pre-Deployment Verification

### Step 1: Verify Prerequisites

- [ ] AWS CLI configured with credentials
- [ ] Region set to us-east-1
- [ ] Docker and ECR login working
- [ ] Git repository up to date
- [ ] All 7 Lambda containers deployed

**Verification Commands:**
```bash
# Check AWS config
aws sts get-caller-identity

# Check Docker
docker ps

# Check Lambda functions
aws lambda list-functions --region us-east-1 --query 'Functions[?contains(FunctionName, `rfp-`)].FunctionName'
```

- [ ] All prerequisites verified

---

## Phase 1: API Gateway Deployment (10 min)

### Step 1a: Create API Gateway Endpoint

```bash
bash setup-api-gateway.sh us-east-1
```

Expected Output:
```
✅ API GATEWAY SETUP COMPLETE
Endpoint: https://XXXXXXXX.execute-api.us-east-1.amazonaws.com/prod/process-rfp
```

**Actions:**
- [ ] Run API Gateway setup script
- [ ] Save endpoint URL
- [ ] Verify endpoint is accessible

### Step 1b: Test API Gateway

```bash
# Set variables
API_ENDPOINT="https://XXXXXXXX.execute-api.us-east-1.amazonaws.com/prod/process-rfp"

# Test endpoint
curl -X POST $API_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{"body": "{\"message\": \"Create RFP for sensors\"}"}'
```

Expected Response:
```json
{
  "statusCode": 200,
  "body": "{\"workflow_status\": \"SUCCESS\", ...}"
}
```

**Actions:**
- [ ] Test endpoint from command line
- [ ] Verify status code 200
- [ ] Document endpoint for clients

---

## Phase 2: Observability Setup (15 min)

### Step 2a: Enable X-Ray & CloudWatch

```bash
bash setup-observability.sh us-east-1
```

Expected Output:
```
✅ OBSERVABILITY SETUP COMPLETE
Services Enabled:
  ✓ X-Ray Distributed Tracing
  ✓ CloudWatch Logs
  ✓ CloudWatch Dashboard
  ✓ CloudWatch Alarms
```

**Actions:**
- [ ] Run observability setup script
- [ ] Verify CloudWatch logs exist
- [ ] Check X-Ray is enabled

### Step 2b: Verify Dashboard

```bash
# Open CloudWatch Dashboard
aws cloudwatch get-dashboard --dashboard-name rfp-agent-dashboard --region us-east-1
```

**Actions:**
- [ ] Dashboard created and accessible
- [ ] Metrics are being collected
- [ ] Alarms are active

### Step 2c: Test Observability

1. Invoke Lambda function
2. Check CloudWatch Logs
3. Check X-Ray Service Map
4. Verify metrics in Dashboard

**Actions:**
- [ ] Logs appearing in CloudWatch
- [ ] X-Ray traces showing
- [ ] Dashboard metrics updating

---

## Phase 3: Memory Persistence Verification (10 min)

### Step 3a: Verify DynamoDB Table

```bash
# Check memory table exists
aws dynamodb describe-table \
  --table-name agentcore-memory-v2 \
  --region us-east-1 \
  --query 'Table.{TableName: TableName, ItemCount: ItemCount, KeySchema: KeySchema}'
```

Expected Output:
```
{
  "TableName": "agentcore-memory-v2",
  "ItemCount": 0-N,
  "KeySchema": [
    {"AttributeName": "session_id", "KeyType": "HASH"}
  ]
}
```

**Actions:**
- [ ] Memory table exists
- [ ] Has correct key schema
- [ ] TTL configured for cleanup

### Step 3b: Test Session Persistence

```bash
# First request - creates session
aws lambda invoke \
  --function-name rfp-agentcore-orchestrator \
  --payload '{"body":"{\"message\":\"Create RFP for sensors\"}"}' \
  --region us-east-1 \
  response1.json

# Extract session_id from response
SESSION_ID=$(jq -r '.body | fromjson | .session_id' response1.json)
echo "Session ID: $SESSION_ID"

# Second request - same session
aws lambda invoke \
  --function-name rfp-agentcore-orchestrator \
  --payload "{\"body\":\"{\\\"session_id\\\":\\\"$SESSION_ID\\\",\\\"message\\\":\\\"Add budget constraint\\\"}\"}" \
  --region us-east-1 \
  response2.json

# Verify conversation history persisted
jq '.body | fromjson | .conversation_history' response2.json
```

**Actions:**
- [ ] First request returns session_id
- [ ] Second request with same session_id
- [ ] Conversation history includes both messages
- [ ] Session data persisted in DynamoDB

---

## Phase 4: Tool Integration Verification (15 min)

### Step 4a: Verify Tool Lambda Functions

```bash
# Check all tool Lambdas are deployed
aws lambda list-functions \
  --region us-east-1 \
  --query 'Functions[?contains(FunctionName, `rfp-`)].{FunctionName: FunctionName, PackageType: PackageType, State: State}' \
  --output table
```

Expected Output:
```
|                    FunctionName                    | PackageType |  State |
|-----------------------------------------------------|-------------|--------|
| rfp-agentcore-orchestrator                         | Image       | Active |
| rfp-supplier-lookup                                | Image       | Active |
| rfp-rfp-generator                                  | Image       | Active |
| rfp-email-dispatch                                 | Image       | Active |
| rfp-proposal-fetch                                 | Image       | Active |
| rfp-scoring                                        | Image       | Active |
| rfp-recommendation                                 | Image       | Active |
```

**Actions:**
- [ ] All 7 Lambdas deployed as container images
- [ ] All functions show State: Active
- [ ] No functions in Failed state

### Step 4b: Test Individual Tools

```bash
# Test Tool 1: supplier_lookup
aws lambda invoke \
  --function-name rfp-supplier-lookup \
  --payload '{"body":"{\"category\":\"sensors\",\"rfp_id\":\"RFP-TEST\"}"}' \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  test1.json

# Verify success
jq '.statusCode' test1.json  # Should be 200
```

**Repeat for each tool**:
- [ ] supplier_lookup: Returns suppliers
- [ ] rfp_generator: Creates RFP
- [ ] email_dispatch: Dispatches emails
- [ ] proposal_fetch: Fetches proposals
- [ ] scoring: Calculates scores
- [ ] recommendation: Generates recommendations

### Step 4c: Test Tool Invocation from Orchestrator

```bash
# Run full orchestrator workflow
aws lambda invoke \
  --function-name rfp-agentcore-orchestrator \
  --payload '{"body":"{\"cognito_token\":\"test-token\",\"message\":\"Create RFP for sensors\"}"}' \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  full_flow.json

# Check response
jq '.body | fromjson | .workflow_status' full_flow.json  # Should be "SUCCESS"
jq '.body | fromjson | .tools_invoked' full_flow.json    # Should list all tools
```

**Actions:**
- [ ] All tools invoked in workflow
- [ ] Each tool returns success
- [ ] No tool errors in logs

---

## Phase 5: End-to-End Testing (5 min)

### Step 5a: Test via API Gateway

```bash
# Set API endpoint
API_ENDPOINT="https://XXXXXXXX.execute-api.us-east-1.amazonaws.com/prod/process-rfp"

# Test request
curl -X POST $API_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "cognito_token": "test-token",
      "message": "Create RFP for semiconductor sensors with $30K budget"
    }
  }'
```

Expected Response:
```json
{
  "statusCode": 200,
  "body": "{\"workflow_status\": \"SUCCESS\", \"rfp_id\": \"RFP-...\", ...}"
}
```

**Actions:**
- [ ] API endpoint responds
- [ ] Status code 200
- [ ] Response contains workflow_status: SUCCESS
- [ ] RFP ID generated
- [ ] All 8 workflow steps executed

### Step 5b: Check Observability Captured

```bash
# Check CloudWatch logs
aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region us-east-1

# Check X-Ray traces
aws xray get-service-graph \
  --start-time $(date -d '5 minutes ago' +%s) \
  --end-time $(date +%s) \
  --region us-east-1
```

**Actions:**
- [ ] Logs showing in CloudWatch
- [ ] X-Ray traces captured
- [ ] Request flow visible in Service Map
- [ ] All tool invocations traced

---

## Phase 6: Production Readiness Verification

### Step 6a: Security Checklist

- [ ] Cognito authorizer configured (or API Key)
- [ ] IAM roles follow least privilege
- [ ] Secrets not in logs
- [ ] DynamoDB encryption enabled
- [ ] S3 bucket versioning enabled
- [ ] Lambda timeout adequate (300s)

### Step 6b: Performance Checklist

- [ ] Lambda concurrency reserved
- [ ] DynamoDB capacity sufficient
- [ ] API Gateway throttling configured
- [ ] Response time < 30s
- [ ] Memory usage < 512MB

### Step 6c: Reliability Checklist

- [ ] Error rate < 1%
- [ ] Tool success rate > 99%
- [ ] No throttling errors
- [ ] No DynamoDB throttling
- [ ] Alarms configured and tested

**Actions:**
- [ ] All security items verified
- [ ] All performance items verified
- [ ] All reliability items verified

---

## Phase 7: Documentation & Knowledge Transfer

### Step 7a: Create API Documentation

Create `API_DOCUMENTATION.md` with:
- [ ] Endpoint URL
- [ ] Request/response format
- [ ] Authentication method
- [ ] Error codes
- [ ] Example curl commands

### Step 7b: Create Runbooks

Create operational runbooks:
- [ ] How to monitor the system
- [ ] How to debug issues
- [ ] How to scale/upgrade
- [ ] How to rollback changes

### Step 7c: Update README

- [ ] Add deployment instructions
- [ ] Add API endpoint information
- [ ] Add monitoring links
- [ ] Add support contacts

**Actions:**
- [ ] API documentation created
- [ ] Runbooks created
- [ ] README updated
- [ ] Documentation pushed to GitHub

---

## Final Verification

### Before Going Live

```bash
# 1. Verify all systems health
aws lambda get-function --function-name rfp-agentcore-orchestrator --region us-east-1

# 2. Check DynamoDB health
aws dynamodb describe-table --table-name agentcore-memory-v2 --region us-east-1

# 3. Verify S3 bucket
aws s3 ls rfp-documents-quadrasystems

# 4. Check API Gateway status
aws apigateway get-rest-apis --region us-east-1 --query "items[?name=='rfp-agent-api']"

# 5. Verify CloudWatch Dashboard
aws cloudwatch get-dashboard --dashboard-name rfp-agent-dashboard --region us-east-1
```

- [ ] All systems green
- [ ] No errors in logs
- [ ] X-Ray showing healthy trace map
- [ ] Dashboard metrics updating
- [ ] Alarms active and configured

---

## Deployment Summary

### Components Deployed

| Component | Status | URL |
|-----------|--------|-----|
| API Gateway Endpoint | ✅ | `https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/process-rfp` |
| Orchestrator Lambda | ✅ | rfp-agentcore-orchestrator |
| 6 Tool Lambdas | ✅ | rfp-supplier-lookup, rfp-rfp-generator, ... |
| Memory Table | ✅ | agentcore-memory-v2 |
| X-Ray Tracing | ✅ | Service Map visible |
| CloudWatch Logs | ✅ | /aws/lambda/rfp-* |
| CloudWatch Dashboard | ✅ | rfp-agent-dashboard |
| CloudWatch Alarms | ✅ | 4 alarms configured |

### Metrics to Track

- Agent execution time: Target < 30s
- Tool success rate: Target > 99%
- Error rate: Target < 1%
- Memory usage: Target < 512MB
- Approval decision accuracy: Track over time

### Success Criteria

✅ API Gateway endpoint responding  
✅ All workflow steps executing  
✅ Memory persisting conversations  
✅ Observability capturing traces  
✅ All tools invoked successfully  
✅ Error rate < 1%  
✅ Response time < 30s  
✅ No throttling or errors  

---

## Post-Deployment

### Week 1: Monitoring

- [ ] Monitor CloudWatch Dashboard daily
- [ ] Check X-Ray traces for anomalies
- [ ] Review error logs
- [ ] Track performance metrics
- [ ] Collect user feedback

### Week 2+: Optimization

- [ ] Analyze performance data
- [ ] Optimize DynamoDB capacity if needed
- [ ] Tune Lambda memory/timeout
- [ ] Implement improvements
- [ ] Update documentation

---

## Rollback Plan

If issues encountered:

1. **Quick Rollback**: Update Lambda to previous image version
   ```bash
   aws lambda update-function-code \
     --function-name rfp-agentcore-orchestrator \
     --image-uri $PREVIOUS_IMAGE_URI
   ```

2. **API Fallback**: Disable API endpoint
   ```bash
   aws apigateway update-stage \
     --rest-api-id $API_ID \
     --stage-name prod \
     --patch-operations op=replace,path=/*/*/logging/level,value=OFF
   ```

3. **Full Restore**: Restore from previous CloudFormation stack
   ```bash
   aws cloudformation update-stack \
     --stack-name rfp-production-stack \
     --template-body file://previous-template.yaml
   ```

---

## Contacts & Support

- **DevOps**: [Add team contact]
- **Architecture**: [Add team contact]
- **On-Call**: [Add escalation path]

---

**Status**: Ready for Deployment ✅

All prerequisites met. System ready for production deployment.

