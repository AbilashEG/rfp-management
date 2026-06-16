# CloudShell Deployment Guide - RFP Management System

This guide walks through deploying the RFP Management Lambda system to AWS using CloudShell.

## Prerequisites

✓ AWS Account with access to CloudShell
✓ Existing CloudFormation stack (`rfp-production-stack`)
✓ S3 bucket created (`rfp-documents-quadrasystems-v2`)
✓ DynamoDB tables created (handled by CloudFormation)
✓ 7 Lambda functions created (handled by CloudFormation)

## Quick Deployment (5 minutes)

### Step 1: Download Repository

Open **AWS CloudShell** and run:

```bash
# Download repo from GitHub
wget https://github.com/AbilashEG/rfp-management/archive/main.zip
unzip main.zip
cd rfp-management-main

# Verify structure
ls -la RFP-main/
ls -la *.sh
```

### Step 2: Run Deployment Script

```bash
# Make script executable
chmod +x cloudshell-deploy.sh

# Run deployment
bash cloudshell-deploy.sh
```

This script will:
1. ✓ Install Python dependencies
2. ✓ Create 7 Lambda ZIPs with correct structure
3. ✓ Upload all ZIPs to S3
4. ✓ Deploy code to all 7 Lambda functions
5. ✓ Test the orchestrator Lambda
6. ✓ Display API endpoint

### Step 3: Verify Deployment

```bash
# Check Lambda function status
aws lambda get-function-configuration \
  --function-name rfp-agent-orchestrator-v2 \
  --region us-east-1 --query 'LastModified'

# View CloudWatch logs
aws logs tail /aws/lambda/rfp-agent-orchestrator-v2 --follow --region us-east-1
```

---

## Manual Deployment (if needed)

### Build ZIPs Locally (Optional)

If you want to build ZIPs locally first:

```bash
# On your local machine
pip install -r RFP-main/requirements.txt -t package/
python3 build-zips-local.py

# Then upload to CloudShell:
# scp *.zip ec2-user@cloudshell:/path/to/
```

### Manual CloudShell Steps

```bash
# Step 1: Install dependencies
pip install -r RFP-main/requirements.txt -t package/

# Step 2: Build orchestrator ZIP
mkdir -p temp-orchestrator
cp RFP-main/agentcore_orchestrator.py temp-orchestrator/
cp RFP-main/agentcore_memory.py temp-orchestrator/
cp RFP-main/config.py temp-orchestrator/
cp -r package/. temp-orchestrator/
cd temp-orchestrator && zip -r ../orchestrator.zip . && cd ..
rm -rf temp-orchestrator

# Step 3: Upload to S3
aws s3 cp orchestrator.zip \
  s3://rfp-documents-quadrasystems-v2/lambda-zips/rfp-agent-orchestrator-v2/orchestrator.zip \
  --region us-east-1

# Step 4: Deploy to Lambda
aws lambda update-function-code \
  --function-name rfp-agent-orchestrator-v2 \
  --s3-bucket rfp-documents-quadrasystems-v2 \
  --s3-key lambda-zips/rfp-agent-orchestrator-v2/orchestrator.zip \
  --region us-east-1

# Step 5: Repeat for each tool Lambda...
# (See script for exact commands)
```

---

## Lambda Deployment Order

Deploy in this order:

1. **orchestrator** → `rfp-agent-orchestrator-v2`
2. **supplier_lookup_tool** → `supplier_lookup_tool-v2`
3. **rfp_generator_tool** → `rfp_generator_tool-v2`
4. **email_dispatch_tool** → `email_dispatch_tool-v2`
5. **proposal_fetch_tool** → `proposal_fetch_tool-v2`
6. **scoring_tool** → `scoring_tool-v2`
7. **recommendation_tool** → `recommendation_tool-v2`

---

## Testing After Deployment

### Test Orchestrator Lambda

```bash
# Invoke with test payload
aws lambda invoke \
  --function-name rfp-agent-orchestrator-v2 \
  --payload '{"RequestID":"RFP-TEST-001","Budget":50000}' \
  --cli-binary-format raw-in-base64-out \
  --region us-east-1 \
  response.json

# View response
cat response.json | python3 -m json.tool
```

### Expected Response

```json
{
  "statusCode": 200,
  "body": {
    "status": "processing",
    "rfp_id": "RFP-TEST-001",
    "message": "RFP request received and processing started"
  }
}
```

### Check CloudWatch Logs

```bash
# View orchestrator logs (last 50 lines)
aws logs tail /aws/lambda/rfp-agent-orchestrator-v2 \
  --log-stream-names '$LATEST' \
  --max-items 50 \
  --region us-east-1
```

---

## Troubleshooting

### Issue: "No module named 'boto3'"

**Solution:**
- Verify dependencies are included in ZIP
- Check: `unzip -l orchestrator.zip | grep boto3`
- Should show files in `site-packages/boto3/`

### Issue: "Unable to import module 'agentcore_orchestrator'"

**Solution:**
- Verify ZIP structure: `unzip -l orchestrator.zip | head -20`
- Should show source files at root level, not nested

### Issue: Lambda timeout

**Solution:**
- Increase timeout: 
  ```bash
  aws lambda update-function-configuration \
    --function-name rfp-agent-orchestrator-v2 \
    --timeout 300 \
    --region us-east-1
  ```

### View All Lambda Logs

```bash
# List all Lambda log groups
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/rfp \
  --region us-east-1

# Tail specific Lambda
aws logs tail /aws/lambda/supplier_lookup_tool-v2 --follow
```

---

## Configuration

### Environment Variables

All Lambda functions use environment variables set in CloudFormation:

- `REGION` = us-east-1
- `MODEL` = amazon.nova-pro-v1:0

View/update:

```bash
aws lambda get-function-configuration \
  --function-name rfp-agent-orchestrator-v2 \
  --region us-east-1 \
  --query 'Environment'
```

### S3 Bucket Configuration

```bash
# Verify bucket exists
aws s3api head-bucket \
  --bucket rfp-documents-quadrasystems-v2 \
  --region us-east-1

# Check bucket contents
aws s3 ls s3://rfp-documents-quadrasystems-v2/lambda-zips/ --recursive
```

---

## Cleanup (if needed)

### Remove Old Lambda ZIPs from S3

```bash
aws s3 rm s3://rfp-documents-quadrasystems-v2/lambda-zips/ --recursive
```

### Delete Stack (WARNING: Removes all infrastructure)

```bash
aws cloudformation delete-stack \
  --stack-name rfp-production-stack \
  --region us-east-1
```

---

## API Testing

### API Endpoint

```
POST https://n1q81b8i4k.execute-api.us-east-1.amazonaws.com/prod/process-rfp
```

### Test Request

```bash
curl -X POST \
  https://n1q81b8i4k.execute-api.us-east-1.amazonaws.com/prod/process-rfp \
  -H "Content-Type: application/json" \
  -d '{
    "RequestID": "RFP-001",
    "Budget": 100000,
    "Timeline": "Q3-2025",
    "Requirements": "Cloud infrastructure setup"
  }'
```

---

## Summary

✅ All 7 Lambda functions deployed
✅ Correct ZIP structure verified
✅ S3 uploads complete
✅ Ready for production use

For questions, refer to `README.md` or check CloudWatch logs.
