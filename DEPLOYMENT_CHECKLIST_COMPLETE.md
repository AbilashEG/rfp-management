# Complete Deployment Checklist

**Status**: Ready for AWS deployment
**Date**: June 17, 2026
**Target**: Deploy all 7 Lambdas as container images

---

## Pre-Deployment Verification

### Environment Setup
- [ ] Docker installed and running
  ```bash
  docker --version
  # Expected: Docker version 20.x or higher
  ```

- [ ] AWS CLI installed and configured
  ```bash
  aws sts get-caller-identity
  # Expected: Account ID, User ARN, Account details
  ```

- [ ] Region set to us-east-1
  ```bash
  aws configure get region
  # Expected: us-east-1
  ```

- [ ] IAM role exists
  ```bash
  aws iam get-role --role-name rfp-agent-lambda-role
  # Expected: Role ARN and trust relationship shown
  ```

### File Verification
- [ ] Main Dockerfile exists
  ```bash
  ls -la ./Dockerfile
  # Expected: -rw- ... Dockerfile
  ```

- [ ] 6 Tool Dockerfiles exist
  ```bash
  ls -la ./RFP-main/lambda/*.Dockerfile
  # Expected: 6 files
  ```

- [ ] requirements.txt is minimal
  ```bash
  cat ./RFP-main/requirements.txt
  # Expected: 3 lines (strands-agents, strands-agents-tools, boto3)
  ```

- [ ] Deploy scripts are executable
  ```bash
  ls -la ./deploy-container.sh ./deploy-all-containers.sh
  # Expected: Both files present and readable
  ```

### Code Verification
- [ ] agentcore_orchestrator.py exists
  ```bash
  ls -la ./RFP-main/agentcore_orchestrator.py
  ```

- [ ] agentcore_memory.py exists
  ```bash
  ls -la ./RFP-main/agentcore_memory.py
  ```

- [ ] config.py exists
  ```bash
  ls -la ./RFP-main/config.py
  ```

- [ ] All 6 tool Lambda files exist
  ```bash
  ls -la ./RFP-main/lambda/*_lambda.py
  # Expected: 6 files
  ```

---

## Deployment Option 1: Quick Test (Orchestrator Only)

### Step 1: Run Deployment Script
```bash
cd "c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT"
bash deploy-container.sh
```

**Expected Output**:
```
================================================================================
RFP Management System - Container Deployment
================================================================================
AWS Account ID: 689050397154
Region: us-east-1
ECR Repository: rfp-agent

STEP 1: Creating ECR repository...
✓ ECR repository ready

STEP 2: Authenticating with ECR...
✓ Docker authenticated with ECR

STEP 3: Building Docker image...
✓ Docker image built successfully

STEP 4: Pushing image to ECR...
✓ Image pushed to ECR: ...

STEP 5: Updating Lambda function...
✓ Container-based Lambda created/updated

STEP 6: Testing Lambda function...
✓ Test successful - no errors in response

================================================================================
✅ DEPLOYMENT COMPLETE!
================================================================================
```

### Step 2: Verify Test Result
- [ ] Script completed without errors
- [ ] Test response shows `"status": "success"` (or similar)
- [ ] No `"errorMessage"` in response
- [ ] No `"rpds.rpds"` error

**Checklist**: Did test pass?
- [ ] ✅ YES → Proceed to "Deployment Option 2" or "Commit to GitHub"
- [ ] ❌ NO → Go to "Troubleshooting" section

---

## Deployment Option 2: Complete Deployment (All 7 Lambdas)

### Step 1: Run All-Lambdas Deployment Script
```bash
cd "c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT"
bash deploy-all-containers.sh
```

**Expected Output** (for each of 7 Lambdas):
```
================================================================================
Processing: rfp-agentcore-orchestrator
================================================================================

Step 3a: Building Docker image...
✓ Docker image built

Step 3b: Tagging for ECR...
✓ Image tagged: ...

Step 3c: Pushing to ECR...
✓ Image pushed to ECR

Step 3d: Updating Lambda function...
✓ Container-based Lambda created

Step 3e: Testing Lambda function...
✓ Lambda test successful

(Repeat for 6 more Lambdas)

================================================================================
✅ DEPLOYMENT COMPLETE!
================================================================================

Summary of Deployed Lambdas:
  1. rfp-agentcore-orchestrator (Orchestrator)
  2. rfp-supplier-lookup (Tool)
  3. rfp-rfp-generator (Tool)
  4. rfp-email-dispatch (Tool)
  5. rfp-proposal-fetch (Tool)
  6. rfp-scoring (Tool)
  7. rfp-recommendation (Tool)
```

### Step 2: Verify All Tests Passed
- [ ] All 7 Lambdas deployed successfully
- [ ] No errors reported for any Lambda
- [ ] All test responses show success
- [ ] No `"rpds.rpds"` errors

**Checklist**: All tests passed?
- [ ] ✅ YES → Proceed to "Post-Deployment Verification"
- [ ] ❌ NO → Go to "Troubleshooting" section

