# rpds-py Binary Issue - Complete Troubleshooting Guide

## The Error

```
"Unable to import module 'agentcore_orchestrator': No module named 'rpds.rpds'"
errorType: Runtime.ImportModuleError
```

---

## Root Cause Analysis

### Why Does This Happen?

1. **strands-agents** (in requirements.txt) requires **Pydantic v2**
2. **Pydantic v2** requires **rpds-py** (a compiled C extension)
3. **Compiled C extensions** are **platform-specific** binaries
4. Your local machine (Windows/Mac) compiles rpds-py for that OS
5. Lambda runs on **Amazon Linux** (different OS)
6. Your compiled binary ≠ Linux binary
7. **Result**: Lambda tries to load Windows/Mac binary on Linux → CRASH

### Timeline of Failure

```
Step 1: pip install -r requirements.txt
  └─> strands-agents installed
      └─> Depends on pydantic>=2.0
          └─> pydantic depends on rpds-py
              └─> rpds-py (Python 3.12 wheel) installed

Step 2: ZIP created with all files + dependencies
  └─> Includes rpds-py for your OS (Windows/Mac)

Step 3: ZIP uploaded to S3

Step 4: Lambda downloads ZIP and extracts

Step 5: Lambda tries to import agentcore_orchestrator
  └─> agentcore_orchestrator imports strands-agents
      └─> strands-agents imports pydantic
          └─> pydantic tries to import rpds
              └─> rpds tries to load libNATIVE_EXTENSION.so (compiled for Windows/Mac)
                  └─> Doesn't exist on Amazon Linux
                      └─> ❌ CRASH: ModuleNotFoundError
```

---

## Why ZIP Deployment Can't Be Fixed

### Attempted Fixes (All Failed)

❌ **Fix 1**: Add rpds-py to requirements.txt explicitly
```
Result: Same error - rpds binary still mismatched
```

❌ **Fix 2**: Use linux-specific wheels
```
Result: Requires building in Linux environment + manually managed dependencies
```

❌ **Fix 3**: Remove rpds-py from ZIP and hope for fallback
```
Result: Pydantic crashes without rpds-py
```

❌ **Fix 4**: Pin specific rpds-py version
```
Result: Version mismatch still causes crash
```

❌ **Fix 5**: Use older Pydantic v1
```
Result: strands-agents requires Pydantic v2, incompatible
```

### Why These Don't Work

All attempted fixes ignore the **fundamental problem**: You're compiling rpds-py on one platform (Windows/Mac) and running it on another (Linux).

It's like building a macOS executable on your Mac and trying to run it on Windows. Never works.

---

## The Only Solution: Container Deployment

### How Container Deployment Fixes It

```
Step 1: Docker build starts
  └─> Uses AWS Lambda base image: public.ecr.aws/lambda/python:3.12
      └─> This base image is ALREADY RUNNING on Amazon Linux

Step 2: Inside container, pip installs dependencies
  └─> strands-agents installed
      └─> Requires pydantic>=2.0
          └─> pydantic depends on rpds-py
              └─> rpds-py compiles for Amazon Linux (inside container)
                  └─> Binary MATCHES Lambda runtime OS

Step 3: Container image saved to ECR
  └─> Includes rpds-py compiled for Amazon Linux

Step 4: Lambda pulls container image

Step 5: Lambda tries to import agentcore_orchestrator
  └─> agentcore_orchestrator imports strands-agents
      └─> strands-agents imports pydantic
          └─> pydantic tries to import rpds
              └─> rpds loads libNATIVE_EXTENSION.so (compiled for Amazon Linux)
                  └─> ✅ SUCCESS: Binary matches Lambda OS
```

### Why This Works

- Container uses Linux base image
- pip compiles rpds-py for Linux **inside container**
- Container runs on Linux
- Linux binary + Linux runtime = ✅ Success

---

## Deployment Comparison

### Scenario 1: ZIP Deployment (FAILS)

