# AWS Stack Deployment & AgentCore Setup Guide
## Supplier RFP Management Agentic AI Backend

---

## **PHASE 1: AWS STACK DEPLOYMENT (Manual via AWS CLI)**

### Prerequisites
- ✅ AWS CLI installed and configured (`aws configure`)
- ✅ Your AWS Account ID: `689050397154` (from config.py)
- ✅ AWS Region: `us-east-1` (configured in config.py)
- ✅ IAM permissions: DynamoDB, S3, Lambda, ECR, IAM, Bedrock, Cognito

---

## **STEP 1: Create DynamoDB Tables**

Run each command below in order. These create the 4 tables required by the RFP system.

### Table 1: rfp-suppliers

```bash
aws dynamodb create-table \
  --table-name rfp-suppliers \
  --attribute-definitions \
    AttributeName=supplier_id,AttributeType=S \
  --key-schema \
    AttributeName=supplier_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

**Expected output:** Table created successfully.

---

### Table 2: rfp-requests

```bash
aws dynamodb create-table \
  --table-name rfp-requests \
  --attribute-definitions \
    AttributeName=rfp_id,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema \
    AttributeName=rfp_id,KeyType=HASH \
    AttributeName=created_at,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

---

### Table 3: rfp-proposals

```bash
aws dynamodb create-table \
  --table-name rfp-proposals \
  --attribute-definitions \
    AttributeName=proposal_id,AttributeType=S \
    AttributeName=rfp_id,AttributeType=S \
  --key-schema \
    AttributeName=proposal_id,KeyType=HASH \
    AttributeName=rfp_id,KeyType=RANGE \
  --global-secondary-indexes \
    IndexName=rfp_id-index,Keys=[{AttributeName=rfp_id,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

---

### Table 4: rfp-scores

```bash
aws dynamodb create-table \
  --table-name rfp-scores \
  --attribute-definitions \
    AttributeName=score_id,AttributeType=S \
    AttributeName=proposal_id,AttributeType=S \
  --key-schema \
    AttributeName=score_id,KeyType=HASH \
    AttributeName=proposal_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

---

### Verify Tables Created

```bash
aws dynamodb list-tables --region us-east-1
```

**Expected output:** All 4 tables should be listed (rfp-suppliers, rfp-requests, rfp-proposals, rfp-scores).

---

## **STEP 2: Create S3 Bucket**

```bash
aws s3api create-bucket \
  --bucket rfp-documents-quadrasystems \
  --region us-east-1 \
  --create-bucket-configuration LocationConstraint=us-east-1
```

---

## **STEP 3: Seed Supplier Data into DynamoDB**

From your project root directory (`c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent`), run:

```powershell
cd c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent
python setup/seed_data.py
```

**Expected output:** All 8 suppliers inserted successfully into `rfp-suppliers` table.

---

## **STEP 4: Create IAM Role for Lambda**

```bash
cat > /tmp/trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name rfp-agent-lambda-role \
  --assume-role-policy-document file:///tmp/trust-policy.json \
  --region us-east-1
```

---

### Attach Permissions to Lambda Role

```bash
# DynamoDB permissions
aws iam put-role-policy \
  --role-name rfp-agent-lambda-role \
  --policy-name DynamoDBAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem"
        ],
        "Resource": "arn:aws:dynamodb:us-east-1:689050397154:table/rfp-*"
      }
    ]
  }' \
  --region us-east-1

# S3 permissions
aws iam put-role-policy \
  --role-name rfp-agent-lambda-role \
  --policy-name S3Access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::rfp-documents-quadrasystems",
          "arn:aws:s3:::rfp-documents-quadrasystems/*"
        ]
      }
    ]
  }' \
  --region us-east-1

# Bedrock permissions
aws iam put-role-policy \
  --role-name rfp-agent-lambda-role \
  --policy-name BedrockAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "bedrock:InvokeModel",
          "bedrock-agent:InvokeAgent"
        ],
        "Resource": "*"
      }
    ]
  }' \
  --region us-east-1

# SES permissions (for future live mode)
aws iam put-role-policy \
  --role-name rfp-agent-lambda-role \
  --policy-name SESAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ],
        "Resource": "*"
      }
    ]
  }' \
  --region us-east-1

# CloudWatch Logs permissions
aws iam put-role-policy \
  --role-name rfp-agent-lambda-role \
  --policy-name CloudWatchLogs \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "arn:aws:logs:us-east-1:689050397154:*"
      }
    ]
  }' \
  --region us-east-1
```

