#!/bin/bash
# Quick-start deployment script for RFP Agent
# Run this from project root: bash scripts/deploy.sh

set -e

REGION="us-east-1"
ACCOUNT_ID="689050397154"
PROJECT_NAME="supplier-rfp-agent"

echo "============================================"
echo "RFP Agent AWS Deployment Script"
echo "============================================"
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# ============================================
# STEP 1: Create DynamoDB Tables
# ============================================
log_info "Creating DynamoDB Tables..."

create_table() {
    local table_name=$1
    local key_schema=$2
    local attr_defs=$3
    
    aws dynamodb create-table \
        --table-name "$table_name" \
        --attribute-definitions $attr_defs \
        --key-schema $key_schema \
        --billing-mode PAY_PER_REQUEST \
        --region $REGION 2>/dev/null || log_info "Table $table_name already exists"
    
    log_success "Table: $table_name"
}

create_table "rfp-suppliers" \
    "AttributeName=supplier_id,KeyType=HASH" \
    "AttributeName=supplier_id,AttributeType=S"

create_table "rfp-requests" \
    "AttributeName=rfp_id,KeyType=HASH AttributeName=created_at,KeyType=RANGE" \
    "AttributeName=rfp_id,AttributeType=S AttributeName=created_at,AttributeType=S"

create_table "rfp-proposals" \
    "AttributeName=proposal_id,KeyType=HASH AttributeName=rfp_id,KeyType=RANGE" \
    "AttributeName=proposal_id,AttributeType=S AttributeName=rfp_id,AttributeType=S"

create_table "rfp-scores" \
    "AttributeName=score_id,KeyType=HASH AttributeName=proposal_id,KeyType=RANGE" \
    "AttributeName=score_id,AttributeType=S AttributeName=proposal_id,AttributeType=S"

# ============================================
# STEP 2: Create S3 Bucket
# ============================================
log_info "Creating S3 Bucket..."

aws s3api create-bucket \
    --bucket "rfp-documents-quadrasystems" \
    --region $REGION 2>/dev/null || log_info "S3 bucket already exists"

log_success "S3 Bucket: rfp-documents-quadrasystems"

# ============================================
# STEP 3: Seed DynamoDB Data
# ============================================
log_info "Seeding supplier data..."

python setup/seed_data.py

log_success "Supplier data seeded"

# ============================================
# STEP 4: Create IAM Role
# ============================================
log_info "Creating IAM Role..."

TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}'

aws iam create-role \
    --role-name rfp-agent-lambda-role \
    --assume-role-policy-document "$TRUST_POLICY" \
    --region $REGION 2>/dev/null || log_info "Role already exists"

log_success "IAM Role: rfp-agent-lambda-role"

# Attach policies
log_info "Attaching IAM policies..."

aws iam put-role-policy \
    --role-name rfp-agent-lambda-role \
    --policy-name DynamoDBAccess \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:UpdateItem"],
        "Resource": "arn:aws:dynamodb:'$REGION':'$ACCOUNT_ID':table/rfp-*"
      }]
    }' --region $REGION

aws iam put-role-policy \
    --role-name rfp-agent-lambda-role \
    --policy-name S3Access \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
        "Resource": ["arn:aws:s3:::rfp-documents-quadrasystems", "arn:aws:s3:::rfp-documents-quadrasystems/*"]
      }]
    }' --region $REGION

aws iam put-role-policy \
    --role-name rfp-agent-lambda-role \
    --policy-name BedrockAccess \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Action": ["bedrock:InvokeModel", "bedrock-agent:InvokeAgent"],
        "Resource": "*"
      }]
    }' --region $REGION

aws iam put-role-policy \
    --role-name rfp-agent-lambda-role \
    --policy-name CloudWatchLogs \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        "Resource": "arn:aws:logs:'$REGION':'$ACCOUNT_ID':*"
      }]
    }' --region $REGION

log_success "IAM policies attached"

# ============================================
# STEP 5: Create ECR Repository
# ============================================
log_info "Creating ECR Repository..."

aws ecr create-repository \
    --repository-name $PROJECT_NAME \
    --region $REGION 2>/dev/null || log_info "ECR repository already exists"

log_success "ECR Repository: $PROJECT_NAME"

# ============================================
# STEP 6: Build and Push Docker Image
# ============================================
log_info "Building Docker image..."

docker build -t $PROJECT_NAME:latest -f lambda/Dockerfile .
docker tag $PROJECT_NAME:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME:latest

log_success "Docker image built"

log_info "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

log_info "Pushing image to ECR..."
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME:latest

log_success "Docker image pushed to ECR"

# ============================================
# STEP 7: Create Lambda Function
# ============================================
log_info "Creating Lambda Function..."

aws lambda create-function \
    --function-name rfp-agent-handler \
    --role arn:aws:iam::$ACCOUNT_ID:role/rfp-agent-lambda-role \
    --code ImageUri=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME:latest \
    --package-type Image \
    --handler lambda.rfp_agent_handler.handler \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables="{REGION=$REGION,BEDROCK_MODEL_ID=amazon.nova-pro-v1:0}" \
    --region $REGION 2>/dev/null || log_info "Lambda function already exists"

log_success "Lambda Function: rfp-agent-handler"

# ============================================
# SUMMARY
# ============================================
echo ""
echo "============================================"
echo "✅ Deployment Complete!"
echo "============================================"
echo ""
echo "Next Steps:"
echo "1. Create API Gateway (manual)"
echo "2. Set up AgentCore Memory and Runtime"
echo "3. Update config.py with AgentCore IDs"
echo "4. Run tests: python -m pytest tests/ -v"
echo ""
echo "Test locally:"
echo "  python -m agent.agent_runner"
echo ""
