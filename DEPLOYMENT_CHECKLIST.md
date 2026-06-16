# RFP Management System - Deployment Checklist

## Pre-Deployment (AWS Account Setup)

### Infrastructure Prerequisites
- [ ] CloudFormation stack created: `rfp-production-stack`
  ```bash
  aws cloudformation describe-stacks --stack-name rfp-production-stack --region us-east-1
  ```
- [ ] S3 bucket exists: `rfp-documents-quadrasystems-v2`
  ```bash
  aws s3api head-bucket --bucket rfp-documents-quadrasystems-v2
  ```
- [ ] 7 Lambda functions created (by CloudFormation):
  - [ ] rfp-agent-orchestrator-v2
  - [ ] supplier_lookup_tool-v2
  - [ ] rfp_generator_tool-v2
  - [ ] email_dispatch_tool-v2
  - [ ] proposal_fetch_tool-v2
  - [ ] scoring_tool-v2
  - [ ] recommendation_tool-v2

### Local Machine Check
- [ ] Git repo cloned/updated
- [ ] Python 3.12+ installed
- [ ] AWS CLI configured
- [ ] CloudShell access available

---

## Code Verification

### Python Code (Pydantic Removal)
- [ ] `agentcore_orchestrator.py` - No pydantic imports ✅
- [ ] `agentcore_memory.py` - Dict-based implementation ✅
- [ ] `supplier_lookup_lambda.py` - No pydantic imports ✅
- [ ] `rfp_generator_lambda.py` - No pydantic imports ✅
- [ ] `email_dispatch_lambda.py` - No pydantic imports ✅
- [ ] `proposal_fetch_lambda.py` - No pydantic imports ✅
- [ ] `scoring_lambda.py` - No pydantic imports ✅
- [ ] `recommendation_lambda.py` - No pydantic imports ✅

### Dependencies
- [ ] `requirements.txt` doesn't include pydantic
- [ ] All required packages listed: boto3, botocore, strands-sdk, etc.

### Configuration
- [ ] `config.py` updated with correct AWS region
- [ ] All 7 Lambda handlers properly named
- [ ] DynamoDB table names correct

---

## GitHub Repository

- [ ] Code pushed to: https://github.com/AbilashEG/rfp-management
- [ ] Remote URL set correctly: `rfp-management.git`
- [ ] All files committed:
  - [ ] RFP-main/ directory
  - [ ] cloudshell-deploy.sh
  - [ ] build-zips-local.py
  - [ ] CLOUDSHELL_DEPLOYMENT.md
  - [ ] DEPLOYMENT_FILES.md
  - [ ] README.md
  - [ ] .gitignore
  - [ ] Dockerfile (optional)
  - [ ] .github/workflows/ (optional)

---

## CloudShell Deployment

### Step 1: Download Repository
- [ ] Opened AWS CloudShell
- [ ] Downloaded: `wget https://github.com/AbilashEG/rfp-management/archive/main.zip`
- [ ] Unzipped: `unzip main.zip`
- [ ] Changed directory: `cd rfp-management-main`
- [ ] Verified files exist: `ls -la cloudshell-deploy.sh`

### Step 2: Run Deployment Script
- [ ] Made script executable: `chmod +x cloudshell-deploy.sh`
- [ ] Ran deployment: `bash cloudshell-deploy.sh`
- [ ] **Wait for completion** - takes 5-10 minutes

### Step 3: Verify Each Phase

#### Phase 1: Dependencies
- [ ] Output shows: "✓ Dependencies installed"
- [ ] No pip errors

#### Phase 2: ZIP Building
- [ ] 7 ZIPs created:
  - [ ] orchestrator.zip
  - [ ] supplier_lookup_tool.zip
  - [ ] rfp_generator_tool.zip
  - [ ] email_dispatch_tool.zip
  - [ ] proposal_fetch_tool.zip
  - [ ] scoring_tool.zip
  - [ ] recommendation_tool.zip
- [ ] Each ZIP ~80-85 MB (dependencies included)
- [ ] All show "Structure verified: [source files] + [python dependencies]"

#### Phase 3: S3 Upload
- [ ] All 7 ZIPs uploaded to S3
- [ ] Output shows: "✓ Uploaded successfully" for each
- [ ] Verify: `aws s3 ls s3://rfp-documents-quadrasystems-v2/lambda-zips/ --recursive`

#### Phase 4: Lambda Deployment
- [ ] All 7 Lambdas deployed in order
- [ ] Each shows: "✓ Deployed successfully"
- [ ] No errors in output

#### Phase 5: Testing
- [ ] Orchestrator test invoked: `aws lambda invoke ...`
- [ ] Test completed without errors
- [ ] Response file generated: `response.json`
- [ ] Response shows success (no pydantic errors)

