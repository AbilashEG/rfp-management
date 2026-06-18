# Build ARM64 Image using CodeBuild in CloudShell

## Problem Solved
CloudShell can't build ARM64 images natively (x86_64 environment, emulation fails with disk space errors). **CodeBuild with ARM64_CONTAINER can build them natively**.

## Solution
Run CodeBuild **from CloudShell** to build the ARM64 image. CodeBuild has native ARM64 compute, so no emulation needed.

---

## Steps to Execute in CloudShell

### 1. Open AWS CloudShell
- Go to https://console.aws.amazon.com/cloudshell
- Make sure you're in region: **us-east-1**

### 2. Clone the repository (if not already there)
```bash
cd ~
git clone https://github.com/AbilashEEG/rfp-management.git
cd rfp-management
```

### 3. Run the CodeBuild setup script
```bash
bash CODEBUILD_ARM64_SETUP.sh
```

This script will:
- ✓ Create IAM role for CodeBuild
- ✓ Attach required policies (ECR, CloudWatch)
- ✓ Create CodeBuild project with ARM64_CONTAINER
- ✓ Start the build
- ✓ Monitor progress (should take 5-10 minutes)
- ✓ Update AgentCore Runtime with the new ARM64 image URI

### 4. Wait for build to complete
The script will display progress every 10 seconds. You should see:
```
Status: IN_PROGRESS | Phase: BUILD
Status: IN_PROGRESS | Phase: POST_BUILD
Status: SUCCEEDED
```

### 5. Once build succeeds
You'll see:
```
✓ Build SUCCEEDED!
  ARM64 Image built successfully!
  URI: 689050397154.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:orchestrator-agentcore-arm64
  Digest: sha256:xxxxxxx...
✓ AgentCore Runtime updated!
```

### 6. Test the agent
Once the script completes, test the full workflow:

```bash
# Test the agent with a sample RFP request
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn "arn:aws:bedrock-agentcore:us-east-1:689050397154:runtime/rfpsupplieragent-ODy0E42s5l" \
  --payload '{
    "message": "We need 500 brake sensors by 2026-09-30. Specs: ABS wheel speed sensor, IP67, CAN bus output. Category: sensors."
  }' \
  --region us-east-1
```

---

## Why This Works

| Approach | Environment | Result |
|----------|-----------|--------|
| CloudShell native buildx | x86_64 | ❌ Emulation fails, disk space error |
| Tag x86_64 as ARM64 | N/A | ❌ Bedrock checks actual manifest architecture |
| **CodeBuild ARM64_CONTAINER** | **ARM64 native** | ✅ Native build, no emulation |

---

## If Build Fails

Check the logs in CloudShell output. Common issues:

1. **Role permissions issue**
   - Ensure AWS credentials have IAM, CodeBuild, ECR permissions

2. **GitHub repo not found**
   - Update `$GITHUB_REPO` in the script to your actual GitHub URL
   - Ensure repository is public or CodeBuild has credentials

3. **ECR repository not found**
   - Repository `rfp-agent` must exist
   - Create it: `aws ecr create-repository --repository-name rfp-agent --region us-east-1`

---

## Troubleshooting Commands

If the build doesn't complete or you need to check status:

```bash
# Check CodeBuild project
aws codebuild batch-get-projects --names rfp-agent-arm64-build --region us-east-1

# Check build status
aws codebuild batch-get-builds \
  --ids rfp-agent-arm64-build:xxxxxxxx \
  --region us-east-1

# View build logs
aws logs tail /aws/codebuild/rfp-agent-arm64-build --follow --region us-east-1

# List images in ECR
aws ecr describe-images --repository-name rfp-agent --region us-east-1

# Check AgentCore Runtime
aws bedrock-agentcore get-resource \
  --resource-arn "arn:aws:bedrock-agentcore:us-east-1:689050397154:runtime/rfpsupplieragent-ODy0E42s5l" \
  --region us-east-1
```

---

## Next Steps After Build

1. Test agent invocation (see Step 6 above)
2. Monitor agent logs:
   ```bash
   aws logs tail /aws/bedrock-agentcore/rfpsupplieragent-ODy0E42s5l --follow --region us-east-1
   ```
3. Check RFP workflow results in DynamoDB:
   ```bash
   aws dynamodb scan --table-name rfp-requests --region us-east-1
   ```

---

## Summary

- **CloudShell Problem**: Can't build ARM64 natively (x86_64 only, emulation breaks)
- **Solution**: Use CodeBuild with ARM64_CONTAINER (native ARM64 compute)
- **Command**: Run `CODEBUILD_ARM64_SETUP.sh` in CloudShell
- **Result**: ARM64 image built → AgentCore Runtime updated → Ready to test
