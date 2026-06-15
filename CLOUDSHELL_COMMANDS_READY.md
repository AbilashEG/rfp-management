# CloudShell Commands - Copy & Paste Ready

## ⚡ Quick Deploy (All-in-One)

**Copy this entire block and paste into CloudShell:**

```bash
cd /tmp/supplier-rfp-agent && \
echo "Building Docker image..." && \
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile . && \
echo "✅ Build complete" && \
echo "" && \
echo "Tagging for ECR..." && \
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest && \
echo "✅ Tagged" && \
echo "" && \
echo "Pushing to ECR..." && \
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest && \
echo "✅ Pushed" && \
echo "" && \
echo "Updating Lambda function..." && \
aws lambda update-function-code \
  --function-name rfp-agent-handler \
  --image-uri 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest \
  --region us-east-1 && \
echo "" && \
echo "╔════════════════════════════════════════════════════════╗" && \
echo "║  ✅ DEPLOYMENT COMPLETE - Lambda updated with new image ║" && \
echo "╚════════════════════════════════════════════════════════╝"
```

---

## 📋 Step-by-Step Breakdown

### STEP 2a: Verify code is in place
```bash
ls -la /tmp/supplier-rfp-agent/lambda/
```

**Expected output:**
```
-rw-r--r--  1 root root  450+ rfp_agent_handler.py
-rw-r--r--  1 root root  XXX  Dockerfile
```

---

### STEP 2b: Build Docker image
```bash
cd /tmp/supplier-rfp-agent
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .
```

**Wait for:**
```
Successfully tagged supplier-rfp-agent:latest
```

If Docker fails with storage error:
```bash
docker system prune -a -f
# Then retry build
```

---

### STEP 2c: Tag for ECR
```bash
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

---

### STEP 2d: Push to ECR
```bash
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

**Wait for:**
```
latest: digest: sha256:XXX
```

---

### STEP 2e: Update Lambda function
```bash
aws lambda update-function-code \
  --function-name rfp-agent-handler \
  --image-uri 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest \
  --region us-east-1
```

**Expected output:**
```json
{
    "FunctionName": "rfp-agent-handler",
    "LastModified": "2026-06-12T...",
    ...
}
```

---

## 🧪 STEP 3: Test Lambda Directly

### STEP 3a: Create test payload
```bash
cat > /tmp/full_test.json << 'EOF'
{"body": "{\"message\": \"We need 500 brake sensors. High-precision ABS, IP67 rated, -40 to 125C. Deadline: 2026-09-30.\"}"}
EOF
```

### STEP 3b: Invoke Lambda
```bash
aws lambda invoke \
  --function-name rfp-agent-handler \
  --cli-binary-format raw-in-base64-out \
  --payload file:///tmp/full_test.json \
  --region us-east-1 \
  /tmp/response.json
```

### STEP 3c: View response
```bash
echo ""
echo "=== RESPONSE ===" 
cat /tmp/response.json | jq .
```

### STEP 3d: Formatted view
```bash
echo ""
echo "=== FORMATTED RESPONSE ===" 
cat /tmp/response.json | jq '.body | fromjson' -r
```

### STEP 3e: Extract summary
```bash
echo ""
echo "=== SUMMARY ===" 
cat /tmp/response.json | jq '.body | fromjson | .summary'
```

---

## 🌐 STEP 4: Test via API Gateway

### STEP 4a: Test from CloudShell using curl
```bash
curl -X POST https://u2iao043li.execute-api.us-east-1.amazonaws.com/prod/process-rfp \
  -H "Content-Type: application/json" \
  -d '{"message": "We need 500 brake sensors. High-precision ABS, IP67 rated, -40 to 125C. Deadline: 2026-09-30."}'
```

---

## 🖥️ PowerShell Test (from your machine)

### STEP 4b: Test from PowerShell on your PC

```powershell
# Set variables
$uri = "https://u2iao043li.execute-api.us-east-1.amazonaws.com/prod/process-rfp"
$body = @{
    message = "We need 500 brake sensors. High-precision ABS, IP67 rated, -40 to 125C. Deadline: 2026-09-30."
} | ConvertTo-Json

# Send request
$response = Invoke-WebRequest -Uri $uri -Method POST -ContentType "application/json" -Body $body

# Show status
Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green

# Parse and display response
$data = $response.Content | ConvertFrom-Json
Write-Host ""
Write-Host "=== RFP WORKFLOW RESULT ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "RFP ID: $($data.rfp_id)" -ForegroundColor White
Write-Host "Suppliers Found: $($data.summary.suppliers_contacted)" -ForegroundColor White
Write-Host "Proposals Scored: $($data.summary.proposals_received)" -ForegroundColor White
Write-Host "Recommended: $($data.summary.recommended_supplier)" -ForegroundColor Yellow
Write-Host "Next Step: $($data.summary.next_step)" -ForegroundColor White
Write-Host ""

# Full response
Write-Host "=== FULL RESPONSE ===" -ForegroundColor Cyan
$data | ConvertTo-Json -Depth 10 | Write-Host
```

