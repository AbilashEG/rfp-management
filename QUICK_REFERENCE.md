# Quick Reference Card
## Essential Commands for RFP Agent Deployment

---

## **CRITICAL VARIABLES**

Save these values as you work:

```
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=689050397154
PROJECT_NAME=supplier-rfp-agent

# After setup - SAVE THESE:
API_ID=?
AGENTCORE_MEMORY_ID=?
AGENTCORE_AGENT_ID=?
COGNITO_USER_POOL_ID=?
COGNITO_APP_CLIENT_ID=?
```

---

## **DynamoDB Table Creation (One-Liners)**

```bash
# Table 1: Suppliers
aws dynamodb create-table --table-name rfp-suppliers --attribute-definitions AttributeName=supplier_id,AttributeType=S --key-schema AttributeName=supplier_id,KeyType=HASH --billing-mode PAY_PER_REQUEST --region us-east-1

# Table 2: Requests
aws dynamodb create-table --table-name rfp-requests --attribute-definitions AttributeName=rfp_id,AttributeType=S AttributeName=created_at,AttributeType=S --key-schema AttributeName=rfp_id,KeyType=HASH AttributeName=created_at,KeyType=RANGE --billing-mode PAY_PER_REQUEST --region us-east-1

# Table 3: Proposals
aws dynamodb create-table --table-name rfp-proposals --attribute-definitions AttributeName=proposal_id,AttributeType=S AttributeName=rfp_id,AttributeType=S --key-schema AttributeName=proposal_id,KeyType=HASH AttributeName=rfp_id,KeyType=RANGE --billing-mode PAY_PER_REQUEST --region us-east-1

# Table 4: Scores
aws dynamodb create-table --table-name rfp-scores --attribute-definitions AttributeName=score_id,AttributeType=S AttributeName=proposal_id,AttributeType=S --key-schema AttributeName=score_id,KeyType=HASH AttributeName=proposal_id,KeyType=RANGE --billing-mode PAY_PER_REQUEST --region us-east-1

# Verify all created
aws dynamodb list-tables --region us-east-1
```

---

## **S3 & Data Setup**

```bash
# Create bucket
aws s3api create-bucket --bucket rfp-documents-quadrasystems --region us-east-1

# Seed supplier data (from project root)
cd c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent
python setup/seed_data.py

# Verify suppliers loaded
aws dynamodb scan --table-name rfp-suppliers --region us-east-1 --query 'Items | length(@)'
```

---

## **IAM Role Setup**

```bash
# Create role
aws iam create-role --role-name rfp-agent-lambda-role --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' --region us-east-1

# Attach DynamoDB policy
aws iam put-role-policy --role-name rfp-agent-lambda-role --policy-name DynamoDBAccess --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["dynamodb:GetItem","dynamodb:PutItem","dynamodb:Query","dynamodb:Scan","dynamodb:UpdateItem"],"Resource":"arn:aws:dynamodb:us-east-1:689050397154:table/rfp-*"}]}' --region us-east-1

# Attach S3 policy
aws iam put-role-policy --role-name rfp-agent-lambda-role --policy-name S3Access --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:PutObject","s3:GetObject","s3:ListBucket"],"Resource":["arn:aws:s3:::rfp-documents-quadrasystems","arn:aws:s3:::rfp-documents-quadrasystems/*"]}]}' --region us-east-1

# Attach Bedrock policy
aws iam put-role-policy --role-name rfp-agent-lambda-role --policy-name BedrockAccess --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["bedrock:InvokeModel","bedrock-agent:InvokeAgent"],"Resource":"*"}]}' --region us-east-1

# Attach CloudWatch Logs policy
aws iam put-role-policy --role-name rfp-agent-lambda-role --policy-name CloudWatchLogs --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"arn:aws:logs:us-east-1:689050397154:*"}]}' --region us-east-1

# Verify
aws iam get-role --role-name rfp-agent-lambda-role --region us-east-1
```

