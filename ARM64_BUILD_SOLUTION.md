# ARM64 Build Solution for AgentCore Runtime

## The Problem You Faced

You tried to build an ARM64 Docker image in **CloudShell** using `docker buildx --platform=linux/arm64`, and it failed with:

```
ERROR: failed to solve: failed to prepare ... as sv58d57jwzhlvz9rrst3zwaxu: no space left on device
```

### Why This Happened

1. **CloudShell runs on x86_64 Linux** - it's an Amazon Linux environment on x86 architecture
2. **ARM64 is a different architecture** - when you try to build `--platform=linux/arm64`, Docker attempts emulation:
   - It runs an ARM64 emulator (QEMU) on the x86 CPU
   - This is slow and resource-intensive
   - During `pip install` of large packages (like `numpy`, `boto3`, etc.), the emulator needs to compile native ARM64 binaries
   - This fills the disk quickly (only ~10GB available in CloudShell)
   - After a few minutes: **`no space left on device`**

3. **You tried to fake it with tags** - you took an x86_64 image and re-tagged it as ARM64, but:
   - AWS Bedrock checks the actual **Docker manifest architecture**
   - It doesn't trust tags - it inspects the image's real architecture
   - Error: `Architecture incompatible for uri...Supported platforms: [arm64]`

---

## The Solution: AWS CodeBuild

**CodeBuild is AWS's managed build service that can build Docker images natively for multiple architectures.**

### Key Insight

When you specify `environment.type = "ARM_CONTAINER"` in CodeBuild:
- CodeBuild runs the build on **actual ARM64 hardware** (not emulation)
- Docker builds **natively** without emulation overhead
- No disk space issues
- No performance penalties

### How It Works

```
You (CloudShell)
    ↓
    Run: bash CODEBUILD_ARM64_SETUP.sh
    ↓
    (Creates IAM role + policies)
    ↓
    (Creates CodeBuild project with ARM64_CONTAINER)
    ↓
    (Starts build on CodeBuild ARM64 runner)
    ↓
CodeBuild ARM64 Runner (real hardware)
    ↓
    Clones your GitHub repo
    ↓
    Reads buildspec.yml
    ↓
    Runs: docker build -t rfp-agent:orchestrator-agentcore-arm64 .
    ↓
    (Build happens on native ARM64 - NO EMULATION)
    ↓
    Pushes image to ECR
    ↓
    Returns: ARM64 image digest
    ↓
You (CloudShell)
    ↓
    Updates AgentCore Runtime with new image URI
    ↓
    ✓ Done!
```

---

## Architecture Comparison

### ❌ CloudShell Native Build (Failed)

```
CloudShell (x86_64 Linux)
    ↓
docker buildx --platform=linux/arm64
    ↓
QEMU Emulation (x86 → ARM64)
    ↓
    pip install large_package
    ↓
    Compile native ARM64 binary
    ↓
    [DISK FULL - 10GB limit]
    ↓
❌ Error: no space left on device
```

### ✅ CodeBuild ARM64 Build (Solution)

```
CodeBuild ARM64 Runner (real ARM64 hardware)
    ↓
docker build (native ARM64)
    ↓
    pip install large_package
    ↓
    Compile native ARM64 binary
    ↓
    [Plenty of disk - 100GB+ available]
    ↓
✓ Success: ARM64 image created
```

---

## Files Created

### 1. `CODEBUILD_ARM64_SETUP.sh`
**Main script** - Automates the entire build process:
- Creates IAM role for CodeBuild
- Attaches ECR + CloudWatch policies
- Creates CodeBuild project (ARM64_CONTAINER type)
- Starts the build
- Monitors progress
- Updates AgentCore Runtime with new image

**Usage:**
```bash
bash CODEBUILD_ARM64_SETUP.sh
```

### 2. `buildspec.yml`
**Build specification** - CodeBuild reads this to know what to do:
- Pre-build: Login to ECR
- Build: `docker build` the ARM64 image
- Post-build: Push to ECR, verify architecture

**Why it works:**
- Runs in CodeBuild's ARM64 environment
- No emulation, native build
- Automatically pushes to ECR

### 3. `CODEBUILD_CLOUDSHELL_INSTRUCTIONS.md`
**Step-by-step guide** - Explains what to do in CloudShell

### 4. `QUICK_CODEBUILD_COMMAND.sh`
**One-liner** - For quick execution:
```bash
cd ~ && git clone ... && bash CODEBUILD_ARM64_SETUP.sh
```

---

## What Happens When You Run It

### Phase 1: Setup (2-3 minutes)
```
[STEP 1] Creating IAM role for CodeBuild...
✓ Role already exists: codebuild-rfp-agent-arm64-role

[STEP 2] Attaching policies to role...
✓ ECR policy already attached
✓ CloudWatch policy already attached

[STEP 3] Creating CodeBuild project...
✓ CodeBuild project already exists: rfp-agent-arm64-build
✓ Updated project configuration
```

### Phase 2: Build Start (10 seconds)
```
[STEP 4] Starting CodeBuild...
✓ Build started: rfp-agent-arm64-build:xxxxxxxx

[STEP 5] Monitoring build progress...
  (This may take 5-10 minutes)
```

