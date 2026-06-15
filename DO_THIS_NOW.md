# DO THIS NOW - Lambda Setup (15-25 minutes)

---

## **Your Current Status**

✅ Complete
- S3 bucket created
- 4 DynamoDB tables created  
- IAM role created with all permissions
- ECR repository created

✅ Ready to use
- `supplier-rfp-agent.zip` file created locally

⏳ Next
- Build Docker image
- Push to ECR
- Create Lambda function

---

## **EXECUTE THESE 10 STEPS IN CLOUDSHELL**

### **Step 1: Open CloudShell (AWS Console)**

1. Go to: https://console.aws.amazon.com/
2. Make sure region = **us-east-1** (top right)
3. Click terminal icon (🖥️) at top → CloudShell
4. Wait 1-2 minutes for it to load

---

### **Step 2: Upload ZIP File**

1. In CloudShell, click **Actions** (top left) → **Upload file**
2. Select: `supplier-rfp-agent.zip`
3. Wait for upload to complete

---

### **Step 3: Extract ZIP**

Copy-paste into CloudShell:

```bash
unzip supplier-rfp-agent.zip
```

Press Enter and wait for it to complete.

---

### **Step 4: Navigate to Project**

```bash
cd supplier-rfp-agent
```

Press Enter.

---

### **Step 5: Build Docker Image** ⏱️ (3-5 minutes)

```bash
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .
```

Press Enter and **wait** for it to complete.

You'll see:
```
Step 1/N : FROM public.ecr.aws/lambda/python:3.12
...
Successfully built <hash>
Successfully tagged supplier-rfp-agent:latest
```

---

### **Step 6: Login to ECR**

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 689050397154.dkr.ecr.us-east-1.amazonaws.com
```

Press Enter. You should see: `Login Succeeded`

---

### **Step 7: Tag Image for ECR**

```bash
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

Press Enter.

---

### **Step 8: Push Image to ECR** ⏱️ (5-10 minutes)

```bash
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

Press Enter and **wait**. Shows progress of pushing layers. You'll see:
```
latest: digest: sha256:abc123... size: 5000
```

---

### **Step 9: Create Lambda Function**

Copy-paste all of this (it's one command):

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

Press Enter. Wait for response showing function created.

---

### **Step 10: Verify Lambda Created**

```bash
aws lambda get-function --function-name rfp-agent-handler --region us-east-1
```

Press Enter. You should see JSON output with:
- `"FunctionName": "rfp-agent-handler"`
- `"State": "Active"`

---

## **✅ You're Done!**

If you got to Step 10 and saw `"State": "Active"`, **congratulations!**

Your Lambda function is now:
- ✅ Built (Docker image)
- ✅ Pushed to ECR
- ✅ Deployed as Lambda function
- ✅ Ready to use

---

## **What Happens Next**

Your Lambda function can now:

1. **Receive messages** via API Gateway (when you set it up)
2. **Call the Strands Agent** with your RFP request
3. **Execute the full RFP lifecycle**:
   - Find matching suppliers
   - Generate RFP document
   - Send RFP emails
   - Fetch proposals
   - Score proposals
   - Recommend top suppliers
4. **Return results** with scoring details

---

## **Next Step: Create API Gateway** (optional)

To expose your Lambda via HTTP:

See: `AWS_DEPLOYMENT_GUIDE.md` **PHASE 7**

Or use AWS Console:
1. Go to API Gateway
2. Create REST API
3. Create resource: `/process-rfp`
4. Create POST method
5. Integrate with Lambda `rfp-agent-handler`
6. Deploy

---

## **Test Your Lambda** (after API Gateway)

```bash
curl -X POST https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod/process-rfp \
  -H "Content-Type: application/json" \
  -d '{"message": "We need 500 brake sensors. IP67, -40 to 125C. Deadline: 2026-09-30."}'
```

Expected response: Full RFP lifecycle output with recommendation.

---

## **If Something Goes Wrong**

### "docker: command not found"
→ CloudShell has Docker pre-installed. Refresh page and try again.

### "Unable to locate Dockerfile"
→ Make sure you're in `supplier-rfp-agent` directory:
```bash
pwd
ls lambda/Dockerfile
```

### "Access Denied" on ECR login
→ Check AWS account access:
```bash
aws sts get-caller-identity
```

### "Build takes too long"
→ Normal! Python image is ~300 MB. Just wait.

### "Push times out"
→ Try again, sometimes network is slow.

### "Lambda creation failed"
→ Check role exists:
```bash
aws iam get-role --role-name rfp-agent-lambda-role
```

---

## **Detailed Guides**

If you need more details:

- **Step-by-step guide:** `CLOUDSHELL_DOCKER_BUILD.md`
- **Quick reference:** `CLOUDSHELL_QUICK_STEPS.txt`
- **Lambda details:** `LAMBDA_SETUP_COMPLETE.md`

---

## **Expected Timeline**

| Step | Duration |
|------|----------|
| CloudShell setup | 2 min |
| Upload & Extract | 2 min |
| Docker build | 3-5 min |
| ECR login & tag | 1 min |
| ECR push | 5-10 min |
| Create Lambda | 1 min |
| Total | **15-25 min** |

---

## **Summary**

You have all the code, all the infrastructure. This is the final step before integration.

**10 commands. 15-25 minutes. Then Lambda is live.**

**Let's do it!** 🚀

---

**Start with:** Open AWS Console → CloudShell → Execute Step 1

When done, reply with: `aws lambda get-function --function-name rfp-agent-handler --region us-east-1`

If you see `"State": "Active"` → **SUCCESS!** ✅

