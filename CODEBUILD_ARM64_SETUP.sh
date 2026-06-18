#!/bin/bash
# ARM64 Docker Image Build using AWS CodeBuild
# Run this in CloudShell to build the ARM64 image natively
# This avoids the disk space and emulation issues in CloudShell's x86 environment

set -e

ACCOUNT_ID="689050397154"
REGION="us-east-1"
REPO_NAME="rfp-agent"
IMAGE_TAG="orchestrator-agentcore-arm64"
GITHUB_REPO="https://github.com/AbilashEEG/rfp-management"  # Update with your actual repo

echo "========================================"
echo "ARM64 Build Setup for AgentCore Runtime"
echo "========================================"

# ============================================================================
# STEP 1: Create IAM Role for CodeBuild
# ============================================================================

echo -e "\n[STEP 1] Creating IAM role for CodeBuild..."

ROLE_NAME="codebuild-rfp-agent-arm64-role"
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

# Check if role exists
if aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
    echo "✓ Role already exists: $ROLE_NAME"
else
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document "$TRUST_POLICY" \
        --region "$REGION"
    echo "✓ Created role: $ROLE_NAME"
fi

# ============================================================================
# STEP 2: Attach Policies to the Role
# ============================================================================

echo -e "\n[STEP 2] Attaching policies to role..."

# Policy for ECR access
ECR_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:'$REGION':'$ACCOUNT_ID':repository/'$REPO_NAME'"
    },
    {
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    }
  ]
}'