---

## **Docker & ECR**

```bash
# Navigate to project root
cd c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent

# Build Docker image
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 689050397154.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repo (if not exists)
aws ecr create-repository --repository-name supplier-rfp-agent --region us-east-1

# Tag and push
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest

# Verify
aws ecr describe-images --repository-name supplier-rfp-agent --region us-east-1
```

---

## **Lambda Function**

```bash
# Create function
aws lambda create-function \
  --function-name rfp-agent-handler \
  --role arn:aws:iam::689050397154:role/rfp-agent-lambda-role \
  --code ImageUri=689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest \
  --package-type Image \
  --handler lambda.rfp_agent_handler.handler \
  --timeout 300 --memory-size 512 \
  --region us-east-1

# Update function
aws lambda update-function-code \
  --function-name rfp-agent-handler \
  --image-uri 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest \
  --region us-east-1

# Verify
aws lambda get-function --function-name rfp-agent-handler --region us-east-1
```

---

## **API Gateway**

```bash
# Create API
API_ID=$(aws apigateway create-rest-api \
  --name supplier-rfp-agent-api \
  --region us-east-1 \
  --query 'id' --output text)

echo "API ID: $API_ID"

# Get root ID
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region us-east-1 --query 'items[0].id' --output text)

# Create resource
RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part process-rfp \
  --region us-east-1 \
  --query 'id' --output text)

# Create method
aws apigateway put-method --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method POST --authorization-type NONE --region us-east-1

# Integrate with Lambda
aws apigateway put-integration --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method POST --type AWS_PROXY --integration-http-method POST --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler/invocations --region us-east-1

# Deploy
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod --region us-east-1

# Get endpoint
echo "API Endpoint: https://$API_ID.execute-api.us-east-1.amazonaws.com/prod/process-rfp"
```

---

## **AgentCore Setup**

```bash
# Create Knowledge Base (Memory)
MEMORY_ID=$(aws bedrock-agent create-knowledge-base \
  --name rfp-agent-memory \
  --description "Session memory for RFP Agent" \
  --region us-east-1 \
  --query 'knowledgeBase.knowledgeBaseId' --output text)

echo "AGENTCORE_MEMORY_ID: $MEMORY_ID"

# Create Agent (Runtime)
AGENT_ID=$(aws bedrock-agent create-agent \
  --agent-name supplier-rfp-agent \
  --agent-role-arn arn:aws:iam::689050397154:role/rfp-agent-lambda-role \
  --foundation-model amazon.nova-pro-v1:0 \
  --description "Supplier RFP Management Agent" \
  --region us-east-1 \
  --query 'agent.agentId' --output text)

echo "AGENTCORE_AGENT_ID: $AGENT_ID"

# Create Cognito User Pool
USER_POOL_ID=$(aws cognito-idp create-user-pool --pool-name rfp-agent-users --region us-east-1 --query 'UserPool.Id' --output text)

echo "COGNITO_USER_POOL_ID: $USER_POOL_ID"

# Create App Client
APP_CLIENT_ID=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-name rfp-agent-client \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --region us-east-1 \
  --query 'UserPoolClient.ClientId' --output text)

echo "COGNITO_APP_CLIENT_ID: $APP_CLIENT_ID"

# Create test user
aws cognito-idp admin-create-user --user-pool-id $USER_POOL_ID --username procure-manager-01 --temporary-password TempPassword123! --message-action SUPPRESS --region us-east-1

# Set permanent password
aws cognito-idp admin-set-user-password --user-pool-id $USER_POOL_ID --username procure-manager-01 --password PermanentPassword123! --permanent --region us-east-1
```

---

## **Testing**