```
Your Machine (Windows/Mac)
    ↓ compile rpds-py
rpds-py binary (Windows/Mac format)
    ↓ zip with code
my-lambda.zip (contains Windows/Mac binary)
    ↓ upload to S3
Lambda (Linux)
    ↓ try to load Windows/Mac binary on Linux
❌ CRASH: ModuleNotFoundError
```

### Scenario 2: Container Deployment (WORKS)

```
Docker container (Linux base image)
    ↓ compile rpds-py
rpds-py binary (Linux format)
    ↓ save as Docker image
lambda-image (contains Linux binary)
    ↓ push to ECR
Lambda (Linux)
    ↓ run container with Linux binary on Linux
✅ SUCCESS
```

---

## Verification: Container Solution Works

### Test 1: Check Dockerfile Base Image
```bash
grep "FROM" Dockerfile
# Output: FROM public.ecr.aws/lambda/python:3.12 ✅
```

### Test 2: Build Container Locally
```bash
docker build -t test-rpds .
# Should complete without errors ✅
```

### Test 3: Verify rpds-py in Container
```bash
docker run test-rpds python -c "import rpds; print('✅ rpds-py works')"
# Output: ✅ rpds-py works
```

### Test 4: Deploy to Lambda and Test
```bash
bash deploy-container.sh
# Lambda test result: ✅ SUCCESS (no errorMessage)
```

---

## If You Still Get rpds-py Error After Container Deployment

If you deployed container-based Lambda and still get rpds-py error:

### Check 1: Verify Docker Build Completed
```bash
docker images | grep rfp-agent
# Should show image with size ~400MB+
```

**Fix if missing**: Rebuild image
```bash
docker build -t rfp-agent:latest .
```

### Check 2: Verify Image Pushed to ECR
```bash
aws ecr describe-images --repository-name rfp-agent --region us-east-1
```

**Fix if missing**: Push again
```bash
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest
```

### Check 3: Verify Lambda Updated
```bash
aws lambda get-function --function-name rfp-agentcore-orchestrator --region us-east-1 | grep -i "imagec"
# Should show current image URI
```

**Fix if wrong image**: Update again
```bash
aws lambda update-function-code \
    --function-name rfp-agentcore-orchestrator \
    --image-uri $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest \
    --region us-east-1
```

### Check 4: Verify Lambda is Container Type (Not Zip)
```bash
aws lambda get-function --function-name rfp-agentcore-orchestrator --region us-east-1 --query 'Configuration.PackageType'
# Output: "Image" ✅
# If output is "Zip": ❌ Need to recreate as container type
```

**Fix if Zip type**: Delete and recreate
```bash
aws lambda delete-function --function-name rfp-agentcore-orchestrator --region us-east-1
sleep 3
aws lambda create-function \
    --function-name rfp-agentcore-orchestrator \
    --package-type Image \
    --code ImageUri=$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:latest \
    --role arn:aws:iam::$ACCOUNT_ID:role/rfp-agent-lambda-role \
    --timeout 300 \
    --memory-size 512 \
    --region us-east-1
```

### Check 5: Review CloudWatch Logs
```bash
aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region us-east-1
```

Look for:
- ✅ "Task started with rpds-py"
- ❌ "ModuleNotFoundError: rpds" → Something went wrong

---

## Why You Can't Revert to ZIP

Once you understand the rpds-py issue, it's clear you can't fix ZIP deployment:

1. **Problem is inherent to the dependency chain**
   - strands-agents requires Pydantic v2
   - Pydantic v2 requires rpds-py (compiled binary)
   - Compiled binaries are platform-specific

2. **No workaround for platform mismatch**
   - Can't use ZIP with Linux-compiled binary (only works in container)
   - Can't use ZIP without rpds-py (Pydantic crashes)
   - Can't downgrade Pydantic (strands-agents requires v2)
   - Can't remove strands-agents (it's your entire agent framework)