**Verify:**
```bash
aws iam get-role-policy \
  --role-name rfp-agent-lambda-role \
  --policy-name DynamoDBAccess \
  --region us-east-1
```

---

## **STEP 5: Create ECR Repository**

```bash
aws ecr create-repository \
  --repository-name supplier-rfp-agent \
  --region us-east-1
```

**Expected output:** ECR repository created. Note the URI: `689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent`

---

## **STEP 6: Build and Push Docker Image to ECR**

From your project root:

```powershell
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 689050397154.dkr.ecr.us-east-1.amazonaws.com

# Build Docker image
cd c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .

# Tag for ECR
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest

# Push to ECR
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

---

## **STEP 7: Create Lambda Function**

```bash
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
```

**Expected output:** Lambda function created successfully.

---

## **STEP 8: Create API Gateway**

### Create REST API

```bash
API_ID=$(aws apigateway create-rest-api \
  --name supplier-rfp-agent-api \
  --description "API for Supplier RFP Management Agent" \
  --region us-east-1 \
  --query 'id' \
  --output text)

echo "API ID: $API_ID"
```

Save the API ID.

---

### Create Resource

```bash
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region us-east-1 \
  --query 'items[0].id' \
  --output text)

RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part process-rfp \
  --region us-east-1 \
  --query 'id' \
  --output text)

echo "Resource ID: $RESOURCE_ID"
```

---

### Create Method

```bash
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --region us-east-1
```

---

### Integrate with Lambda

```bash
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler/invocations \
  --region us-east-1
```

---

### Deploy API

```bash
DEPLOYMENT_ID=$(aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region us-east-1 \
  --query 'id' \
  --output text)

echo "Deployment ID: $DEPLOYMENT_ID"
```

**API Endpoint:** `https://{API_ID}.execute-api.us-east-1.amazonaws.com/prod/process-rfp`

---

## **PHASE 2: AgentCore Setup**

### What is AgentCore?

AgentCore is AWS Bedrock's orchestration platform with 6 pillars:
1. **Runtime** — Agent execution engine
2. **Memory** — Session persistence
3. **Gateway (MCP)** — Tool interface
4. **Observability** — Logging & metrics
5. **Policy** — Human approval gates
6. **Identity** — Cognito authentication

---

### AgentCore Deployment Steps

#### Step 1: Create AgentCore Memory

This persists session state across invocations.

```bash
aws bedrock-agent create-knowledge-base \
  --name rfp-agent-memory \
  --description "Session memory for RFP Agent" \
  --region us-east-1
```

**Output:** Note the `knowledgeBaseId` (this is your `AGENTCORE_MEMORY_ID`).

---

#### Step 2: Register Agent with AgentCore Runtime

```bash
aws bedrock-agent create-agent \
  --agent-name rfp-agent \
  --agent-role-arn arn:aws:iam::689050397154:role/rfp-agent-lambda-role \
  --description "RFP Management Agent" \
  --foundation-model amazon.nova-pro-v1:0 \
  --instruction "You are an intelligent Supplier RFP Management Agent for automotive and manufacturing procurement." \
  --region us-east-1
```

**Output:** Note the `agentId` (this is your `AGENTCORE_AGENT_ID`).

---

#### Step 3: Register Tools with AgentCore Gateway (MCP)

For each of the 6 tools, register them:

```bash
AGENT_ID="<your-agent-id-from-step-2>"

# Tool 1: Supplier Lookup
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name SupplierLookupActionGroup \
  --description "Lookup suppliers by category and region" \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1

# Tool 2: RFP Generator
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name RFPGeneratorActionGroup \
  --description "Generate RFP documents" \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1

# Tool 3: Email Dispatch
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name EmailDispatchActionGroup \
  --description "Dispatch RFP emails to suppliers" \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1

# Tool 4: Proposal Fetch
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name ProposalFetchActionGroup \
  --description "Fetch supplier proposals" \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1

# Tool 5: Scoring
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name ScoringActionGroup \
  --description "Score proposals using multi-criteria evaluation" \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1

# Tool 6: Recommendation
aws bedrock-agent create-agent-action-group \
  --agent-id $AGENT_ID \
  --action-group-name RecommendationActionGroup \
  --description "Generate ranked supplier recommendations" \
  --action-group-executor lambda:arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler \
  --region us-east-1
```

---

#### Step 4: Set Up AgentCore Policy (Human Approval Gate)

Create a policy rule that triggers human approval when `approval_required` is True:

```bash
AGENT_ID="<your-agent-id-from-step-2>"

aws bedrock-agent create-agent-policy \
  --agent-id $AGENT_ID \
  --policy-name RFPApprovalPolicy \
  --policy-document '{
    "version": "1.0",
    "rules": [
      {
        "name": "require-approval-on-risk-flags",
        "condition": "approval_required == true",
        "action": "halt_and_wait_for_approval",
        "approver_arn": "arn:aws:iam::689050397154:role/rfp-approval-gate"
      }
    ]
  }' \
  --region us-east-1
```

---

#### Step 5: Enable Observability (CloudWatch Metrics)

```bash
AGENT_ID="<your-agent-id-from-step-2>"

aws cloudwatch put-metric-alarm \
  --alarm-name rfp-agent-errors \
  --alarm-description "Alert on RFP Agent execution errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --region us-east-1
```

---

#### Step 6: Configure Cognito Authentication

```bash
# Create Cognito User Pool (if not already done)
USER_POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name rfp-agent-users \
  --region us-east-1 \
  --query 'UserPool.Id' \
  --output text)

echo "User Pool ID: $USER_POOL_ID"

# Create App Client
APP_CLIENT_ID=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-name rfp-agent-client \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --region us-east-1 \
  --query 'UserPoolClient.ClientId' \
  --output text)

echo "App Client ID: $APP_CLIENT_ID"
```

**Update config.py with these values.**

---

## **PHASE 3: Update config.py with AgentCore IDs**

After completing the AgentCore setup, update your `config.py`:

```python
# config.py

# ... existing config ...

# AgentCore — fill after AgentCore Memory + Runtime are created
AGENTCORE_MEMORY_ID = "kb-xxxxxxxxxxxxxxxx"    # from Step 1
AGENTCORE_AGENT_ID  = "agent-xxxxxxxxxxxxxxxx" # from Step 2

# Cognito
COGNITO_USER_POOL_ID  = "us-east-1_xxxxxxxxx"  # from Step 6
COGNITO_APP_CLIENT_ID = "xxxxxxxxxxxxxxxx"     # from Step 6
```

---

## **PHASE 4: Test the Full Stack**

### Local Test (before deployment)

```powershell
cd c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent

# Test agent runner locally
python -m agent.agent_runner

# Run test suite
python -m pytest tests/ -v
```

---

### API Test (via API Gateway)

```bash
API_ENDPOINT="https://{API_ID}.execute-api.us-east-1.amazonaws.com/prod/process-rfp"

curl -X POST $API_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{
    "message": "We need 500 units of brake sensors. Specs: High-precision ABS wheel speed sensor, IP67 rated, operating temp -40°C to 125°C. Deadline: 2026-09-30."
  }'
```

**Expected Response:**
```json
{
  "response": "RFP lifecycle completed successfully. RFP-20250112-XXXXXXXX generated and sent to 3 suppliers. 3 proposals received and scored. Top recommendation: SUP003 (AutoSensor Global) with score 97.5/100. Approval status: ✅ No critical flags."
}
```

---

## **PHASE 5: Deployment Checklist**

- [ ] All 4 DynamoDB tables created
- [ ] S3 bucket created
- [ ] Supplier seed data loaded
- [ ] Lambda IAM role created with all permissions
- [ ] ECR repository created
- [ ] Docker image built and pushed to ECR
- [ ] Lambda function created
- [ ] API Gateway created and deployed
- [ ] AgentCore Memory created (KB)
- [ ] AgentCore Agent registered
- [ ] 6 tools registered via AgentCore Gateway
- [ ] AgentCore Policy approval gate configured
- [ ] CloudWatch metrics configured
- [ ] Cognito User Pool and App Client created
- [ ] config.py updated with all AgentCore IDs
- [ ] Local tests passing
- [ ] API Gateway test successful

---

## **Troubleshooting**

### Issue: "Missing required parameter: region"
**Solution:** Ensure all AWS CLI commands include `--region us-east-1`

### Issue: Lambda timeout during agent invocation
**Solution:** Increase Lambda timeout from 300s to 600s:
```bash
aws lambda update-function-configuration \
  --function-name rfp-agent-handler \
  --timeout 600 \
  --region us-east-1
```

### Issue: DynamoDB table still creating
**Solution:** Wait 1-2 minutes, check status:
```bash
aws dynamodb describe-table --table-name rfp-suppliers --region us-east-1
```

### Issue: Docker build fails
**Solution:** Ensure you're in the correct directory:
```bash
cd c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent
```

---

## **Support**

For detailed documentation, refer to:
- Backend Prompt: `KIRO_RFP_Backend_Prompt.md`
- Requirements: `.kiro/specs/supplier-rfp-agent/requirements.md`
- README: `supplier-rfp-agent/README.md`

