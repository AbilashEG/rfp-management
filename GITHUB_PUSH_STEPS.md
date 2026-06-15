# Push Backend Code to GitHub - Step by Step

**Repository**: https://github.com/AbilashEG/RFP  
**Status**: ✅ Backend validated, ready to push

---

## ✅ Pre-Push Validation

**All checks passed**:
- ✅ Handler has all 6 tools
- ✅ Requirements.txt correct
- ✅ Config.py correct
- ✅ Dockerfile correct
- ✅ All tool files present
- ✅ Database integration working
- ✅ S3 integration working

See: `BACKEND_VALIDATION_CHECKLIST.md`

---

## Step 1: Create .gitignore

**File**: `.gitignore` (in root of `supplier-rfp-agent/`)

```
# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.Python

# Environment
.env
.env.local
.env.*.local

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# AWS
.aws/
*.pem

# CDK
cdk.out/
cdk.json

# Logs
*.log
logs/
```

**Save this file in**: `c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent\.gitignore`

---

## Step 2: Create/Update README.md

**File**: `README.md`

```markdown
# RFP Management Agent

Complete RFP (Request for Proposal) management system powered by AWS Lambda, DynamoDB, and S3.

## Features

### 6 Integrated Tools
1. **Supplier Lookup** - Query DynamoDB to find relevant suppliers
2. **RFP Generation** - Create and store RFP documents
3. **Email Dispatch** - Send RFPs to suppliers
4. **Proposal Fetch** - Retrieve and manage supplier proposals
5. **Scoring** - Multi-criteria evaluation (Price 30%, Quality 30%, Delivery 20%, Compliance 20%)
6. **Recommendation** - Generate Top-2 recommendations with risk analysis

### Architecture
- **Lambda**: Serverless compute (Docker container)
- **DynamoDB**: 4 tables (suppliers, requests, proposals, scores)
- **S3**: Document storage (`rfp-documents-quadrasystems`)
- **API Gateway**: REST API endpoint

### Deployment
- **Production**: GitHub Actions CI/CD
- **Quick Test**: AWS CloudShell

## Quick Start

### Deploy via GitHub Actions
```bash
git push origin main
```
GitHub Actions automatically:
1. Builds Docker image
2. Pushes to ECR
3. Updates Lambda function
4. Runs tests

### Test Lambda
```bash
aws lambda invoke \
  --function-name rfp-agent-handler \
  --payload '{"body":"{\"message\":\"We need 500 brake sensors...\"}"}' \
  --region us-east-1 \
  /tmp/response.json

cat /tmp/response.json
```

## Configuration

**File**: `config.py`

- `REGION`: us-east-1
- `BEDROCK_MODEL_ID`: amazon.nova-pro-v1:0
- `AWS_ACCOUNT_ID`: 689050397154
- Scoring weights configurable

## Directory Structure

```
supplier-rfp-agent/
├── lambda/                    # Lambda handler & Docker
│   ├── rfp_agent_handler.py  # Main handler with 6 tools
│   └── Dockerfile            # Lambda container
├── tools/                     # 6 RFP tools
│   ├── supplier_lookup_tool.py
│   ├── rfp_generator_tool.py
│   ├── email_dispatch_tool.py
│   ├── proposal_fetch_tool.py
│   ├── scoring_tool.py
│   └── recommendation_tool.py
├── agent/                     # Strands Agent integration
│   ├── agent_runner.py
│   ├── rfp_agent.py
│   └── system_prompt.py
├── infra/                     # CDK Infrastructure as Code
├── setup/                     # DynamoDB & S3 setup scripts
├── tests/                     # Unit tests
├── config.py                  # Configuration
└── requirements.txt           # Dependencies
```

## API Endpoint

**Live endpoint**: https://u2iao043li.execute-api.us-east-1.amazonaws.com/prod/process-rfp

### Request
```json
{
  "message": "We need 500 brake sensors. High-precision ABS, IP67 rated, -40 to 125C. Deadline: 2026-09-30."
}
```

### Response
```json
{
  "workflow_status": "SUCCESS",
  "rfp_id": "RFP-20260612-XXXXXXXX",
  "tool_results": {
    "tool_1_supplier_lookup": {...},
    "tool_2_rfp_generation": {...},
    "tool_3_email_dispatch": {...},
    "tool_4_proposal_fetch": {...},
    "tool_5_scoring": {...},
    "tool_6_recommendation": {...}
  },
  "summary": {
    "suppliers_contacted": 4,
    "proposals_received": 4,
    "recommended_supplier": "AutoParts Inc",
    "next_step": "AWAITING_APPROVAL"
  }
}
```

## Deployment

### GitHub Actions (Recommended)
See: `.github/workflows/deploy-to-lambda.yml`

Automatically deploys on `git push origin main`:
1. Builds Docker image
2. Pushes to ECR
3. Updates Lambda function
4. Runs tests

### Manual CloudShell Deployment
```bash
cd /tmp/supplier-rfp-agent
docker build -t supplier-rfp-agent:latest -f lambda/Dockerfile .
docker tag supplier-rfp-agent:latest 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
docker push 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest
aws lambda update-function-code --function-name rfp-agent-handler --image-uri 689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent:latest --region us-east-1
```

## Dependencies

- `strands-agents==0.1.7` - Agent framework
- `boto3==1.38.0` - AWS SDK
- `aws-cdk-lib==2.100.0` - Infrastructure as Code

## Testing

```bash
# Unit tests
pytest tests/

