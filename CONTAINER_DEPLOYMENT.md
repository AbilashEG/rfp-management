# Container Deployment Guide - RFP Management System

## Overview

This document describes how to deploy the RFP Management System using **Docker container images** instead of ZIP files. Container deployment is **required** for this project because:

1. **Pydantic v2 Dependency**: `strands-agents` requires Pydantic v2
2. **Native Binary Dependencies**: Pydantic v2 requires `rpds-py` (a compiled C binary)
3. **Platform Mismatch**: Pre-compiled rpds-py binaries for your local machine won't work in Lambda's Linux environment
4. **Solution**: Docker containers solve this by building rpds-py inside Lambda's Linux environment

### Why ZIP Deployment Fails

```
Error: "Unable to import module 'agentcore_orchestrator': No module named 'rpds.rpds'"

Reason: rpds-py was compiled for your OS (Windows/Mac) but Lambda runs on Linux.
The binary won't work at runtime.

Solution: Use Docker to compile rpds-py inside Lambda's Linux environment.
```

---

## Prerequisites

1. **Docker** installed and running
2. **AWS CLI** configured with credentials
3. **AWS IAM Role**: `rfp-agent-lambda-role` must exist with permissions:
   - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
   - `bedrock:InvokeModel` (for Amazon Nova)
   - `dynamodb:*` (if using DynamoDB)
   - `s3:*` (if using S3)

4. **Region**: us-east-1

---

## Architecture

### 7 Lambda Functions (All Container-Based)

| Function | Role | Handler | Dockerfile |
|----------|------|---------|-----------|
| rfp-agentcore-orchestrator | Main orchestrator | agentcore_orchestrator.handler | ./Dockerfile |
| rfp-supplier-lookup | Tool | supplier_lookup_lambda.handler | ./RFP-main/lambda/supplier_lookup_lambda.Dockerfile |
| rfp-rfp-generator | Tool | rfp_generator_lambda.handler | ./RFP-main/lambda/rfp_generator_lambda.Dockerfile |
| rfp-email-dispatch | Tool | email_dispatch_lambda.handler | ./RFP-main/lambda/email_dispatch_lambda.Dockerfile |
| rfp-proposal-fetch | Tool | proposal_fetch_lambda.handler | ./RFP-main/lambda/proposal_fetch_lambda.Dockerfile |
| rfp-scoring | Tool | scoring_lambda.handler | ./RFP-main/lambda/scoring_lambda.Dockerfile |
| rfp-recommendation | Tool | recommendation_lambda.handler | ./RFP-main/lambda/recommendation_lambda.Dockerfile |

### Dockerfile Structure

Each Dockerfile follows this pattern:

```dockerfile
FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

# Copy application files
COPY RFP-main/<source> ${LAMBDA_TASK_ROOT}/
COPY RFP-main/config.py ${LAMBDA_TASK_ROOT}/
COPY RFP-main/requirements.txt .

# Install dependencies (rpds-py will compile correctly here)
RUN pip install -r requirements.txt --no-cache-dir

# Set handler
CMD [ "<handler>.handler" ]
```

Key points:
- Uses AWS Lambda Python 3.12 base image
- Installs dependencies **inside** the container (ensures correct rpds-py compilation)
- `--no-cache-dir` reduces image size

### requirements.txt

Minimal dependencies only:
```
strands-agents
strands-agents-tools
boto3
```

**DO NOT:**
- Add `rpds-py` manually (let pip resolve it)
- Pin versions (pydantic v2 management is automatic)

---

## Deployment Methods

### Option 1: Deploy Orchestrator Only (Quick Test)

```bash
bash deploy-container.sh
```

This script:
1. Creates ECR repository `rfp-agent`
2. Authenticates Docker with ECR
3. Builds orchestrator Docker image
4. Pushes to ECR
5. Updates/creates Lambda as container type
6. Tests with sample invocation

**Time**: ~3-5 minutes

### Option 2: Deploy All 7 Lambdas (Complete)

```bash
bash deploy-all-containers.sh
```

This script:
1. Creates ECR repository `rfp-agent`
2. Authenticates Docker with ECR
3. For each of 7 Lambdas:
   - Builds Docker image
   - Pushes to ECR
   - Updates/creates Lambda as container type
   - Tests with sample invocation

**Time**: ~15-20 minutes

---

## Step-by-Step Deployment (Manual)

### 1. Build Docker Image

```bash
# For orchestrator
docker build -t rfp-agent:latest .

# For a specific tool (example: supplier lookup)
docker build -f ./RFP-main/lambda/supplier_lookup_lambda.Dockerfile \
             -t rfp-agent:supplier_lookup .
```

### 2. Get AWS Account ID

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo $ACCOUNT_ID
```

### 3. Create ECR Repository

```bash
aws ecr create-repository \
    --repository-name rfp-agent \
    --region us-east-1
```

### 4. Authenticate Docker with ECR

```bash
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS \
    --password-stdin \
    $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

### 5. Tag and Push Image

```bash
# Tag for ECR
docker tag rfp-agent:latest \
    $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest

# Push to ECR
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest
```

### 6. Update Lambda Function

If Lambda already exists as ZIP type, delete and recreate:

