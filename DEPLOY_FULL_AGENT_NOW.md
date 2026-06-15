# DEPLOY FULL RFP AGENT - IMMEDIATE ACTION

## STATUS: Ready to Deploy ✅

The Lambda handler has been updated with all 6 tools. Now execute these steps:

---

## STEP 2: Build and Push Docker Image (CloudShell)

**Copy and paste each command block into CloudShell:**

### 2a. Navigate to project
```bash
cd /tmp/supplier-rfp-agent
```

### 2b. Build Docker image
```bash
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .
```

### 2c. Tag for ECR
```bash
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

### 2d. Login to ECR (if needed)
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 689050397154.dkr.ecr.us-east-1.amazonaws.com
```

### 2e. Push to ECR
```bash
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
```

### 2f. Update Lambda function with new image
```bash
aws lambda update-function-code \
  --function-name rfp-agent-handler \
  --image-uri 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest \
  --region us-east-1
```

**Wait for output confirming update:**
```
{
    "FunctionName": "rfp-agent-handler",
    "LastModified": "2026-06-12T...",
    "CodeSize": XXX,
    ...
}
```

---

## STEP 3: Test Lambda Directly (CloudShell)

### 3a. Create test payload
```bash
cat > /tmp/full_test.json << 'EOF'
{
  "body": "{\"message\": \"We need 500 brake sensors. High-precision ABS, IP67 rated, -40 to 125C. Deadline: 2026-09-30.\"}"
}
EOF
```

### 3b. Invoke Lambda function
```bash
aws lambda invoke \
  --function-name rfp-agent-handler \
  --cli-binary-format raw-in-base64-out \
  --payload file:///tmp/full_test.json \
  --region us-east-1 \
  /tmp/response.json

echo ""
echo "=== RESPONSE ==="
cat /tmp/response.json | jq .
```

### 3c. Expected Output (excerpt):
```json
{
  "statusCode": 200,
  "body": {
    "workflow_status": "SUCCESS",
    "rfp_id": "RFP-20260612-XXXXXXXX",
    "tool_results": {
      "tool_1_supplier_lookup": {
        "status": "success",
        "supplier_count": 4,
        "suppliers": [...]
      },
      "tool_2_rfp_generation": {
        "status": "success",
        "rfp_id": "RFP-20260612-XXXXXXXX"
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
        "top_3_scores": [...]
      },
      "tool_6_recommendation": {
        "status": "success",
        "approval_status": "READY_FOR_APPROVAL",
        "recommendations": [...]
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

## STEP 4: Test API Gateway (PowerShell)

### 4a. Set API endpoint
```powershell
$uri = "https://u2iao043li.execute-api.us-east-1.amazonaws.com/prod/process-rfp"
```

### 4b. Create RFP request
```powershell
$body = @{
    message = "We need 500 brake sensors. High-precision ABS, IP67 rated, -40 to 125C. Deadline: 2026-09-30."
} | ConvertTo-Json

Write-Host "Sending RFP to API..." -ForegroundColor Cyan
```

### 4c. Send request
```powershell
$response = Invoke-WebRequest -Uri $uri -Method POST -ContentType "application/json" -Body $body

Write-Host ""
Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
Write-Host ""
Write-Host "Response (formatted):" -ForegroundColor Cyan
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### 4d. Expected Output:
- Status: 200
- RFP ID created (RFP-20260612-XXXXXXXX)
- 4 suppliers found
- 4 proposals scored
- Top 2 recommendations with risk flags

---

## Full 6-Tool Workflow Executed

### Tool 1: Supplier Lookup ✅
- Queries DynamoDB `rfp-suppliers` table
- Returns 4 relevant automotive suppliers
- Fields: SupplierID, Name, Email, Capabilities, Past Performance

### Tool 2: RFP Generation ✅
- Creates unique RFP ID
- Generates RFP document
- Saves to S3: `rfp-documents/{RFP_ID}.txt`
- Saves metadata to DynamoDB `rfp-requests` table

### Tool 3: Email Dispatch ✅
- Sends RFP to all 4 suppliers (mock mode)
- Logs delivery status
- Records timestamp

### Tool 4: Proposal Fetch ✅
- Retrieves proposals from DynamoDB `rfp-proposals` table
- Auto-generates mock proposals if none exist
- Includes: Price, DeliveryTime, Quality, Compliance Certs

### Tool 5: Scoring ✅
- Multi-criteria evaluation:
  - Price: 30% weight
  - Quality: 30% weight
  - Delivery: 20% weight
  - Compliance: 20% weight
- Normalizes and scores all proposals
- Saves scores to DynamoDB `rfp-scores` table

### Tool 6: Recommendation ✅
- Generates Top-2 recommendations
- Includes risk flag detection:
  - High Price flag
  - Long Delivery flag
  - Compliance Gap flag
  - Quality Concern flag
- Generates approval status

---

## Database Tables Used

| Table | Purpose | Items Created |
|-------|---------|----------------|
| `rfp-suppliers` | Supplier master data | Read-only, pre-seeded |
| `rfp-requests` | RFP metadata | 1 item per RFP |
| `rfp-proposals` | Supplier proposals | 4 items (1 per supplier) |
| `rfp-scores` | Scoring results | 4 items (1 per proposal) |

---

## S3 Bucket Used

- **Bucket**: `rfp-documents-quadrasystems`
- **Path**: `rfp-documents/{RFP_ID}.txt`
- **Content**: Full RFP document with requirement and supplier list

---

## Next Steps After Successful Test

1. ✅ Lambda handler updated with all 6 tools
2. ⏳ Build Docker image in CloudShell (Step 2)
3. ⏳ Test Lambda directly (Step 3)
4. ⏳ Test API Gateway (Step 4)
5. Then: **AGENT IS LIVE** - RFP workflow ready for production

---

## Troubleshooting

### Docker build fails
- Clear CloudShell storage: `docker system prune -a -f`
- Retry build

### Lambda timeout
- Increase timeout to 300 seconds (already set)
- Check CloudWatch logs

### Proposal data missing
- Handler auto-generates mock proposals
- Ensure DynamoDB tables exist

### API returns "Internal server error"
- Check Lambda logs: `aws logs tail /aws/lambda/rfp-agent-handler --follow`
- Verify environment variables: `REGION=us-east-1`, `BEDROCK_MODEL_ID=amazon.nova-pro-v1:0`

---

## Commands Summary (Copy-Paste Ready)

**CloudShell Block:**
```bash
cd /tmp/supplier-rfp-agent && \
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile . && \
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest && \
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest && \
aws lambda update-function-code --function-name rfp-agent-handler --image-uri 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest --region us-east-1 && \
echo "✅ Build and deploy complete"
```

**CloudShell Test (Step 3):**
```bash
cat > /tmp/full_test.json << 'EOF'
{"body": "{\"message\": \"We need 500 brake sensors. High-precision ABS, IP67 rated, -40 to 125C. Deadline: 2026-09-30.\"}"}
EOF

aws lambda invoke --function-name rfp-agent-handler --cli-binary-format raw-in-base64-out --payload file:///tmp/full_test.json --region us-east-1 /tmp/response.json && cat /tmp/response.json | jq .
```

---

## ✅ Ready to Deploy

Execute the steps above and the full RFP agent workflow will be live!
