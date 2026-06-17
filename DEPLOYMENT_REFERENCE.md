# Deployment Reference - All Resources

**Last Updated**: June 17, 2026
**Status**: ✅ Container deployment ready
**All Files Created**: 13

---

## Quick Navigation

### For Immediate Deployment
- **Deploy Orchestrator Only**: `bash deploy-container.sh` (5 min)
- **Deploy All 7 Lambdas**: `bash deploy-all-containers.sh` (20 min)
- **Quick Reference**: `DEPLOYMENT_QUICK_START.md`

### For Understanding the Issue
- **Root Cause**: `RPDS_PY_TROUBLESHOOTING.md` (why ZIP fails)
- **Complete Guide**: `CONTAINER_DEPLOYMENT.md` (technical details)
- **Summary**: `CONTAINER_DEPLOYMENT_SUMMARY.md` (what was done)

### For Debugging
- **Docker issues**: See "Troubleshooting" in `CONTAINER_DEPLOYMENT.md`
- **AWS issues**: See "Common Issues" in `DEPLOYMENT_QUICK_START.md`
- **rpds-py issues**: See `RPDS_PY_TROUBLESHOOTING.md`

---

## File Inventory

### Deployment Scripts
```
deploy-container.sh              ✅ Ready
deploy-all-containers.sh         ✅ Ready
```

### Dockerfiles
```
Dockerfile                        ✅ (Orchestrator)
RFP-main/lambda/supplier_lookup_lambda.Dockerfile      ✅
RFP-main/lambda/rfp_generator_lambda.Dockerfile        ✅
RFP-main/lambda/email_dispatch_lambda.Dockerfile       ✅
RFP-main/lambda/proposal_fetch_lambda.Dockerfile       ✅
RFP-main/lambda/scoring_lambda.Dockerfile              ✅
RFP-main/lambda/recommendation_lambda.Dockerfile       ✅
```

### Configuration
```
RFP-main/requirements.txt         ✅ Minimal (3 dependencies)
RFP-main/config.py                ✅ Existing
```

### Documentation
```
CONTAINER_DEPLOYMENT.md               ✅ Technical guide (complete)
CONTAINER_DEPLOYMENT_SUMMARY.md       ✅ Setup summary (complete)
DEPLOYMENT_QUICK_START.md             ✅ Quick reference (complete)
RPDS_PY_TROUBLESHOOTING.md           ✅ rpds-py guide (complete)
DEPLOYMENT_REFERENCE.md               ✅ This file
```

---

## The Problem (Summary)

**ZIP deployment fails with**: `"No module named 'rpds.rpds'"`

**Why**: 
- strands-agents requires Pydantic v2
- Pydantic v2 requires rpds-py (compiled C binary for your OS)
- Lambda runs on Linux (different OS)
- Binary mismatch = crash

**Solution**: Container deployment (compiles rpds-py on Linux inside container)

---

## The Solution (Summary)

**Created**:
1. 7 Dockerfiles (orchestrator + 6 tools)
2. 2 deployment scripts (orchestrator only or all 7)
3. Updated requirements.txt (minimal dependencies)
4. Comprehensive documentation

**How it works**:
- Docker builds image using AWS Lambda Linux base image
- pip installs dependencies (rpds-py compiles for Linux)
- Container image contains Linux binary
- Lambda runs container (binary matches OS)
- ✅ No rpds-py error

---

## Step-by-Step: Deploy in 5 Minutes

### Prerequisites
```bash
# 1. Verify Docker installed
docker --version

# 2. Verify AWS CLI configured
aws sts get-caller-identity

# 3. Verify region
aws configure get region
# Should output: us-east-1
```

### Deploy
```bash
# Navigate to project root
cd "c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT"

# Run deployment script
bash deploy-container.sh

# Monitor output...
```

### Test
```bash
# Script runs test automatically, but you can test manually:
aws lambda invoke \
    --function-name rfp-agentcore-orchestrator \
    --payload '{"body": "{\"message\": \"test\"}"}' \
    --region us-east-1 \
    response.json

cat response.json
# ✅ Success: No "errorMessage"
# ❌ Failure: Contains "errorMessage"
```

