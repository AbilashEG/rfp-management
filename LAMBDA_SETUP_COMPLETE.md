# Lambda Setup - Complete Details
## Docker Image Build → Lambda Creation

---

## **Current Status**

✅ **Completed:**
- S3 bucket: `rfp-documents-quadrasystems`
- DynamoDB tables: All 4 tables
- IAM role: `rfp-agent-lambda-role` with all permissions

⏳ **Pending:**
- Docker image build (via CloudShell)
- Lambda function creation

---

## **What is Happening**

1. **Local → ZIP**: Your code zipped as `supplier-rfp-agent.zip`
2. **CloudShell Upload**: ZIP uploaded to CloudShell
3. **Docker Build**: Image built from `lambda/Dockerfile`
4. **ECR Push**: Image pushed to your ECR repository
5. **Lambda Create**: Lambda function created pointing to ECR image

---

## **Files Needed**

### Already Created:
- ✅ `supplier-rfp-agent.zip` (in your RFP MANAGEMENT folder)

### Use These Guides:
- 📄 `CLOUDSHELL_DOCKER_BUILD.md` (detailed step-by-step)
- 📄 `CLOUDSHELL_QUICK_STEPS.txt` (quick reference)

---

## **Lambda Configuration Details**

| Property | Value | Purpose |
|----------|-------|---------|
| **Function Name** | `rfp-agent-handler` | Unique identifier |
| **Handler** | `lambda.rfp_agent_handler.handler` | Entry point in code |
| **Runtime** | Python 3.12 (container) | Language environment |
| **Package Type** | Image | Docker container-based |
| **Memory** | 512 MB | RAM allocated |
| **Timeout** | 300 seconds (5 min) | Max execution time |
| **IAM Role** | `rfp-agent-lambda-role` | Permissions to access AWS services |
| **Image Source** | ECR | Docker registry |
| **Image URI** | `689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest` | Full image path |
| **Region** | us-east-1 | AWS region |

---

## **Environment Variables**

Lambda will be configured with:

```
REGION = us-east-1
BEDROCK_MODEL_ID = amazon.nova-pro-v1:0
```

These are read by your `config.py` at runtime.

---

## **What the Lambda Handler Does**

Location: `lambda/rfp_agent_handler.py`

**Function:** `handler(event, context)`

**Input:**
```json
{
  "body": {
    "message": "We need 500 brake sensors..."
  }
}
```

**Process:**
1. Parse incoming request
2. Validate message field
3. Call the Strands Agent with the message
4. Get agent response (full RFP lifecycle)
5. Return response with metadata

**Output:**
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
  },
  "body": {
    "response": "RFP lifecycle completed successfully...",
    "rfp_id": "RFP-20260612-ABC123DE",
    "suppliers_matched": 3,
    "top_recommendation": "SUP003 (AutoSensor Global)"
  }
}
```

---

## **Docker Image Details**

**Dockerfile:** `lambda/Dockerfile`

```dockerfile
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install dependencies
RUN pip install -r requirements.txt

# Copy source code
COPY . ${LAMBDA_TASK_ROOT}/

