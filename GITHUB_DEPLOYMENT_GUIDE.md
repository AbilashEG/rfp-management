# GitHub-Based Deployment (CI/CD) - Best Practice

**Date**: June 12, 2026  
**Approach**: Push code to GitHub → GitHub Actions → AWS Lambda  
**Status**: ✅ Recommended Production Method

---

## Why GitHub Deployment is Better

| Aspect | CloudShell | GitHub CI/CD |
|--------|-----------|------------|
| **Version Control** | ❌ Manual | ✅ Git history |
| **Automation** | ❌ Manual steps | ✅ Automatic triggers |
| **Rollback** | ❌ Difficult | ✅ Easy (revert commit) |
| **Team Collaboration** | ❌ No | ✅ Pull requests, reviews |
| **Audit Trail** | ❌ No | ✅ Complete history |
| **Scalability** | ❌ Manual | ✅ Automated |
| **Production Ready** | ❌ Ad-hoc | ✅ Professional |

---

## Architecture: GitHub → Lambda

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Local Machine                       │
│                  (Windows PowerShell)                       │
│                                                             │
│  1. Edit code (rfp_agent_handler.py)                       │
│  2. Git commit & push                                       │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                        │
│  (github.com/your-repo/supplier-rfp-agent)                 │
│                                                             │
│  ✅ Stores code                                            │
│  ✅ Triggers GitHub Actions on push                        │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼ (Webhook)
┌─────────────────────────────────────────────────────────────┐
│             GitHub Actions (CI/CD Pipeline)                │
│                                                             │
│  Step 1: Checkout code                                     │
│  Step 2: Build Docker image                                │
│  Step 3: Push to ECR                                       │
│  Step 4: Update Lambda function                            │
│  Step 5: Run tests                                         │
│  Step 6: Slack notification                                │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                   AWS Resources                            │
│                                                             │
│  ✅ ECR (Docker image stored)                              │
│  ✅ Lambda (Updated automatically)                         │
│  ✅ S3 (RFP documents)                                     │
│  ✅ DynamoDB (Proposals, scores)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create GitHub Repository

### 1a. Create empty repo on GitHub
- Go: https://github.com/new
- **Repository name**: `supplier-rfp-agent`
- **Description**: "RFP Management Agent with AWS Lambda & DynamoDB"
- **Visibility**: Private (for business use)
- **Initialize**: No README

### 1b. Clone locally
```powershell
cd C:\Users\AbilashEEG\Desktop\RFP MANAGEMENT
git clone https://github.com/YOUR_USERNAME/supplier-rfp-agent.git
cd supplier-rfp-agent
```

### 1c. Copy your code
```powershell
# Copy all project files from supplier-rfp-agent/ to the cloned repo
Copy-Item "C:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent\*" -Destination "." -Recurse -Force
```

---

## Step 2: Set Up GitHub Actions

### 2a. Create workflow directory
```powershell
mkdir .github\workflows
```

### 2b. Create deployment workflow file

**File**: `.github/workflows/deploy-to-lambda.yml`

```yaml
name: Deploy to AWS Lambda

on:
  push:
    branches:
      - main
    paths:
      - 'lambda/**'
      - 'requirements.txt'
      - '.github/workflows/deploy-to-lambda.yml'

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: supplier-rfp-agent
  LAMBDA_FUNCTION_NAME: rfp-agent-handler

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    permissions:
      contents: read
      id-token: write
    
    steps:
      # Step 1: Checkout code
      - name: Checkout code
        uses: actions/checkout@v3

      # Step 2: Configure AWS credentials
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::689050397154:role/github-actions-role
          aws-region: ${{ env.AWS_REGION }}

      # Step 3: Login to ECR
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      # Step 4: Build Docker image
      - name: Build Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -f lambda/Dockerfile .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest

      # Step 5: Push image to ECR
      - name: Push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      # Step 6: Update Lambda function
      - name: Update Lambda function
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          aws lambda update-function-code \
            --function-name ${{ env.LAMBDA_FUNCTION_NAME }} \
            --image-uri $ECR_REGISTRY/$ECR_REPOSITORY:latest \
            --region ${{ env.AWS_REGION }}

      # Step 7: Wait for Lambda update
      - name: Wait for Lambda update
        run: sleep 10

      # Step 8: Run Lambda tests
      - name: Test Lambda function
        run: |
          RESPONSE=$(aws lambda invoke \
            --function-name ${{ env.LAMBDA_FUNCTION_NAME }} \
            --cli-binary-format raw-in-base64-out \
            --payload '{"body":"{\"message\":\"We need 500 brake sensors. High-precision ABS, IP67 rated, -40 to 125C. Deadline: 2026-09-30.\"}"}' \
            --region ${{ env.AWS_REGION }} \
            /tmp/response.json && cat /tmp/response.json)
          
          echo "Lambda Response: $RESPONSE"
          
          # Check for success
          if echo "$RESPONSE" | grep -q "\"workflow_status\": \"SUCCESS\""; then
            echo "✅ Lambda test passed!"
          else
            echo "❌ Lambda test failed!"
            exit 1
          fi

      # Step 9: Notify on success
      - name: Notify success
        if: success()
        run: |
          echo "✅ Deployment successful!"
          echo "Lambda function updated with Docker image: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:latest"

      # Step 10: Notify on failure
      - name: Notify failure
        if: failure()
        run: |
          echo "❌ Deployment failed!"
          exit 1
```

---

## Step 3: Set Up AWS IAM for GitHub Actions

### 3a. Create IAM Role for GitHub Actions