### Push to GitHub
```bash
git add .
git commit -m "Deploy orchestrator as container image"
git push
```

---

## Key Files Explained

### Dockerfile (Orchestrator)
```dockerfile
FROM public.ecr.aws/lambda/python:3.12        # AWS Lambda base image
WORKDIR ${LAMBDA_TASK_ROOT}
COPY RFP-main/agentcore_orchestrator.py ...    # Application files
COPY RFP-main/requirements.txt .
RUN pip install -r requirements.txt ...        # Installs dependencies in Linux
CMD [ "agentcore_orchestrator.handler" ]       # Lambda entry point
```

**Key**: `pip install` runs inside Linux environment → rpds-py compiles for Linux

### deploy-container.sh (Orchestrator)
```bash
1. Create ECR repo
2. Authenticate Docker
3. Build image
4. Push to ECR
5. Update Lambda
6. Test
```

**Time**: ~3-5 minutes
**Output**: ✅ Lambda deployed and tested

### deploy-all-containers.sh (All 7)
```bash
Loop for each of 7 Lambdas:
  1. Build image (using specific Dockerfile)
  2. Push to ECR
  3. Create/update Lambda
  4. Test
```

**Time**: ~15-20 minutes
**Output**: All 7 Lambdas deployed and tested

### RPDS_PY_TROUBLESHOOTING.md
Explains:
- Why rpds-py fails in ZIP deployment
- Why container deployment fixes it
- Platform-specific binary details
- Verification steps
- Fallback troubleshooting

---

## Common Workflows

### Workflow 1: Test Orchestrator Only (5 min)
```bash
bash deploy-container.sh
# Creates 1 Lambda, tests, reports results
```

### Workflow 2: Deploy All 7 Lambdas (20 min)
```bash
bash deploy-all-containers.sh
# Creates 7 Lambdas, tests each, reports results
```

### Workflow 3: Manual Single Lambda
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
docker build -t rfp-agent:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker tag rfp-agent:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest
aws lambda update-function-code --function-name rfp-agentcore-orchestrator --image-uri $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest --region us-east-1
```

### Workflow 4: Check Deployment Status
```bash
# Check ECR repository
aws ecr describe-repositories --repository-names rfp-agent --region us-east-1

# Check images in ECR
aws ecr describe-images --repository-name rfp-agent --region us-east-1

# Check Lambda function
aws lambda get-function --function-name rfp-agentcore-orchestrator --region us-east-1

# Check logs
aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region us-east-1
```

### Workflow 5: Debug Deployment Failure
```bash
# 1. Check Docker build
docker build -t test:latest .
# Should complete without errors

# 2. Check image in Docker
docker images | grep rfp-agent

# 3. Check ECR push
aws ecr describe-images --repository-name rfp-agent --region us-east-1

# 4. Check Lambda package type
aws lambda get-function --function-name rfp-agentcore-orchestrator --region us-east-1 --query 'Configuration.PackageType'
# Should be "Image" not "Zip"

# 5. Check Lambda logs
aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region us-east-1
```

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────┐
│                 RFP Management System                    │
│                 (Container Deployment)                   │
└─────────────────────────────────────────────────────────┘

Components Created:
  ✅ 1 Main Dockerfile (orchestrator)
  ✅ 6 Tool Dockerfiles (in RFP-main/lambda/)
  ✅ 1 Deploy Script (orchestrator)
  ✅ 1 Deploy Script (all 7)
  ✅ Updated requirements.txt

Deployment Targets (AWS):
  ✅ ECR Repository: rfp-agent
  ✅ 7 Lambda Functions: rfp-agentcore-orchestrator + 6 tools

Problem Solved:
  ✅ rpds-py binary mismatch (ZIP deployment)
  ✅ Platform-specific compiled extensions
  ✅ Import module errors

Verification:
  ✅ No "rpds.rpds" errors expected
  ✅ Test payload responds with "status": "success"
  ✅ CloudWatch logs show normal execution
```

---

## Decision Matrix: Which Deployment to Use?

