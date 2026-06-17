# Next Steps: Deploy Agent Runtime & Connect Gateway

**Status**: Ready to Execute  
**Duration**: ~1 hour  
**Output**: Production-ready API Gateway + Observability + Memory

---

## What You Need To Do

### Option 1: Execute Deployment (Recommended)

Run these scripts to deploy the agent with API Gateway and observability:

#### Step 1: Deploy API Gateway (10 minutes)
```bash
bash setup-api-gateway.sh us-east-1
```
**Output**: HTTP endpoint like `https://XXXXXXXX.execute-api.us-east-1.amazonaws.com/prod/process-rfp`

#### Step 2: Setup Observability (15 minutes)
```bash
bash setup-observability.sh us-east-1
```
**Output**: X-Ray tracing + CloudWatch dashboards + Alarms

#### Step 3: Verify Memory Table
```bash
aws dynamodb describe-table --table-name agentcore-memory-v2 --region us-east-1
```
**Output**: Memory table with session_id as primary key

#### Step 4: Run Deployment Checklist
Follow `DEPLOYMENT_CHECKLIST.md` for:
- [ ] Verify all 7 Lambdas deployed
- [ ] Test API Gateway endpoint
- [ ] Test tool invocation
- [ ] Test session persistence
- [ ] Check observability

---

### Option 2: Manual Deployment

If you prefer step-by-step:

1. **Create API Gateway**
   ```bash
   aws apigateway create-rest-api --name rfp-agent-api --region us-east-1
   ```

2. **Create /process-rfp Resource**
   - Create resource under root
   - Add POST method
   - Link to rfp-agentcore-orchestrator Lambda

3. **Enable Tracing**
   ```bash
   aws lambda update-function-configuration \
       --function-name rfp-agentcore-orchestrator \
       --tracing-config Mode=Active \
       --region us-east-1
   ```

4. **Create CloudWatch Dashboard**
   - Add Lambda metrics
   - Add DynamoDB metrics
   - Add error tracking

5. **Deploy & Test**
   - Deploy API to prod stage
   - Test endpoint with curl
   - Verify logs in CloudWatch
   - Verify traces in X-Ray

---

## What Gets Deployed

### API Gateway
- **Endpoint**: `https://API_ID.execute-api.us-east-1.amazonaws.com/prod/process-rfp`
- **Method**: POST
- **Authentication**: Cognito (ready to integrate)
- **CORS**: Enabled for web/mobile clients

### Observability Stack
- **X-Ray Tracing**: Full request flow visualization
- **CloudWatch Logs**: Structured logging (30-day retention)
- **CloudWatch Dashboard**: Real-time metrics
- **CloudWatch Alarms**: Error, throttle, performance alerts

### Memory System
- **Session Storage**: agentcore-memory-v2 DynamoDB table
- **Conversation History**: Persists across requests
- **TTL**: 24-hour auto-cleanup
- **Data**: User ID, requirement, workflow state

### Tool Integration
- All 6 tools connected via Lambda invocation
- Parallel/sequential execution based on workflow
- Error handling and retries
- Logging and tracing

---

## Architecture After Deployment

```
┌─────────────────────────┐
│   Client Application    │
│   (Web/Mobile/API)      │
└──────────────┬──────────┘
               │ HTTP POST
               ↓
┌─────────────────────────────────────────┐
│   API Gateway (rate limit + auth)       │
│   https://xxx.execute-api.us-east-1...  │
└──────────────┬──────────────────────────┘
               │ Invoke
               ↓
┌─────────────────────────────────────────┐
│   Orchestrator Agent (Bedrock)          │
│   rfp-agentcore-orchestrator            │
│   • Amazon Nova Pro LLM                  │
│   • Tool calling logic                   │
│   • Approval decisions                   │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────────────────────────┬──────┐
       │                                    │      │
       ↓                                    ↓      ↓
   ┌──────────────────────────────┐  ┌──────────────────────┐
   │   DynamoDB                   │  │   S3 Bucket          │
   │ • rfp-suppliers              │  │ • RFP documents      │
   │ • rfp-requests               │  │ • Signed URLs        │
   │ • rfp-proposals              │  │                      │
   │ • rfp-scores                 │  │                      │
   │ • agentcore-memory-v2 (NEW)  │  │                      │
   └──────────────────────────────┘  └──────────────────────┘

┌─────────────────────────────────────────┐
│   Observability (NEW)                   │
│   • X-Ray Service Map                   │
│   • CloudWatch Logs                     │
│   • CloudWatch Dashboard                │
│   • Performance Alarms                  │
└─────────────────────────────────────────┘
```

---

## Testing After Deployment

### Test 1: Direct API Call
```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/process-rfp \
  -H "Content-Type: application/json" \
  -d '{"body": "{\"message\": \"Create RFP for sensors\"}"}'
```
Expected: 200 status with workflow success

### Test 2: Session Persistence
```bash
# First request
curl -X POST ... -d '{"body": "{\"message\": \"Create RFP\"}"}'
# Extract session_id from response

# Second request with same session
curl -X POST ... -d '{"body": "{\"session_id\": \"xxx\", \"message\": \"Add budget\"}"}'
# Verify conversation history includes both messages
```