---

## Post-Deployment Verification

### ECR Repository Check
```bash
aws ecr describe-repositories --repository-names rfp-agent --region us-east-1
```
- [ ] Repository exists: `rfp-agent`
- [ ] Region: `us-east-1`

### Lambda Functions Check
For each of 7 functions, verify:

#### Orchestrator
```bash
aws lambda get-function --function-name rfp-agentcore-orchestrator --region us-east-1
```
- [ ] Function exists
- [ ] PackageType: `Image` (not `Zip`)
- [ ] State: `Active`

#### Supplier Lookup
```bash
aws lambda get-function --function-name rfp-supplier-lookup --region us-east-1
```
- [ ] Function exists
- [ ] PackageType: `Image`
- [ ] State: `Active`

#### RFP Generator
```bash
aws lambda get-function --function-name rfp-rfp-generator --region us-east-1
```
- [ ] Function exists
- [ ] PackageType: `Image`
- [ ] State: `Active`

#### Email Dispatch
```bash
aws lambda get-function --function-name rfp-email-dispatch --region us-east-1
```
- [ ] Function exists
- [ ] PackageType: `Image`
- [ ] State: `Active`

#### Proposal Fetch
```bash
aws lambda get-function --function-name rfp-proposal-fetch --region us-east-1
```
- [ ] Function exists
- [ ] PackageType: `Image`
- [ ] State: `Active`

#### Scoring
```bash
aws lambda get-function --function-name rfp-scoring --region us-east-1
```
- [ ] Function exists
- [ ] PackageType: `Image`
- [ ] State: `Active`

#### Recommendation
```bash
aws lambda get-function --function-name rfp-recommendation --region us-east-1
```
- [ ] Function exists
- [ ] PackageType: `Image`
- [ ] State: `Active`

### Docker Images Check
```bash
aws ecr describe-images --repository-name rfp-agent --region us-east-1
```
- [ ] At least 7 images pushed to ECR
- [ ] Each image has unique tag
- [ ] Image size reasonable (~400-500 MB each)

### CloudWatch Logs Check
```bash
aws logs tail /aws/lambda/rfp-agentcore-orchestrator --max-items 20 --region us-east-1
```
- [ ] Logs exist
- [ ] No ERROR entries
- [ ] No "rpds" related errors
- [ ] Task execution visible

---

## Testing Lambda Functions

### Test 1: Basic Orchestrator Invoke
```bash
aws lambda invoke \
    --function-name rfp-agentcore-orchestrator \
    --payload '{"body": "{\"message\": \"test\"}"}' \
    --region us-east-1 \
    response.json

cat response.json
```

**Checklist**:
- [ ] Invoke succeeded
- [ ] Response file created
- [ ] Response is valid JSON
- [ ] No `"errorMessage"` in response
- [ ] No `"rpds"` errors

### Test 2: Orchestrator with RFP Data
```bash
aws lambda invoke \
    --function-name rfp-agentcore-orchestrator \
    --payload '{"RequestID":"RFP-TEST-001","Budget":50000,"Category":"Software"}' \
    --region us-east-1 \
    response.json

cat response.json
```

**Checklist**:
- [ ] Invoke succeeded
- [ ] Response shows RFP processing started
- [ ] No errors in response

### Test 3: Tool Lambda (Supplier Lookup)
```bash
aws lambda invoke \
    --function-name rfp-supplier-lookup \
    --payload '{"category":"Software","budget":50000}' \
    --region us-east-1 \
    response.json

cat response.json
```

**Checklist**:
- [ ] Invoke succeeded
- [ ] Response indicates tool execution
- [ ] No "rpds.rpds" error

### Test 4: Tool Lambda (Scoring)
```bash
aws lambda invoke \
    --function-name rfp-scoring \
    --payload '{"proposal":{"name":"Test Proposal","score":0}}' \
    --region us-east-1 \
    response.json

cat response.json
```

**Checklist**:
- [ ] Invoke succeeded
- [ ] Tool executed successfully
- [ ] No import errors

---

## Commit to GitHub

### Stage Changes
```bash
cd "c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT"
git status
```