---

## Post-Deployment Verification

### CloudWatch Logs
- [ ] Check orchestrator logs:
  ```bash
  aws logs tail /aws/lambda/rfp-agent-orchestrator-v2 --follow --region us-east-1
  ```
- [ ] Logs show no errors
- [ ] Logs show successful initialization

### Lambda Status
- [ ] Check each Lambda function:
  ```bash
  aws lambda get-function-configuration \
    --function-name rfp-agent-orchestrator-v2 \
    --region us-east-1
  ```
- [ ] Last Modified timestamp is recent
- [ ] Code Size shows ~80+ MB
- [ ] Status: Active

### Test Invocation
- [ ] Test orchestrator with payload:
  ```bash
  aws lambda invoke \
    --function-name rfp-agent-orchestrator-v2 \
    --payload '{"RequestID":"RFP-TEST-001","Budget":50000}' \
    --cli-binary-format raw-in-base64-out \
    --region us-east-1 \
    test-response.json
  ```
- [ ] Response status: 200 (no FunctionError)
- [ ] Response body valid JSON
- [ ] No pydantic import errors

### DynamoDB Tables
- [ ] Verify tables exist:
  ```bash
  aws dynamodb list-tables --region us-east-1
  ```
- [ ] Tables created:
  - [ ] rfp-metadata-v2
  - [ ] proposals-v2
  - [ ] scores-v2
  - [ ] suppliers-v2
  - [ ] recommendations-v2

### API Gateway
- [ ] Endpoint accessible: `https://n1q81b8i4k.execute-api.us-east-1.amazonaws.com/prod/process-rfp`
- [ ] Responds to GET: `curl https://n1q81b8i4k.execute-api.us-east-1.amazonaws.com/prod/process-rfp`

---

## Troubleshooting Checks

### If Deployment Fails

**ZIP Build Error:**
- [ ] Verify dependencies: `pip install -r RFP-main/requirements.txt --dry-run`
- [ ] Check disk space: `df -h`
- [ ] Check Python version: `python3 --version` (should be 3.12+)

**S3 Upload Error:**
- [ ] Verify bucket permissions: `aws s3 ls rfp-documents-quadrasystems-v2/`
- [ ] Check AWS credentials: `aws sts get-caller-identity`
- [ ] Verify bucket exists

**Lambda Deploy Error:**
- [ ] Check Lambda exists: `aws lambda get-function --function-name rfp-agent-orchestrator-v2`
- [ ] Check IAM permissions for Lambda updates
- [ ] View deployment logs: `aws logs tail /aws/lambda/rfp-agent-orchestrator-v2`

**Runtime Errors:**
- [ ] Check for pydantic imports: `grep -r "pydantic" RFP-main/`
- [ ] Verify ZIP structure: `unzip -l orchestrator.zip | head -20`
- [ ] Should see source files + site-packages at root level

---

## Success Criteria

✅ **Deployment is successful when:**

1. All 7 Lambda functions updated with new code
2. CloudShell script runs without errors
3. Test invocation returns status 200
4. No pydantic import errors in logs
5. Orchestrator Lambda processes requests
6. Tool Lambdas respond to invocations
7. DynamoDB tables receive and store data
8. S3 bucket has uploaded documents
9. API Gateway endpoint is accessible
10. CloudWatch logs show no errors

---

## Rollback Plan

If issues occur, have these ready:

### Quick Fix (Try First)
```bash
# Re-run deployment
cd rfp-management-main
bash cloudshell-deploy.sh
```

### Manual Fix (If needed)
```bash
# Update single Lambda
aws lambda update-function-code \
  --function-name rfp-agent-orchestrator-v2 \
  --s3-bucket rfp-documents-quadrasystems-v2 \
  --s3-key lambda-zips/rfp-agent-orchestrator-v2/orchestrator.zip \
  --region us-east-1
```

### Full Rollback (Last Resort)
```bash
# Note: This deletes everything
aws cloudformation delete-stack \
  --stack-name rfp-production-stack \
  --region us-east-1

# Then redeploy from scratch
```

---

## Support Resources

- 📖 **Deployment Guide**: CLOUDSHELL_DEPLOYMENT.md
- 📋 **File Overview**: DEPLOYMENT_FILES.md
- 🔍 **Project Docs**: README.md
- ❓ **Troubleshooting**: See CLOUDSHELL_DEPLOYMENT.md

---

**Date Deployed:** ________________
**Deployed By:** ________________
**Status:** ✅ Complete / ❌ Failed

---

Print this checklist and check items as you deploy! 🚀