### Test 3: Check Observability
```bash
# View CloudWatch logs
aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow

# View X-Ray traces
aws xray get-service-graph --start-time ... --end-time ...

# Check dashboard metrics
aws cloudwatch list-metrics --namespace AWS/Lambda
```

---

## Production Checklist

Before going live with real users:

- [ ] API endpoint responding < 30s
- [ ] All 6 tools invoked successfully
- [ ] Session persistence working
- [ ] Error rate < 1%
- [ ] CloudWatch logs capturing all events
- [ ] X-Ray traces visible
- [ ] Dashboard metrics updating
- [ ] Alarms triggered and working
- [ ] Cognito integration configured
- [ ] Least privilege IAM roles
- [ ] DynamoDB capacity sufficient
- [ ] S3 bucket versioning enabled
- [ ] Backup/recovery plan documented
- [ ] On-call procedures documented
- [ ] Runbooks created
- [ ] Team trained on monitoring

---

## Key Files

### Deployment Scripts
- `setup-api-gateway.sh` - Creates API Gateway endpoint
- `setup-observability.sh` - Enables X-Ray, CloudWatch, alarms
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step verification

### Architecture Documentation
- `AGENT_RUNTIME_DEPLOYMENT.md` - Complete design & implementation
- `NEXT_STEPS.md` - This file
- `DEPLOYMENT_CHECKLIST.md` - Pre-flight checks

### Reference Files
- `BACKEND_INTEGRATION_COMPLETE.md` - DynamoDB integration
- `CONTAINER_DEPLOYMENT.md` - Lambda container deployment
- `START_HERE.md` - Overview

---

## Time Estimate

| Phase | Duration | Status |
|-------|----------|--------|
| API Gateway setup | 10 min | Ready to run |
| Observability setup | 15 min | Ready to run |
| Memory verification | 10 min | Automated |
| Tool integration testing | 15 min | Automated |
| End-to-end testing | 5 min | Manual |
| **Total** | **~1 hour** | **Ready** |

---

## Success Criteria

✅ API Gateway endpoint responding  
✅ Orchestrator processing requests  
✅ All 6 tools invoked per workflow  
✅ Memory persisting sessions  
✅ CloudWatch logs capturing events  
✅ X-Ray showing full trace  
✅ Dashboard displaying metrics  
✅ Alarms configured and tested  
✅ Error rate < 1%  
✅ Response time < 30s  

---

## What Happens Next

### Immediate (Today)
1. Run deployment scripts
2. Verify endpoints work
3. Test with sample data
4. Check observability

### Short Term (This Week)
1. Integrate Cognito authentication
2. Set up backup/recovery
3. Train team on operations
4. Document runbooks

### Medium Term (This Month)
1. Performance tuning
2. Load testing
3. Security audit
4. User acceptance testing

### Long Term (Next Quarter)
1. Cost optimization
2. Feature enhancements
3. Capacity planning
4. Disaster recovery tests

---

## Support

### Logs & Tracing
- **CloudWatch Logs**: `/aws/lambda/rfp-agentcore-orchestrator`
- **X-Ray**: Service map shows request flow
- **Dashboard**: `rfp-agent-dashboard` in CloudWatch

### Common Issues

**Issue**: API endpoint returns 500
- **Action**: Check CloudWatch logs for error
- **Solution**: Update Lambda configuration

**Issue**: Session not persisting
- **Action**: Verify agentcore-memory-v2 table has data
- **Solution**: Check DynamoDB write permissions

**Issue**: Tools not invoked
- **Action**: Check X-Ray service map
- **Solution**: Verify tool Lambda roles have invoke permissions

**Issue**: Slow response time
- **Action**: Check CloudWatch metrics
- **Solution**: Increase Lambda memory or DynamoDB capacity

---

## Commit History

```
8af8fcc - Add: Agent Runtime Deployment - API Gateway, Observability
ffc42eb - Add: Quick reference guide for Task 7 completion
3387570 - Complete: Task 7 - Backend integration verification
583e875 - Verify: All 6 Lambda tools operational with real DynamoDB
```

---

## Next Action

### 👉 Execute Deployment Now
```bash
bash setup-api-gateway.sh us-east-1
bash setup-observability.sh us-east-1
```

### 👉 Follow Deployment Checklist
Open `DEPLOYMENT_CHECKLIST.md` and complete each phase

### 👉 Test API Gateway
Use curl or Postman to test the deployed endpoint

---

## Questions?

Refer to:
- **Architecture**: `AGENT_RUNTIME_DEPLOYMENT.md`
- **Deployment**: `DEPLOYMENT_CHECKLIST.md`
- **Backend**: `BACKEND_INTEGRATION_COMPLETE.md`
- **Lambda**: `CONTAINER_DEPLOYMENT.md`

---

**Status**: ✅ All components ready for deployment

Your RFP Management System is ready to go live with:
- Production API Gateway
- Full observability
- Session memory
- Tool integration

Execute the deployment scripts and you'll be ready to serve real users.

