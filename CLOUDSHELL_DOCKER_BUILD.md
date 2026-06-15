# Docker Image Build via AWS CloudShell
## Step-by-Step Instructions

Your ZIP file is ready: `supplier-rfp-agent.zip`

---

## **STEP 1: Open AWS CloudShell**

1. Go to: https://console.aws.amazon.com/
2. Make sure you're in region: **us-east-1** (top right)
3. Click terminal icon (🖥️) at the top right → **CloudShell**
4. Wait for shell to load (1-2 minutes first time)

---

## **STEP 2: Upload ZIP File to CloudShell**

In CloudShell, click the **Actions** menu (top left of terminal) → **Upload file**

Upload: `c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent.zip`

---

## **STEP 3: Extract ZIP in CloudShell**

Copy-paste this command into CloudShell:

```bash
unzip supplier-rfp-agent.zip
```

Then verify it extracted:

```bash
ls -la supplier-rfp-agent/
```

Expected output shows folders: `agent/`, `tools/`, `lambda/`, `setup/`, `tests/`, `infra/`, etc.

---

## **STEP 4: Build Docker Image**

```bash
cd supplier-rfp-agent
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .
```

**This will take 2-5 minutes.** Wait for it to complete.

Expected output ends with:
```
Successfully built <image-id>
Successfully tagged supplier-rfp-agent:latest
```

---

## **STEP 5: Verify Image**

```bash
docker images | grep supplier-rfp-agent
```

Expected output:
```
supplier-rfp-agent   latest   abc123def456   2 minutes ago   500MB
```

---

## **STEP 6: Login to ECR**

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 689050397154.dkr.ecr.us-east-1.amazonaws.com
```

Expected output: `Login Succeeded`

---

## **STEP 7: Tag Image for ECR**

```bash
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

---

## **STEP 8: Push to ECR**

```bash
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

**This will take 2-10 minutes depending on image size.** Shows progress of each layer.

Expected output ends with:
```
latest: digest: sha256:abc123...xyz789 size: 5000
```

---

## **STEP 9: Verify Image in ECR**

```bash
aws ecr describe-images --repository-name supplier-rfp-agent --region us-east-1
```

Expected output shows your image with:
- `repositoryName`: supplier-rfp-agent
- `imageDigest`: sha256:...
- `imageTags`: ["latest"]
- `imagePushedAt`: today's date

---

## **Complete CloudShell Commands (Copy-Paste All at Once)**

```bash
#!/bin/bash

echo "================================"
echo "Docker Build & Push via CloudShell"
echo "================================"

# Variables
ACCOUNT_ID="689050397154"
REGION="us-east-1"
REPO_NAME="supplier-rfp-agent"

# Extract ZIP
echo "Extracting ZIP file..."
unzip -q supplier-rfp-agent.zip
cd supplier-rfp-agent

# Build image
echo "Building Docker image..."
docker build -t $REPO_NAME:latest -f lambda/Dockerfile . || exit 1

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com || exit 1

# Tag image
echo "Tagging image for ECR..."
docker tag $REPO_NAME:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

# Push to ECR
echo "Pushing image to ECR (this may take a few minutes)..."
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest || exit 1

# Verify
echo "Verifying image in ECR..."
aws ecr describe-images --repository-name $REPO_NAME --region $REGION

echo ""
echo "================================"
echo "✅ SUCCESS!"
echo "================================"
echo "Image URI:"
echo "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest"
echo ""
echo "Next: Create Lambda function with this image URI"
```

---

## **Copy-Paste Commands One by One (If Script Fails)**

1. Extract:
```bash
unzip supplier-rfp-agent.zip
```

2. Navigate:
```bash
cd supplier-rfp-agent
```

3. Build:
```bash
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .
```

4. Login:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 689050397154.dkr.ecr.us-east-1.amazonaws.com
```

5. Tag:
```bash
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

6. Push:
```bash
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

7. Verify:
```bash
aws ecr describe-images --repository-name supplier-rfp-agent --region us-east-1
```

---

## **After Docker Image is Pushed**

You'll see output like:
```json
{
    "imageDetails": [
        {
            "repositoryName": "supplier-rfp-agent",
            "imageTags": [
                "latest"
            ],
            "imageDigest": "sha256:abc123...",
            "imageSizeInBytes": 500000000,
            "imagePushedAt": "2026-06-12T12:35:00+00:00"
        }
    ]
}
```

**Save the Image URI:** 
```
689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

---

## **Next: Create Lambda Function**

Once image is in ECR, run this in CloudShell:

```bash
aws lambda create-function \
  --function-name rfp-agent-handler \
  --role arn:aws:iam::689050397154:role/rfp-agent-lambda-role \
  --code ImageUri=689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest \
  --package-type Image \
  --handler lambda.rfp_agent_handler.handler \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables="{REGION=us-east-1,BEDROCK_MODEL_ID=amazon.nova-pro-v1:0}" \
  --region us-east-1
```

**Expected output:** Lambda function created successfully

---

## **Verify Lambda Created**

```bash
aws lambda get-function --function-name rfp-agent-handler --region us-east-1
```

Should show:
```json
{
    "Configuration": {
        "FunctionName": "rfp-agent-handler",
        "FunctionArn": "arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler",
        "Handler": "lambda.rfp_agent_handler.handler",
        "CodeSha256": "...",
        "State": "Active",
        "Timeout": 300,
        "MemorySize": 512
    }
}
```

---

## **CloudShell Tips**

- **Commands are case-sensitive** (use lowercase for aws commands)
- **Copy-paste works:** Right-click or use Ctrl+Shift+V
- **Long operations:** Don't close the terminal, wait for completion
- **Session timeout:** CloudShell times out after 1 hour of inactivity
- **Files persist:** Your uploaded files stay in CloudShell for the session

---

## **Troubleshooting in CloudShell**

### "docker: command not found"
**Solution:** CloudShell has docker pre-installed. Try refreshing:
```bash
docker --version
```

### "Unable to locate Dockerfile"
**Solution:** Make sure you're in the `supplier-rfp-agent` directory:
```bash
pwd
ls lambda/Dockerfile
```

### "ECR login failed"
**Solution:** Check AWS credentials and region:
```bash
aws sts get-caller-identity
aws ec2 describe-regions --query 'Regions[0]'
```

### "Docker push times out"
**Solution:** Try again, sometimes network is slow in CloudShell:
```bash
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

### "Image already exists in ECR"
**Solution:** That's fine, it will just overwrite the old one. The push will still complete successfully.

---

## **Summary**

| Step | Command | Time |
|------|---------|------|
| 1 | Open CloudShell | 2 min |
| 2 | Upload ZIP | 1 min |
| 3 | Extract | 1 min |
| 4 | Build image | 3-5 min |
| 5 | Login to ECR | <1 min |
| 6 | Tag image | <1 min |
| 7 | Push to ECR | 5-10 min |
| 8 | Create Lambda | <1 min |
| **Total** | | **15-25 min** |

---

**You're all set to build and deploy via CloudShell!** 🚀

