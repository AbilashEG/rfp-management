# Quick Start - Container Deployment

## TL;DR

**Problem**: ZIP deployment fails with `"No module named 'rpds.rpds'"` because compiled binaries don't match Lambda's Linux environment.

**Solution**: Use Docker container images (rpds-py will compile correctly inside container).

---

## Prerequisites Check

```bash
# 1. Docker running?
docker --version

# 2. AWS CLI configured?
aws sts get-caller-identity

# 3. Region is us-east-1?
aws configure get region

# 4. IAM role exists?
aws iam get-role --role-name rfp-agent-lambda-role
```

If any of these fail, fix them before proceeding.

---

## Deploy Orchestrator Only (5 minutes)

```bash
bash deploy-container.sh
```

This will:
- Create ECR repo
- Build Docker image
- Push to ECR
- Deploy Lambda as container type
- Test with sample payload

If test passes → Move to "Deploy All 7 Lambdas"
If test fails → Run: `aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region us-east-1`

---

## Deploy All 7 Lambdas (20 minutes)

```bash
bash deploy-all-containers.sh
```

This will deploy all 7 Lambdas (orchestrator + 6 tools) as container types.

---

## Manual Single Lambda Deployment

```bash
# 1. Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 2. Create ECR repo (one time only)
aws ecr create-repository --repository-name rfp-agent --region us-east-1

# 3. Authenticate Docker
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# 4. Build image
docker build -t rfp-agent:latest .

# 5. Tag for ECR
docker tag rfp-agent:latest \
    $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest

# 6. Push to ECR
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest

# 7. Update Lambda (if exists) or create (if new)
aws lambda update-function-code \
    --function-name rfp-agentcore-orchestrator \
    --image-uri $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest \
    --region us-east-1

# 8. Test
aws lambda invoke \
    --function-name rfp-agentcore-orchestrator \
    --payload '{"body": "{\"message\": \"test\"}"}' \
    --region us-east-1 \
    response.json
cat response.json
```

---

## Test Results

**✅ Success** (No rpds error):
```json
{
  "status": "success",
  "message": "RFP processing started",
  ...
}
```

**❌ Failure** (rpds error - should NOT happen with container deployment):
```json
{
  "errorMessage": "Unable to import module 'agentcore_orchestrator': No module named 'rpds.rpds'",
  "errorType": "Runtime.ImportModuleError"
}
```

---

## Common Issues

| Issue | Fix |
|-------|-----|
| "Access Denied" pushing to ECR | Run: `aws ecr get-login-password...` step again |
| "No such file or directory" | Verify paths: `ls Dockerfile`, `ls RFP-main/requirements.txt` |
| Lambda test fails | Check logs: `aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow` |
| "Unable to import module" still happens | Old Lambda still running as ZIP. Delete and recreate as Image type. |

---

## What Gets Created

1. **ECR Repository**: `rfp-agent` (holds all Docker images)
2. **Lambda Functions** (container-based):
   - rfp-agentcore-orchestrator
   - rfp-supplier-lookup
   - rfp-rfp-generator
   - rfp-email-dispatch
   - rfp-proposal-fetch
   - rfp-scoring
   - rfp-recommendation

---

## Next Steps

1. **Test end-to-end**:
   ```bash
   aws lambda invoke \
       --function-name rfp-agentcore-orchestrator \
       --payload '{"RequestID":"RFP-001","Budget":50000}' \
       --region us-east-1 \
       response.json
   cat response.json
   ```

2. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Deploy all 7 Lambdas as container images"
   git push
   ```

3. **Monitor in CloudWatch**:
   ```bash
   aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region us-east-1
   ```

---

## Why This Works

- **Docker base image**: `public.ecr.aws/lambda/python:3.12` (AWS Lambda-optimized)
- **Compilation environment**: rpds-py builds inside Linux container (matches Lambda runtime)
- **No binary mismatch**: Container image runs on exact same OS as Lambda
- **Pydantic v2**: Still required by strands-agents, compiles correctly
- **pip resolution**: Automatic handling of all transitive dependencies

---

## Important Notes

❌ **DO NOT** try to fix ZIP deployment by:
- Adding rpds-py manually
- Pinning versions
- Installing locally and zipping
- Using pre-compiled wheels

✅ **ALWAYS** use container deployment for this project.

---

## Rollback (If Needed)

If you need to revert:

1. Delete Lambda: `aws lambda delete-function --function-name rfp-agentcore-orchestrator --region us-east-1`
2. Delete ECR images: `aws ecr batch-delete-image --repository-name rfp-agent --image-ids imageTag=latest`
3. Restore old ZIP Lambda from backup

---

## Questions?

Check `CONTAINER_DEPLOYMENT.md` for detailed troubleshooting and architecture info.