**Expected**: Files to commit:
- [ ] Dockerfile
- [ ] deploy-container.sh
- [ ] deploy-all-containers.sh
- [ ] RFP-main/lambda/*.Dockerfile (6 files)
- [ ] RFP-main/requirements.txt (updated)
- [ ] Documentation files (*.md)

### Commit
```bash
git add .
git commit -m "Deploy all 7 Lambdas as container images (fixes rpds-py binary issue)"
```

**Checklist**:
- [ ] Commit message is clear
- [ ] All changed files staged
- [ ] Commit successful

### Push
```bash
git push origin main
```

**Checklist**:
- [ ] Push successful
- [ ] No conflicts
- [ ] GitHub updated

---

## Troubleshooting

### If Docker Build Fails

**Error**: `"docker: command not found"`
```bash
# Solution: Install Docker
# Windows: Download from https://www.docker.com/products/docker-desktop
# Verify after install:
docker --version
```

**Error**: `"Cannot connect to Docker daemon"`
```bash
# Solution: Start Docker
# Windows: Start Docker Desktop from Start Menu
# Linux: sudo systemctl start docker
```

**Error**: `"failed to solve with frontend dockerfile.v0: failed to read dockerfile"`
```bash
# Solution: Check Dockerfile path
ls -la ./Dockerfile
# Ensure file exists in current directory
```

### If AWS CLI Fails

**Error**: `"Unable to locate credentials"`
```bash
# Solution: Configure AWS credentials
aws configure
# Enter: Access Key, Secret Key, Region (us-east-1), Output format (json)
# Verify:
aws sts get-caller-identity
```

**Error**: `"Access Denied"`
```bash
# Solution: Check IAM permissions
# Ensure user/role has:
# - ecr:* (ECR actions)
# - lambda:* (Lambda actions)
# - iam:GetRole (to read Lambda execution role)
```

**Error**: `"The specified bucket does not exist"`
```bash
# This is OK - means ECR repo doesn't exist yet
# Solution: Script will create it automatically
```

### If ECR Push Fails

**Error**: `"denied: Your authorization token has expired"`
```bash
# Solution: Re-authenticate
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

**Error**: `"name unknown: The repository with name 'rfp-agent' does not exist in the registry"`
```bash
# Solution: Create repository first
aws ecr create-repository --repository-name rfp-agent --region us-east-1
```

### If Lambda Test Fails

**Error**: `"rpds.rpds"`
```bash
# Solution: Check that Lambda is Container type (not Zip)
aws lambda get-function --function-name rfp-agentcore-orchestrator --region us-east-1 --query 'Configuration.PackageType'
# If output is "Zip": Delete and recreate as container type
# See RPDS_PY_TROUBLESHOOTING.md for details
```

**Error**: `"Unable to import module"`
```bash
# Solution: Check CloudWatch logs
aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region us-east-1
# Look for detailed error message
```

**Error**: `"Timeout waiting for response"`
```bash
# Solution: Increase Lambda timeout
aws lambda update-function-configuration \
    --function-name rfp-agentcore-orchestrator \
    --timeout 600 \
    --region us-east-1
```

---

## Success Criteria

✅ **Deployment is successful if**:

1. All 7 Lambda functions deployed as container type
2. All ECR images pushed without errors
3. All Lambda tests passed (no "rpds.rpds" error)
4. All Lambdas have PackageType = "Image"
5. All Lambdas have State = "Active"
6. Code committed to GitHub
7. No "Unable to import module" errors

❌ **Deployment failed if**:

1. Any Lambda remains as "Zip" type
2. Any Lambda test shows "rpds.rpds" error
3. Any Lambda has State = "Failed"
4. Docker build failed
5. ECR push failed
6. Code not committed

---

## Final Verification Checklist

Before considering deployment complete:

- [ ] All 7 Lambdas deployed
- [ ] All Lambdas are container type
- [ ] All Lambdas tested successfully
- [ ] No rpds-py errors
- [ ] ECR repository contains all images
- [ ] CloudWatch logs show normal execution
- [ ] Code committed to GitHub
- [ ] Documentation updated (if needed)
- [ ] No further errors expected

---

## Next Steps After Successful Deployment

1. **Monitor in Production**
   ```bash
   # Watch logs during initial usage
   aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region us-east-1
   ```

2. **Test Full RFP Workflow**
   - Create sample RFP via API
   - Monitor orchestrator processing
   - Verify all tool Lambdas execute
   - Check final output

3. **Set Up Alerts** (Optional)
   ```bash
   # Create CloudWatch alarm for errors
   # Create SNS topic for notifications
   # Set threshold for Lambda errors
   ```

4. **Document Deployment**
   - Record deployment date
   - Save container image URIs
   - Document any customizations
   - Update runbooks

---

## Support Resources

| Issue | Resource |
|-------|----------|
| Docker basics | CONTAINER_DEPLOYMENT.md → Architecture |
| rpds-py details | RPDS_PY_TROUBLESHOOTING.md |
| AWS CLI commands | DEPLOYMENT_QUICK_START.md → Manual Deployment |
| Debugging | CONTAINER_DEPLOYMENT.md → Troubleshooting |

---

## Sign-Off

When all checkboxes are completed:

```
✅ Pre-deployment verification: PASS
✅ Deployment script execution: PASS
✅ Post-deployment verification: PASS
✅ Testing: PASS
✅ GitHub commit: PASS
✅ No critical issues: PASS

STATUS: READY FOR PRODUCTION
DATE: [Today's date]
DEPLOYED BY: [Your name]
```

---

**Deployment completed on**: _________________ (date)
**Deployed by**: _________________ (name)
**Notes**: _____________________________________________________________________________

---

**End of Checklist**