# Set handler
CMD [ "lambda.rfp_agent_handler.handler" ]
```

**Image Size:** ~500 MB (Python 3.12 + dependencies)

---

## **IAM Permissions Applied**

Your Lambda role (`rfp-agent-lambda-role`) has these permissions:

### DynamoDB
```
dynamodb:GetItem
dynamodb:PutItem
dynamodb:Query
dynamodb:Scan
dynamodb:UpdateItem
```
**On:** `arn:aws:dynamodb:us-east-1:689050397154:table/rfp-*`

### S3
```
s3:PutObject
s3:GetObject
s3:ListBucket
```
**On:** `arn:aws:s3:::rfp-documents-quadrasystems` and `/*`

### Bedrock
```
bedrock:InvokeModel
bedrock-agent:InvokeAgent
```
**On:** `*` (all Bedrock resources)

### CloudWatch Logs
```
logs:CreateLogGroup
logs:CreateLogStream
logs:PutLogEvents
```
**On:** `arn:aws:logs:us-east-1:689050397154:*`

---

## **Complete Setup Flow**

```
┌─────────────────────────────────────────────────────┐
│ Step 1: Prepare Local Code                          │
│ → Code already exists in supplier-rfp-agent/        │
│ → Zipped as supplier-rfp-agent.zip                  │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ Step 2: CloudShell - Extract & Build                │
│ → unzip supplier-rfp-agent.zip                      │
│ → cd supplier-rfp-agent                             │
│ → docker build -t supplier-rfp-agent:latest ...     │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ Step 3: CloudShell - Push to ECR                    │
│ → docker login to ECR                               │
│ → docker tag supplier-rfp-agent:latest ... (ECR)    │
│ → docker push 689050397154.dkr.ecr...               │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ Step 4: CloudShell - Create Lambda                  │
│ → aws lambda create-function                        │
│ → --code ImageUri=689050397154.dkr.ecr...           │
│ → --function-name rfp-agent-handler                 │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ ✅ Lambda Function Ready                            │
│ → Function: rfp-agent-handler (Active)              │
│ → Handler: lambda.rfp_agent_handler.handler         │
│ → Can now be invoked via API Gateway                │
└─────────────────────────────────────────────────────┘
```

---

## **Quick Command Summary**

**In CloudShell (copy-paste in order):**

```bash
# 1. Extract
unzip supplier-rfp-agent.zip

# 2. Navigate
cd supplier-rfp-agent

# 3. Build (wait 3-5 min)
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .

# 4. Login ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 689050397154.dkr.ecr.us-east-1.amazonaws.com

# 5. Tag
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest

# 6. Push (wait 5-10 min)
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest

# 7. Create Lambda
aws lambda create-function \
  --function-name rfp-agent-handler \
  --role arn:aws:iam::689050397154:role/rfp-agent-lambda-role \
  --code ImageUri=689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest \
  --package-type Image \
  --handler lambda.rfp_agent_handler.handler \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables="{REGION=us-east-1,BEDROCK_MODEL_ID=amazon.nova-pro-v1:0}" \
  --region us-east-1

# 8. Verify
aws lambda get-function --function-name rfp-agent-handler --region us-east-1
```

---

## **After Lambda is Created**

✅ **What Works:**
- Lambda can read/write to DynamoDB
- Lambda can upload/download from S3
- Lambda can invoke Bedrock models
- Lambda logs to CloudWatch

❌ **Not Yet Available:**
- API Gateway endpoint (need to create separately)
- AgentCore integration (need to set up separately)

---

## **Next Steps**

After Lambda creation:

1. **Create API Gateway** (optional for testing)
   - See: `AWS_DEPLOYMENT_GUIDE.md` PHASE 7
   
2. **Set up AgentCore** (if using Bedrock agents)
   - See: `AGENTCORE_SETUP_GUIDE.md`

3. **Test Lambda Invocation** (manual test)
   ```bash
   aws lambda invoke \
     --function-name rfp-agent-handler \
     --payload '{"body":"{\"message\":\"We need 500 brake sensors\"}"}' \
     --region us-east-1 \
     response.json
   
   cat response.json
   ```

---

## **Monitoring & Logs**

**View Lambda Logs in CloudWatch:**

```bash
# Real-time logs
aws logs tail /aws/lambda/rfp-agent-handler --follow --region us-east-1

# View logs from specific time
aws logs filter-log-events \
  --log-group-name /aws/lambda/rfp-agent-handler \
  --start-time $(date -d '5 minutes ago' +%s)000 \
  --region us-east-1
```

**View Lambda Metrics:**

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=rfp-agent-handler \
  --start-time 2026-06-12T00:00:00Z \
  --end-time 2026-06-13T00:00:00Z \
  --period 3600 \
  --statistics Average,Maximum \
  --region us-east-1
```

---

## **Lambda Cost Estimate**

**With pay-per-use (US East 1):**

- Memory: 512 MB
- Average duration: 20 seconds per invocation
- Pricing: $0.0000002 per GB-second + $0.20 per 1M requests

**For 100 requests/day:**
- Compute: 100 × 20s × 512MB/1024 = 1000 GB-seconds = $0.02/day
- Requests: 100 × $0.20/1M = ~$0.00/day
- **Total: ~$0.60/month**

---

## **Troubleshooting**

### Lambda Errors in CloudWatch

**"ModuleNotFoundError: No module named 'agent'"**
- Solution: Ensure all source files are included in Docker image
- Check: Dockerfile copies all source code

**"DynamoDB: AccessDeniedException"**
- Solution: Verify IAM role has DynamoDB permissions
- Check: `aws iam get-role-policy --role-name rfp-agent-lambda-role --policy-name DynamoDBAccess`

**"Bedrock: ThrottlingException"**
- Solution: Too many concurrent invocations
- Increase Lambda concurrency limit

**"Lambda timeout after 300 seconds"**
- Solution: Increase timeout to 600 seconds
- Run: `aws lambda update-function-configuration --function-name rfp-agent-handler --timeout 600 --region us-east-1`

---

## **Success Criteria**

Lambda is ready when:

```bash
aws lambda get-function --function-name rfp-agent-handler --region us-east-1
```

Returns:
```json
{
  "Configuration": {
    "FunctionName": "rfp-agent-handler",
    "State": "Active",
    "CodeSha256": "...",
    "Timeout": 300,
    "MemorySize": 512,
    "PackageType": "Image"
  }
}
```

---

## **Files Reference**

| File | Purpose |
|------|---------|
| `CLOUDSHELL_DOCKER_BUILD.md` | Detailed step-by-step CloudShell guide |
| `CLOUDSHELL_QUICK_STEPS.txt` | Quick reference for commands |
| `lambda/rfp_agent_handler.py` | Lambda handler code |
| `lambda/Dockerfile` | Docker image definition |
| `supplier-rfp-agent.zip` | Zipped source code |

---

## **Summary**

✅ **What you have:**
- Complete source code (26 Python files)
- Dockerfile ready
- IAM role with permissions
- ECR repository created
- ZIP file ready for CloudShell

⏳ **What you're doing:**
- Build Docker image in CloudShell
- Push to ECR
- Create Lambda function

✅ **Result:**
- Lambda function `rfp-agent-handler` (Active)
- Ready to integrate with API Gateway or AgentCore

**Time remaining:** 15-25 minutes (mostly waiting for build/push)

---

**Next:** Open `CLOUDSHELL_DOCKER_BUILD.md` and follow the steps. 🚀