```bash
# Delete old ZIP Lambda
aws lambda delete-function \
    --function-name rfp-agentcore-orchestrator \
    --region us-east-1

# Wait 3 seconds
sleep 3

# Create container-based Lambda
aws lambda create-function \
    --function-name rfp-agentcore-orchestrator \
    --package-type Image \
    --code ImageUri=$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest \
    --role arn:aws:iam::$ACCOUNT_ID:role/rfp-agent-lambda-role \
    --timeout 300 \
    --memory-size 512 \
    --region us-east-1
```

If Lambda already exists as container type, just update the image URI:

```bash
aws lambda update-function-code \
    --function-name rfp-agentcore-orchestrator \
    --image-uri $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest \
    --region us-east-1
```

### 7. Test Lambda

```bash
aws lambda invoke \
    --function-name rfp-agentcore-orchestrator \
    --payload '{"body": "{\"message\": \"test\"}"}' \
    --region us-east-1 \
    response.json

# View response
cat response.json
```

**Success**: Response contains `"status": "success"` (no errorMessage)
**Failure**: Response contains `"errorMessage"`

### 8. Check Logs

If test fails:

```bash
aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region us-east-1
```

---

## Troubleshooting

### Error: "Unable to import module"

**Cause**: rpds-py binary mismatch or missing dependencies

**Solution**:
1. Verify requirements.txt is correct
2. Verify Dockerfile uses `public.ecr.aws/lambda/python:3.12` base image
3. Delete Lambda, rebuild image, and redeploy
4. Check CloudWatch logs for detailed error

### Error: "Access Denied" when pushing to ECR

**Cause**: AWS credentials not configured or IAM permissions missing

**Solution**:
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Verify IAM role has ECR permissions
aws iam list-attached-user-policies --user-name <your-user>
```

### Docker Build Fails

**Cause**: Missing files or incorrect paths

**Solution**:
1. Verify Dockerfile paths are correct relative to project root
2. Verify files exist: `ls RFP-main/agentcore_orchestrator.py`
3. Verify requirements.txt exists: `ls RFP-main/requirements.txt`

### Lambda Container Timeout

**Cause**: Model invocation taking too long

**Solution**:
Increase timeout:
```bash
aws lambda update-function-configuration \
    --function-name rfp-agentcore-orchestrator \
    --timeout 600 \
    --region us-east-1
```

---

## Verification Checklist

After deployment, verify:

- [ ] ECR repository created: `aws ecr describe-repositories --repository-names rfp-agent --region us-east-1`
- [ ] Docker image pushed: `aws ecr describe-images --repository-name rfp-agent --region us-east-1`
- [ ] Lambda exists as container type: `aws lambda get-function --function-name rfp-agentcore-orchestrator --region us-east-1 | grep PackageType`
- [ ] Lambda test successful: No `errorMessage` in response
- [ ] Orchestrator can invoke tools: Check Lambda logs
- [ ] All 7 Lambdas deployed (if using deploy-all-containers.sh)

---

## Pushing to GitHub

After successful deployment:

```bash
# Stage all changes
git add .

# Commit
git commit -m "Deploy all 7 Lambdas as container images (fixes rpds-py binary issue)"

# Push
git push origin main
```

---

## FAQ

**Q: Why not just fix the ZIP deployment?**
A: rpds-py is a compiled C binary that must match Lambda's Linux environment. Pre-compiled binaries won't work. Container images are the only solution.

**Q: Do I need to run both deploy scripts?**
A: No. Choose one:
- `deploy-container.sh` for orchestrator only
- `deploy-all-containers.sh` for all 7 Lambdas

**Q: Can I use ZIP deployment after this?**
A: No. This project will always require container-based deployment because of the rpds-py dependency.

**Q: How do I rollback to ZIP deployment?**
A: You can't. Container deployment is permanent for this project.

**Q: How much does ECR cost?**
A: First 50 GB/month free. Container images for this project are ~200 MB each, so 7 images ≈ 1.4 GB total (well within free tier).

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Local Machine                        │
│                                                              │
│  1. docker build -f Dockerfile -t rfp-agent:latest .        │
│  2. docker push ... (to ECR)                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   AWS ECR Registry                           │
│                                                              │
│  rfp-agent:latest (orchestrator image)                      │
│  rfp-agent:supplier_lookup (tool image)                     │
│  rfp-agent:rfp_generator (tool image)                       │
│  ... (7 total)                                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  AWS Lambda (Container)                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ rfp-agentcore-orchestrator (Amazon Nova Pro)        │   │
│  │ ├─ Invokes: Tool Lambdas                            │   │
│  │ └─ Returns: Decision + Tool Results                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│           ┌───────────────┼───────────────┐                 │
│           ↓               ↓               ↓                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Supplier     │ │ RFP          │ │ Scoring      │        │
│  │ Lookup       │ │ Generator    │ │ Tool         │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│           │               │               │                 │
│           └───────────────┼───────────────┘                 │
│                           ↓                                  │
│                    (Same for other tools)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## References

- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Amazon ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [Docker Official Images for AWS Lambda](https://gallery.ecr.aws/lambda/python)
- [Strands Agents SDK](https://github.com/strands-ai/strands-agents)

