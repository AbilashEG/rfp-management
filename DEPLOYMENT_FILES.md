# Deployment Files Overview

This repository includes three main files for deployment:

## 1. `cloudshell-deploy.sh` (Main - Use This!)

**Fully automated CloudShell deployment script**

Handles entire deployment in one command:
```bash
bash cloudshell-deploy.sh
```

### What it does:
1. Installs Python dependencies
2. Builds 7 Lambda ZIPs with **CORRECT structure** (python dependencies at root)
3. Uploads all ZIPs to S3
4. Deploys code to all 7 Lambda functions in order:
   - orchestrator → rfp-agent-orchestrator-v2
   - supplier_lookup_tool → supplier_lookup_tool-v2
   - rfp_generator_tool → rfp_generator_tool-v2
   - email_dispatch_tool → email_dispatch_tool-v2
   - proposal_fetch_tool → proposal_fetch_tool-v2
   - scoring_tool → scoring_tool-v2
   - recommendation_tool → recommendation_tool-v2
5. Tests orchestrator Lambda
6. Displays status and API endpoint

**Usage:** CloudShell only

---

## 2. `build-zips-local.py` (Optional - Local Testing)

**Python script to build ZIPs locally on your machine**

Use if you want to verify ZIP structure before CloudShell:
```bash
# On local machine
pip install -r RFP-main/requirements.txt -t package/
python3 build-zips-local.py
```

### What it does:
1. Creates 7 Lambda ZIPs locally
2. Verifies correct structure
3. Lists ZIP file sizes
4. Shows next steps

**Usage:** Your local machine (optional, for verification)

---

## 3. `CLOUDSHELL_DEPLOYMENT.md` (Detailed Guide)

**Complete documentation for deployment**

Includes:
- Prerequisites checklist
- Quick deployment (5 minutes)
- Manual deployment steps (if needed)
- Troubleshooting guide
- Lambda testing commands
- CloudWatch logs viewing
- Configuration details
- API testing examples

**Use this if:**
- You need detailed steps
- Something goes wrong
- You want to understand what's happening
- You need manual deployment instructions

---

## File Manifest

### Deployment Scripts
- ✅ `cloudshell-deploy.sh` - Automated CloudShell deployment (MAIN)
- ✅ `build-zips-local.py` - Optional local ZIP builder
- ✅ `CLOUDSHELL_DEPLOYMENT.md` - Detailed deployment guide

### Core Code
- ✅ `RFP-main/agentcore_orchestrator.py` - Main orchestrator
- ✅ `RFP-main/agentcore_memory.py` - Memory management
- ✅ `RFP-main/config.py` - Configuration
- ✅ `RFP-main/requirements.txt` - Dependencies (pydantic removed)
- ✅ `RFP-main/cloudformation-deployment.yaml` - Infrastructure
- ✅ `RFP-main/lambda/` - 6 tool Lambdas (all pydantic removed)

### Documentation
- ✅ `README.md` - Main project documentation
- ✅ `DEPLOYMENT_FILES.md` - This file
- ✅ `CLOUDSHELL_DEPLOYMENT.md` - Detailed deployment guide

### CI/CD
- ✅ `.github/workflows/deploy-to-ecr.yml` - GitHub Actions (optional)
- ✅ `Dockerfile` - For ECR builds (optional)

### Other
- ✅ `.gitignore` - Git ignore rules
- ✅ `README.md` - Quick start guide

---

## Quick Deployment Path

### First Time Setup (Complete)

```bash
# 1. Ensure CloudFormation stack exists with infrastructure
aws cloudformation describe-stacks \
  --stack-name rfp-production-stack \
  --region us-east-1

# 2. In CloudShell, download repo
wget https://github.com/AbilashEG/rfp-management/archive/main.zip
unzip main.zip
cd rfp-management-main

# 3. Run deployment
bash cloudshell-deploy.sh

# 4. Test
aws logs tail /aws/lambda/rfp-agent-orchestrator-v2 --follow
```

---

## Understanding ZIP Structure

### INCORRECT (What failed before)
```
orchestrator.zip
├── lambda-deps/
│   └── python/
│       ├── boto3/
│       ├── botocore/
│       └── ...
├── agentcore_orchestrator.py
└── config.py
❌ Lambda can't find dependencies!
```

### CORRECT (What we do now)
```
orchestrator.zip
├── boto3/               ← At ROOT level
├── botocore/           ← Not nested!
├── site-packages/
├── bin/
├── agentcore_orchestrator.py
├── agentcore_memory.py
└── config.py
✅ Lambda finds everything!
```

This is why we use `cp -r package/. temp-dir/` instead of nested directory structure.

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| "No module named 'boto3'" | ZIP structure wrong - verify dependencies at root |
| "Cannot import module" | ZIP not deployed properly - check S3 upload |
| Lambda timeout | Increase timeout in cloudshell-deploy.sh |
| S3 access denied | Check IAM role permissions |
| API not responding | Check if orchestrator Lambda has been deployed |

---

## Environment Variables

All Lambdas receive:
- `REGION` = us-east-1
- `MODEL` = amazon.nova-pro-v1:0

Set via CloudFormation environment variables.

---

## Support

- 📖 **Documentation**: See CLOUDSHELL_DEPLOYMENT.md
- 🐛 **Issues**: Check CloudWatch logs
- ✅ **Verification**: cloudshell-deploy.sh includes built-in test

---

**Ready to deploy?** Run: `bash cloudshell-deploy.sh` in CloudShell! 🚀