---

## 📊 Expected Outputs

### After Step 2e (Lambda updated):
```json
{
    "FunctionName": "rfp-agent-handler",
    "FunctionArn": "arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler",
    "LastModified": "2026-06-12T14:30:00.000+0000",
    "CodeSize": 0,
    "CodeSha256": "sha256:XXX"
}
```

### After Step 3 (Lambda test):
```json
{
  "statusCode": 200,
  "body": {
    "workflow_status": "SUCCESS",
    "rfp_id": "RFP-20260612-XXXXXXXX",
    "timestamp": "2026-06-12T14:35:00.123456",
    "requirement": "We need 500 brake sensors...",
    "tool_results": {
      "tool_1_supplier_lookup": {
        "status": "success",
        "supplier_count": 4,
        "suppliers": [
          {
            "name": "AutoParts Inc",
            "capabilities": "High-precision sensors",
            "email": "rfp@autoparts.com"
          },
          ...
        ]
      },
      "tool_2_rfp_generation": {
        "status": "success",
        "rfp_id": "RFP-20260612-XXXXXXXX",
        "s3_location": "rfp-documents/RFP-20260612-XXXXXXXX.txt"
      },
      "tool_3_email_dispatch": {
        "status": "success",
        "email_count": 4
      },
      "tool_4_proposal_fetch": {
        "status": "success",
        "proposal_count": 4
      },
      "tool_5_scoring": {
        "status": "success",
        "scored_count": 4,
        "top_3_scores": [
          {
            "supplier": "AutoParts Inc",
            "score": 87.5,
            "price": 2500,
            "delivery_days": 20
          },
          ...
        ]
      },
      "tool_6_recommendation": {
        "status": "success",
        "recommendation_count": 2,
        "approval_status": "READY_FOR_APPROVAL",
        "recommendations": [
          {
            "Rank": 1,
            "SupplierName": "AutoParts Inc",
            "TotalScore": 87.5,
            "Price": 2500,
            "DeliveryTime": 20,
            "Quality": 92,
            "Compliance": "Yes",
            "RiskFlags": [],
            "Recommendation": "Consider for PRIMARY supplier"
          },
          ...
        ]
      }
    },
    "summary": {
      "suppliers_contacted": 4,
      "proposals_received": 4,
      "recommended_supplier": "AutoParts Inc",
      "next_step": "AWAITING_APPROVAL"
    }
  }
}
```

---

## ✅ Validation Checklist

- [ ] Docker image builds successfully
- [ ] Image pushed to ECR
- [ ] Lambda function updated
- [ ] Lambda test returns statusCode 200
- [ ] 4 suppliers found
- [ ] 4 proposals scored
- [ ] Top-2 recommendations generated
- [ ] API Gateway test returns statusCode 200
- [ ] All tool results include "success" status
- [ ] RFP ID created (RFP-YYYYMMDD-XXXXXXXX format)

---

## 🔍 Troubleshooting

### Docker build fails
```bash
# Clear Docker storage
docker system prune -a -f

# Retry build
cd /tmp/supplier-rfp-agent
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .
```

### Push fails - not authenticated
```bash
# Re-authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 689050397154.dkr.ecr.us-east-1.amazonaws.com
```

### Lambda test returns error
```bash
# Check Lambda logs
aws logs tail /aws/lambda/rfp-agent-handler --follow --region us-east-1

# Or view specific invocation
aws logs get-log-events \
  --log-group-name /aws/lambda/rfp-agent-handler \
  --log-stream-name '2024/06/12/[$LATEST]XXXXXXX' \
  --region us-east-1
```

### API returns "Internal server error"
```bash
# Check API Gateway CloudWatch logs
aws logs tail /aws/apigateway/rfp-agent-handler --follow --region us-east-1
```

---

## 📝 Notes

- **Region**: All commands use `us-east-1`
- **Account**: `689050397154`
- **API Endpoint**: `https://u2iao043li.execute-api.us-east-1.amazonaws.com/prod/process-rfp`
- **Lambda Function**: `rfp-agent-handler`
- **ECR Repository**: `supplier-rfp-agent`

---

## ⏱️ Expected Timing

- Build image: 2-3 minutes
- Push to ECR: 1 minute
- Update Lambda: 30 seconds
- Lambda test: 10-15 seconds
- API test: 10-15 seconds

**Total deployment + test time: ~5-10 minutes**

---

## 🎯 Next Step

1. Open CloudShell
2. Paste the "Quick Deploy (All-in-One)" command
3. Wait for completion
4. Return to PowerShell for STEP 4 test
5. Verify all 6 tools executed successfully

**You're ready to go! 🚀**