# Policy for CloudWatch logs
LOGS_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:'$REGION':'$ACCOUNT_ID':log-group:/aws/codebuild/*"
    }
  ]
}'

# Attach ECR policy
POLICY_NAME="codebuild-rfp-ecr"
if aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME" 2>/dev/null; then
    echo "✓ ECR policy already attached"
else
    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "$POLICY_NAME" \
        --policy-document "$ECR_POLICY"
    echo "✓ Attached ECR policy"
fi

# Attach CloudWatch policy
POLICY_NAME="codebuild-rfp-logs"
if aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME" 2>/dev/null; then
    echo "✓ CloudWatch policy already attached"
else
    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "$POLICY_NAME" \
        --policy-document "$LOGS_POLICY"
    echo "✓ Attached CloudWatch policy"
fi

# ============================================================================
# STEP 3: Create CodeBuild Project
# ============================================================================

echo -e "\n[STEP 3] Creating CodeBuild project..."

PROJECT_NAME="rfp-agent-arm64-build"
ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"

# Build configuration
BUILD_CONFIG='{
  "name": "'$PROJECT_NAME'",
  "source": {
    "type": "GITHUB",
    "location": "'$GITHUB_REPO'",
    "gitCloneDepth": 1
  },
  "artifacts": {
    "type": "NO_ARTIFACTS"
  },
  "environment": {
    "type": "ARM_CONTAINER",
    "image": "aws/codebuild/amazonlinux2-arm64-standard:3.0",
    "computeType": "BUILD_GENERAL1_LARGE",
    "environmentVariables": [
      {
        "name": "AWS_DEFAULT_REGION",
        "value": "'$REGION'",
        "type": "PLAINTEXT"
      },
      {
        "name": "AWS_ACCOUNT_ID",
        "value": "'$ACCOUNT_ID'",
        "type": "PLAINTEXT"
      },
      {
        "name": "IMAGE_REPO_NAME",
        "value": "'$REPO_NAME'",
        "type": "PLAINTEXT"
      },
      {
        "name": "IMAGE_TAG",
        "value": "'$IMAGE_TAG'",
        "type": "PLAINTEXT"
      }
    ],
    "privilegedMode": true
  },
  "serviceRole": "'$ROLE_ARN'",
  "logsConfig": {
    "cloudWatchLogs": {
      "status": "ENABLED",
      "groupName": "/aws/codebuild/'$PROJECT_NAME'"
    }
  }
}'

# Check if project exists
if aws codebuild batch-get-projects --names "$PROJECT_NAME" --region "$REGION" 2>/dev/null | grep -q "$PROJECT_NAME"; then
    echo "✓ CodeBuild project already exists: $PROJECT_NAME"
    # Update it
    aws codebuild update-project \
        --cli-input-json "$BUILD_CONFIG" \
        --region "$REGION"
    echo "✓ Updated project configuration"
else
    aws codebuild create-project \
        --cli-input-json "$BUILD_CONFIG" \
        --region "$REGION"
    echo "✓ Created CodeBuild project: $PROJECT_NAME"
fi

# ============================================================================
# STEP 4: Start the Build
# ============================================================================

echo -e "\n[STEP 4] Starting CodeBuild..."

BUILD_OUTPUT=$(aws codebuild start-build \
    --project-name "$PROJECT_NAME" \
    --region "$REGION" \
    --output json)

BUILD_ID=$(echo "$BUILD_OUTPUT" | jq -r '.build.id')
echo "✓ Build started: $BUILD_ID"
echo -e "\n  Build logs: https://console.aws.amazon.com/codesuite/codebuild/projects/$PROJECT_NAME/history"

# ============================================================================
# STEP 5: Monitor Build Progress
# ============================================================================

echo -e "\n[STEP 5] Monitoring build progress..."
echo "  (This may take 5-10 minutes)"

BUILD_STATUS="IN_PROGRESS"
LOOP_COUNT=0
MAX_LOOPS=60  # 60 * 10 seconds = 10 minutes

while [ "$BUILD_STATUS" == "IN_PROGRESS" ] && [ $LOOP_COUNT -lt $MAX_LOOPS ]; do
    sleep 10
    LOOP_COUNT=$((LOOP_COUNT + 1))
    
    BUILD_STATUS=$(aws codebuild batch-get-builds \
        --ids "$BUILD_ID" \
        --region "$REGION" \
        --query 'builds[0].buildStatus' \
        --output text)
    
    BUILD_PHASE=$(aws codebuild batch-get-builds \
        --ids "$BUILD_ID" \
        --region "$REGION" \
        --query 'builds[0].currentPhase' \
        --output text)
    
    echo "  [$LOOP_COUNT/60] Status: $BUILD_STATUS | Phase: $BUILD_PHASE"
done

# ============================================================================
# STEP 6: Check Build Result
# ============================================================================

echo -e "\n[STEP 6] Checking build result..."

BUILD_RESULT=$(aws codebuild batch-get-builds \
    --ids "$BUILD_ID" \
    --region "$REGION" \
    --output json)

FINAL_STATUS=$(echo "$BUILD_RESULT" | jq -r '.builds[0].buildStatus')

if [ "$FINAL_STATUS" == "SUCCEEDED" ]; then
    echo "✓ Build SUCCEEDED!"
    
    # Get the image digest
    IMAGE_DIGEST=$(aws ecr describe-images \
        --repository-name "$REPO_NAME" \
        --image-ids "imageTag=$IMAGE_TAG" \
        --region "$REGION" \
        --query 'imageDetails[0].imageDigest' \
        --output text)
    
    IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG"
    FULL_IMAGE_URI="$IMAGE_URI@$IMAGE_DIGEST"
    
    echo -e "\n  ARM64 Image built successfully!"
    echo "  URI: $IMAGE_URI"
    echo "  Digest: $IMAGE_DIGEST"
    
    # ====================================================================
    # STEP 7: Update AgentCore Runtime with new ARM64 image
    # ====================================================================
    
    echo -e "\n[STEP 7] Updating AgentCore Runtime with ARM64 image..."
    
    RUNTIME_ARN="arn:aws:bedrock-agentcore:$REGION:$ACCOUNT_ID:runtime/rfpsupplieragent-ODy0E42s5l"
    
    aws bedrock-agentcore update-resource \
        --resource-arn "$RUNTIME_ARN" \
        --image-uri "$FULL_IMAGE_URI" \
        --region "$REGION"
    
    echo "✓ AgentCore Runtime updated!"
    echo -e "\nDeploy complete. You can now test the agent."
    
else
    echo "❌ Build FAILED with status: $FINAL_STATUS"
    echo -e "\nLogs:"
    aws logs tail "/aws/codebuild/$PROJECT_NAME" --follow --region "$REGION"
    exit 1
fi

echo -e "\n========================================"
echo "✓ ARM64 Build Setup Complete"
echo "========================================"