**AWS Console → IAM → Roles → Create Role**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::689050397154:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_USERNAME/supplier-rfp-agent:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

### 3b. Attach permissions policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:us-east-1:689050397154:repository/supplier-rfp-agent"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode"
      ],
      "Resource": "arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-east-1:689050397154:function:rfp-agent-handler"
    }
  ]
}
```

---

## Step 4: Push to GitHub

### 4a. Initialize git and add files
```powershell
cd supplier-rfp-agent
git init
git add .
git commit -m "Initial commit: RFP Agent with all 6 tools"
```

### 4b. Add remote and push
```powershell
git remote add origin https://github.com/YOUR_USERNAME/supplier-rfp-agent.git
git branch -M main
git push -u origin main
```

---

## Step 5: Verify GitHub Actions Workflow

### 5a. Check workflow runs
- Go: https://github.com/YOUR_USERNAME/supplier-rfp-agent/actions
- Should see workflow running
- Wait for completion (5-10 minutes)

### 5b. Check logs
- Click on workflow run
- See each step: Build → Push → Update → Test

### 5c. Verify Lambda updated
- AWS Console → Lambda → rfp-agent-handler
- Check "Last Modified" timestamp (should be recent)
- Check "Image URI" (should show latest commit SHA)

---

## Workflow: Making Updates

### From now on, deployment is automatic:

**1. Edit code locally** (e.g., update handler)
```powershell
# Edit rfp_agent_handler.py
code lambda/rfp_agent_handler.py
```

**2. Commit and push**
```powershell
git add lambda/rfp_agent_handler.py
git commit -m "Add new feature to Tool 1"
git push origin main
```

**3. Automatic deployment**
- GitHub Actions triggered automatically
- Docker image built
- Pushed to ECR
- Lambda updated
- Tests run
- You're notified

**4. Check status**
- GitHub Actions tab → See workflow progress
- Takes ~5-10 minutes

**5. Rollback if needed**
```powershell
# Revert last commit
git revert HEAD
git push origin main

# GitHub Actions automatically deploys the previous version
```

---

## Complete .github/workflows Directory Structure

```
.github/
└── workflows/
    ├── deploy-to-lambda.yml (created above)
    ├── test-locally.yml (optional: run tests on PR)
    └── security-scan.yml (optional: scan for vulnerabilities)
```

---

## Git Workflow Best Practice

### For small changes:
```powershell
git add .
git commit -m "Update handler with new scoring logic"
git push origin main
```

### For big changes (recommended):
```powershell
# Create feature branch
git checkout -b feature/new-tool
# Make changes
git add .
git commit -m "Add Tool 7: Advanced Analytics"
git push origin feature/new-tool

# Create Pull Request on GitHub
# Review → Approve → Merge to main
# GitHub Actions automatically deploys
```

---

## Monitoring Deployments

### GitHub Actions Dashboard
- URL: `https://github.com/YOUR_USERNAME/supplier-rfp-agent/actions`
- Shows: Each workflow run, status, logs, duration

### AWS CloudWatch Logs
- Check Lambda logs: `/aws/lambda/rfp-agent-handler`
- View deployment history

### Slack Notification (Optional)
Add to workflow to notify on success/failure:

```yaml
- name: Slack Notification
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Lambda deployment ${{ job.status }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "Lambda *${{ job.status }}* for commit ${{ github.sha }}"
            }
          }
        ]
      }
```

---

## Advantages of GitHub Deployment

✅ **Version Control**: Every change tracked  
✅ **Automated**: No manual CloudShell commands  
✅ **Rollback**: Easy revert to previous version  
✅ **Audit Trail**: Who changed what and when  
✅ **Team Collaboration**: Pull requests, code reviews  
✅ **Testing**: Automatic tests before deployment  
✅ **Production Ready**: Industry standard approach  
✅ **Scaling**: Deploy multiple lambdas easily  

---

## Troubleshooting

### Workflow fails: "Role not found"
**Solution**: Check IAM role ARN in workflow matches AWS account

### Workflow fails: "ECR permission denied"
**Solution**: Verify IAM policy includes ECR permissions

### Workflow fails: "Lambda update timeout"
**Solution**: Increase sleep time in workflow (Step 7)

### Lambda test fails in workflow
**Solution**: Check CloudWatch logs for detailed error message

---

## Next Steps

1. ✅ Create GitHub repository
2. ✅ Set up IAM role for GitHub Actions
3. ✅ Create `.github/workflows/deploy-to-lambda.yml`
4. ✅ Push code to GitHub
5. ✅ Monitor first deployment in GitHub Actions
6. ✅ Verify Lambda updated
7. ✅ Make future changes via git push (automatic deployment)

---

## Complete Comparison

| Task | CloudShell | GitHub |
|------|-----------|--------|
| Initial setup | 10 min | 30 min (one-time) |
| Deployment | Manual command | Automatic on push |
| Rollback | Manual revert | `git revert HEAD` |
| Team collaboration | Not supported | Full support |
| Audit trail | None | Complete |
| Testing | Manual | Automatic |
| Scaling | Difficult | Easy |

**GitHub is the professional, scalable approach!** 🚀

---

## Recommendation

**For Production**: Use GitHub CI/CD (Recommended)  
**For Quick Testing**: Use CloudShell (Ad-hoc)

**Your situation**: Since you have production requirements, **use GitHub deployment**.

---

**Status**: Ready to set up GitHub Actions  
**Next Action**: Create GitHub repository and IAM role  
**Questions?**: See troubleshooting section above