| Need | Solution | Time | Complexity |
|------|----------|------|-----------|
| Quick test | `bash deploy-container.sh` | 5 min | Low |
| Production | `bash deploy-all-containers.sh` | 20 min | Medium |
| Manual control | Follow manual steps in CONTAINER_DEPLOYMENT.md | 10 min | High |
| Debugging | See RPDS_PY_TROUBLESHOOTING.md + check logs | Varies | High |

---

## Validation Checklist

Before deploying, verify:
- [ ] Docker installed: `docker --version`
- [ ] AWS CLI configured: `aws sts get-caller-identity`
- [ ] Region is us-east-1: `aws configure get region`
- [ ] IAM role exists: `aws iam get-role --role-name rfp-agent-lambda-role`
- [ ] requirements.txt is minimal: `cat RFP-main/requirements.txt`
- [ ] Dockerfile exists: `ls Dockerfile`
- [ ] Tool Dockerfiles exist: `ls RFP-main/lambda/*.Dockerfile | wc -l` → should be 6

After deploying, verify:
- [ ] ECR repo created: `aws ecr describe-repositories --repository-names rfp-agent`
- [ ] Images pushed: `aws ecr describe-images --repository-name rfp-agent`
- [ ] Lambda is container type: `aws lambda get-function --function-name rfp-agentcore-orchestrator --query 'Configuration.PackageType'` → "Image"
- [ ] Lambda test passes: No "errorMessage" in response
- [ ] No rpds-py errors: Check CloudWatch logs

---

## Next Steps After Deployment

1. **Commit to Git**
   ```bash
   git add .
   git commit -m "Deploy all 7 Lambdas as container images"
   git push
   ```

2. **Test End-to-End**
   ```bash
   aws lambda invoke \
       --function-name rfp-agentcore-orchestrator \
       --payload '{"RequestID":"RFP-001","Budget":50000}' \
       --region us-east-1 \
       response.json
   ```

3. **Monitor in CloudWatch**
   ```bash
   aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region us-east-1
   ```

4. **Check Tool Lambda Integration**
   - Verify orchestrator can invoke each tool Lambda
   - Check tool Lambda logs for errors
   - Test full RFP processing workflow

5. **Document Deployment** (optional)
   - Add deployment date to project wiki
   - Record Container Image URIs
   - Document any customizations

---

## Support & Debugging

### Get Help
1. **Container deployment issues**: `CONTAINER_DEPLOYMENT.md` → Troubleshooting
2. **rpds-py issues**: `RPDS_PY_TROUBLESHOOTING.md`
3. **Quick issues**: `DEPLOYMENT_QUICK_START.md` → Common Issues
4. **AWS CLI issues**: Run `aws configure` and `aws sts get-caller-identity`

### Check Status
```bash
# Comprehensive health check
echo "=== Docker ==="
docker --version
echo "=== AWS CLI ==="
aws sts get-caller-identity
echo "=== Region ==="
aws configure get region
echo "=== ECR ==="
aws ecr describe-repositories --repository-names rfp-agent --region us-east-1
echo "=== Lambda ==="
aws lambda get-function --function-name rfp-agentcore-orchestrator --region us-east-1 --query 'Configuration.{State:State,PackageType:PackageType,LastModified:LastModified}'
echo "=== Logs (last 10 lines) ==="
aws logs tail /aws/lambda/rfp-agentcore-orchestrator --max-items 10 --region us-east-1
```

---

## Key Constraints

❌ **DO NOT**:
- Use ZIP deployment (will fail)
- Manually add rpds-py to requirements
- Pin Pydantic versions
- Remove rpds from dependencies
- Use non-Lambda base images

✅ **DO**:
- Use container deployment
- Keep requirements.txt minimal
- Use public.ecr.aws/lambda/python:3.12
- Test after deployment
- Push code to GitHub

---

## Summary

**Created**: Complete container deployment solution for 7 Lambda functions

**Includes**:
- 7 Dockerfiles
- 2 deployment scripts
- Updated dependencies
- Comprehensive documentation

**Status**: Ready to deploy

**Next Action**: Run `bash deploy-container.sh` or `bash deploy-all-containers.sh`

---

**Contact**: See deployment scripts for AWS CLI commands or CloudWatch logs for runtime issues