# Lambda test
python tests/test_agent_flow.py
```

## AWS Resources Required

- Lambda function: `rfp-agent-handler`
- DynamoDB tables: `rfp-suppliers`, `rfp-requests`, `rfp-proposals`, `rfp-scores`
- S3 bucket: `rfp-documents-quadrasystems`
- IAM role: `rfp-agent-lambda-role`
- ECR repository: `supplier-rfp-agent`
- API Gateway: `supplier-rfp-agent-api`

## Author

Developed for Quadra Systems - RFP Management

## License

Proprietary - Quadra Systems
```

**Save this file in**: `c:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent\README.md`

---

## Step 3: Open PowerShell and Navigate

```powershell
cd "C:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent"
```

---

## Step 4: Initialize Git (if not done)

```powershell
git init
```

---

## Step 5: Add All Files

```powershell
git add .
```

---

## Step 6: Create Initial Commit

```powershell
git commit -m "Initial commit: Full RFP Agent with 6 tools, DynamoDB, S3, and Lambda integration"
```

**Expected output**:
```
[main (root-commit) abc1234] Initial commit: Full RFP Agent with 6 tools...
 20 files changed, 5000 insertions(+)
 create mode 100644 .gitignore
 create mode 100644 README.md
 create mode 100644 config.py
 ... (more files)
```

---

## Step 7: Add GitHub Remote

```powershell
git remote add origin https://github.com/AbilashEG/RFP.git
```

---

## Step 8: Rename Branch to Main (if needed)

```powershell
git branch -M main
```

---

## Step 9: Push to GitHub

```powershell
git push -u origin main
```

**Expected output**:
```
Enumerating objects: 30, done.
Counting objects: 100% (30/30), done.
Delta compression using up to 8 threads
Compressing objects: 100% (28/28), done.
Writing objects: 100% (30/30), 150 KiB | 500 KiB/s, done.
Total 30 (delta 0), reused 0 (delta 0), pack-reused 0

To https://github.com/AbilashEG/RFP.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## Step 10: Verify on GitHub

1. Go to: https://github.com/AbilashEG/RFP
2. Should see all files uploaded
3. Check files are present:
   - ✅ `lambda/rfp_agent_handler.py`
   - ✅ `lambda/Dockerfile`
   - ✅ `tools/` (all 6 tools)
   - ✅ `config.py`
   - ✅ `requirements.txt`
   - ✅ `README.md`
   - ✅ `.gitignore`

---

## Complete PowerShell Script (Copy-Paste All At Once)

```powershell
# Navigate to project
cd "C:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent"

# Initialize git
git init

# Add all files
git add .

# Create commit
git commit -m "Initial commit: Full RFP Agent with 6 tools, DynamoDB, S3, and Lambda integration"

# Add remote
git remote add origin https://github.com/AbilashEG/RFP.git

# Rename branch
git branch -M main

# Push to GitHub
git push -u origin main

# Verify
Write-Host ""
Write-Host "✅ Push complete!"
Write-Host "Repository: https://github.com/AbilashEG/RFP"
Write-Host ""
git remote -v
git log --oneline
```

---

## Troubleshooting

### Error: "remote already exists"
```powershell
git remote remove origin
git remote add origin https://github.com/AbilashEG/RFP.git
```

### Error: "permission denied"
```powershell
# Use GitHub personal access token instead of password
# or set up SSH key
```

### Error: "branch already exists"
```powershell
# Just push
git push -u origin main
```

### Error: "authentication failed"
```powershell
# Option 1: Use personal access token
git push https://YOUR_TOKEN@github.com/AbilashEG/RFP.git main

# Option 2: Set up SSH
ssh-keygen -t ed25519 -C "your_email@example.com"
# Add public key to GitHub
```

---

## After Push: Set Up GitHub Actions

1. Create directory: `.github/workflows/`
2. Create file: `.github/workflows/deploy-to-lambda.yml`
3. Copy content from `GITHUB_DEPLOYMENT_GUIDE.md`
4. Commit and push:
   ```powershell
   git add .github/workflows/
   git commit -m "Add GitHub Actions CI/CD workflow"
   git push origin main
   ```

---

## Verify Deployment

After push:
- ✅ Check GitHub repo: https://github.com/AbilashEG/RFP
- ✅ Files should be visible
- ✅ Commit history visible
- ✅ README visible

---

## Next: GitHub Actions Setup

After push is successful:
1. Create `.github/workflows/deploy-to-lambda.yml` (see `GITHUB_DEPLOYMENT_GUIDE.md`)
2. Set up IAM role for GitHub Actions
3. Push workflow file
4. Automatic deployments enabled

---

## Summary

**What you're doing**:
- ✅ Creating git history
- ✅ Uploading backend code to GitHub
- ✅ Setting up for automatic deployment
- ✅ Enabling team collaboration

**Result**:
- ✅ Code on GitHub
- ✅ Ready for GitHub Actions
- ✅ Ready for team collaboration
- ✅ Professional CI/CD setup

---

**Status**: ✅ Ready to push  
**Action**: Follow steps 1-10 above  
**Time**: ~5 minutes  
**Result**: Backend on GitHub, ready for CI/CD