### Phase 3: Build Monitoring (5-10 minutes)
```
  [1/60] Status: IN_PROGRESS | Phase: QUEUED
  [2/60] Status: IN_PROGRESS | Phase: PROVISIONING
  [3/60] Status: IN_PROGRESS | Phase: DOWNLOAD_SOURCE
  [4/60] Status: IN_PROGRESS | Phase: INSTALL
  [5/60] Status: IN_PROGRESS | Phase: PRE_BUILD
  [10/60] Status: IN_PROGRESS | Phase: BUILD
      [+] Building with native buildkit ...
      sha256:xxxxxxx
      => [1/6] FROM public.ecr.aws/lambda/python:3.12
      => [2/6] COPY RFP-main/agentcore_orchestrator.py
      => [3/6] COPY RFP-main/requirements.txt
      => [4/6] RUN pip install -r requirements.txt
      => [5/6] RUN chmod +x ./agentcore_orchestrator.py
      => [6/6] CMD [ "agentcore_orchestrator.handler" ]
  [15/60] Status: IN_PROGRESS | Phase: POST_BUILD
      Pushing docker image...
      ✓ Image pushed to ECR
```

### Phase 4: Success (5 seconds)
```
[STEP 6] Checking build result...
✓ Build SUCCEEDED!

  ARM64 Image built successfully!
  URI: 689050397154.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:orchestrator-agentcore-arm64
  Digest: sha256:f1520eb8f4512623bc4a1441b4562b7427b9333a834b89704485a44527cc4e39

[STEP 7] Updating AgentCore Runtime with ARM64 image...
✓ AgentCore Runtime updated!

Deploy complete. You can now test the agent.
```

---

## Why This Solution Is Better

| Aspect | CloudShell | CodeBuild |
|--------|-----------|----------|
| **Architecture Support** | x86_64 only | x86_64, ARM64, ARM64v2, etc. |
| **Build Method** | Emulation (slow) | **Native** (fast) |
| **Disk Space** | 10GB | 100GB+ |
| **Build Time** | 20-30 min (if it works) | 5-10 min |
| **Cost** | Free | ~$0.01-0.05 per build |
| **Reliability** | Fragile | Reliable |

---

## Next Steps After Build

Once the build completes and AgentCore Runtime is updated:

### 1. Test Agent Invocation
```bash
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn "arn:aws:bedrock-agentcore:us-east-1:689050397154:runtime/rfpsupplieragent-ODy0E42s5l" \
  --payload '{"message": "We need 500 brake sensors by Sept 30, 2026"}' \
  --region us-east-1
```

### 2. Monitor Agent Logs
```bash
aws logs tail /aws/bedrock-agentcore/rfpsupplieragent-ODy0E42s5l --follow --region us-east-1
```

### 3. Check RFP Workflow Results
```bash
aws dynamodb scan --table-name rfp-requests --region us-east-1
aws dynamodb scan --table-name rfp-proposals --region us-east-1
```

---

## Technical Details

### CodeBuild Project Configuration

```json
{
  "environment": {
    "type": "ARM_CONTAINER",
    "image": "aws/codebuild/amazonlinux2-arm64-standard:3.0",
    "computeType": "BUILD_GENERAL1_LARGE",
    "privilegedMode": true
  }
}
```

**Key settings:**
- `type: ARM_CONTAINER` - Use ARM64 compute (not x86)
- `image: amazonlinux2-arm64-standard:3.0` - Official ARM64 builder image
- `computeType: BUILD_GENERAL1_LARGE` - Sufficient compute for Docker builds
- `privilegedMode: true` - Required for Docker daemon

### IAM Permissions Required

```json
{
  "Effect": "Allow",
  "Action": [
    "ecr:GetAuthorizationToken",
    "ecr:PutImage",
    "ecr:InitiateLayerUpload",
    "ecr:UploadLayerPart",
    "ecr:CompleteLayerUpload"
  ],
  "Resource": "arn:aws:ecr:us-east-1:689050397154:repository/rfp-agent"
}
```

The setup script creates these automatically.

---

## Troubleshooting

### Build fails with "exec format error"
- **Cause**: Still running on x86 (not actual ARM64)
- **Solution**: Check CodeBuild project environment type - must be `ARM_CONTAINER`

### Build fails with disk space error
- **Cause**: Compute type too small
- **Solution**: Use `BUILD_GENERAL1_LARGE` (at least) in CodeBuild project

### Image not recognized as ARM64 by Bedrock
- **Cause**: x86_64 image mislabeled as ARM64
- **Solution**: Use native ARM64 build (this script does it correctly)

### CodeBuild project not found
- **Cause**: Project name mismatch or wrong region
- **Solution**: Check `--region us-east-1` in all commands

---

## Conclusion

**The solution:** Use CodeBuild's native ARM64 infrastructure instead of trying to emulate ARM64 in CloudShell's x86 environment.

**Result:** Clean, fast, reliable ARM64 Docker image that AgentCore Runtime accepts.

**Time:** ~10 minutes from start to deployed AgentCore agent.