```bash
# Local agent test
cd c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent
python -m agent.agent_runner

# Run unit tests
python -m pytest tests/test_tools.py -v

# Run end-to-end test
python -m pytest tests/test_agent_flow.py -v

# Get Cognito token
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id $COGNITO_USER_POOL_ID \
  --client-id $COGNITO_APP_CLIENT_ID \
  --auth-flow ADMIN_USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=procure-manager-01,PASSWORD=PermanentPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.AccessToken' --output text)

# Call API
curl -X POST https://$API_ID.execute-api.us-east-1.amazonaws.com/prod/process-rfp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "We need 500 brake sensors. Specs: High-precision ABS sensor, IP67, -40°C to 125°C, Deadline: 2026-09-30"}'
```

---

## **Monitoring & Debugging**

```bash
# View Lambda logs
aws logs tail /aws/lambda/rfp-agent-handler --follow --region us-east-1

# Check DynamoDB table size
aws dynamodb describe-table --table-name rfp-suppliers --region us-east-1 --query 'Table.ItemCount'

# List all RFPs
aws dynamodb scan --table-name rfp-requests --region us-east-1

# Get specific RFP
aws dynamodb get-item --table-name rfp-requests --key '{"rfp_id":{"S":"RFP-YYYYMMDD-XXXXXXXX"}}' --region us-east-1

# Check agent invocations
aws logs filter-log-events --log-group-name /aws/bedrock/rfp-agent --filter-pattern "invocation" --region us-east-1

# List metrics
aws cloudwatch list-metrics --namespace RFPAgent --region us-east-1
```

---

## **Cleanup (If Needed)**

```bash
# Delete Lambda function
aws lambda delete-function --function-name rfp-agent-handler --region us-east-1

# Delete API Gateway
aws apigateway delete-rest-api --rest-api-id $API_ID --region us-east-1

# Delete DynamoDB tables
aws dynamodb delete-table --table-name rfp-suppliers --region us-east-1
aws dynamodb delete-table --table-name rfp-requests --region us-east-1
aws dynamodb delete-table --table-name rfp-proposals --region us-east-1
aws dynamodb delete-table --table-name rfp-scores --region us-east-1

# Delete S3 bucket (must be empty first)
aws s3 rm s3://rfp-documents-quadrasystems --recursive
aws s3api delete-bucket --bucket rfp-documents-quadrasystems

# Delete IAM role (must remove policies first)
aws iam delete-role-policy --role-name rfp-agent-lambda-role --policy-name DynamoDBAccess --region us-east-1
aws iam delete-role --role-name rfp-agent-lambda-role --region us-east-1

# Delete Cognito User Pool
aws cognito-idp delete-user-pool --user-pool-id $USER_POOL_ID --region us-east-1

# Delete Agent
aws bedrock-agent delete-agent --agent-id $AGENT_ID --region us-east-1
```

---

## **Environment Setup (One-Time)**

```powershell
# PowerShell - set AWS region
$env:AWS_REGION = "us-east-1"
$env:AWS_ACCOUNT_ID = "689050397154"

# Or permanently in Windows:
# Settings > System > Advanced system settings > Environment Variables
# Add: AWS_REGION = us-east-1
#      AWS_ACCOUNT_ID = 689050397154
```

---

## **Useful Links**

- **AWS Bedrock Agents:** https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
- **Cognito:** https://docs.aws.amazon.com/cognito/latest/developerguide/
- **DynamoDB:** https://docs.aws.amazon.com/dynamodb/latest/developerguide/
- **Lambda:** https://docs.aws.amazon.com/lambda/latest/dg/
- **API Gateway:** https://docs.aws.amazon.com/apigateway/latest/developerguide/

---

## **Support**

- **Deployment Guide:** AWS_DEPLOYMENT_GUIDE.md
- **AgentCore Setup:** AGENTCORE_SETUP_GUIDE.md
- **Progress Tracking:** DEPLOYMENT_CHECKLIST.md
- **Backend Prompt:** KIRO_RFP_Backend_Prompt.md
- **Requirements:** .kiro/specs/supplier-rfp-agent/requirements.md
- **Project README:** supplier-rfp-agent/README.md