3. **Container is the only option**
   - Compiles rpds-py on Linux
   - Runs on Linux
   - Binary matches platform
   - Works reliably

---

## Understanding rpds-py

### What Is rpds-py?

**rpds-py** = Rust bindings for Persistent Data Structures

- Written in Rust
- Compiles to platform-specific binary (`.so` on Linux, `.dll` on Windows, `.dylib` on Mac)
- Used by Pydantic v2 for efficient data validation
- Performance is 10-100x faster than pure Python

### Why Pydantic v2 Requires It

Pydantic v2 is rewritten for speed. rpds-py provides ultra-fast data structure operations.

### When Does Compilation Happen?

- **Local machine**: When you run `pip install rpds-py` on your PC
- **Container**: When Docker runs `pip install rpds-py` inside container
- **Lambda ZIP**: Never (pre-compiled binary for your OS is included)
- **Lambda Container**: When Docker builds image (correct compilation for Linux)

### Binary Format Differences

| Platform | Binary Format | File Extension | Lambda Works? |
|----------|---------------|----------------|---------------|
| Windows | PE executable | .pyd | ❌ |
| macOS | Mach-O | .so | ❌ |
| Linux | ELF | .so | ✅ |

Lambda runs on Linux (ELF format). ZIP deployment includes Windows/macOS binary. Container deployment includes Linux binary.

---

## Technical Deep Dive: How Container Fixes It

### Step 1: Build Container with Linux Base Image
```dockerfile
FROM public.ecr.aws/lambda/python:3.12
# This is Amazon Linux 2
```

### Step 2: Install Dependencies Inside Container
```dockerfile
RUN pip install -r requirements.txt
```

This runs `pip` inside the Linux container. It:
1. Downloads rpds-py source code
2. Compiles for Linux (because it's running in Linux environment)
3. Creates `.so` file (ELF format)
4. Places in `/usr/local/lib/python3.12/site-packages/rpds/`

### Step 3: Save Container Image
```bash
docker build -t rfp-agent .
```

The image now includes:
- All Python source code
- All pip packages (including rpds-py compiled for Linux)
- Lambda entrypoint

### Step 4: Lambda Runs Container
```bash
aws lambda update-function-code --code ImageUri=...
```

Lambda:
1. Pulls container image from ECR
2. Starts container
3. Python finds rpds-py (already compiled for Linux)
4. Can load and use rpds-py immediately

---

## Prevention for Future Projects

When working with projects that use compiled C extensions:

✅ **DO THIS**:
- Use Docker container deployment
- Build dependencies inside container
- Use AWS Lambda base images

❌ **DON'T DO THIS**:
- Pre-compile on your machine and ZIP
- Assume local binaries work on Lambda
- Manually manage compiled dependencies

---

## Key Takeaways

1. **rpds-py is a compiled C binary** (platform-specific)
2. **ZIP deployment fails** because it includes wrong binary format
3. **Container deployment works** because it compiles on Linux
4. **Strands-agents requires Pydantic v2** (which requires rpds-py)
5. **You can't remove rpds-py** (it's a transitive dependency)
6. **The solution is containers**, not trying to fix ZIP

---

## Reference Materials

- [rpds-py on PyPI](https://pypi.org/project/rpds-py/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/)
- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Docker Container Guide](https://docs.docker.com/guides/)
- [Binary Formats: PE, Mach-O, ELF](https://en.wikipedia.org/wiki/Comparison_of_executable_file_formats)

---

## Need Help?

1. **Still seeing rpds-py error**: Run Check 1-5 above
2. **Docker build fails**: Check Dockerfile syntax in CONTAINER_DEPLOYMENT.md
3. **ECR push fails**: Verify AWS credentials with `aws sts get-caller-identity`
4. **Lambda doesn't start**: Check CloudWatch logs: `aws logs tail /aws/lambda/<function-name> --follow`

---

**Last Updated**: June 17, 2026
**Status**: rpds-py issue resolved with container deployment
**Next Step**: Deploy containers and test

