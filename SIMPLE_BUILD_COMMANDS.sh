#!/bin/bash
# Simple ARM64 Build Commands for CloudShell
# Run these commands one by one in CloudShell

# Step 1: Create the CodeBuild project using buildspec.yml from GitHub
aws codebuild create-project \
  --name rfp-agent-arm64-build \
  --source type=GITHUB,location=https://github.com/AbilashEEG/rfp-management.git \
  --artifacts type=NO_ARTIFACTS \
  --environment type=ARM_CONTAINER,image=aws/codebuild/amazonlinux2-aarch64-standard:3.0,computeType=BUILD_GENERAL1_LARGE,privilegedMode=true,environmentVariables='[{name=AWS_DEFAULT_REGION,value=us-east-1},{name=AWS_ACCOUNT_ID,value=689050397154},{name=IMAGE_REPO_NAME,value=rfp-agent},{name=IMAGE_TAG,value=orchestrator-agentcore-arm64}]' \
  --service-role arn:aws:iam::689050397154:role/codebuild-rfp-agent-arm64-role \
  --region us-east-1

# Step 2: Start the build
aws codebuild start-build \
  --project-name rfp-agent-arm64-build \
  --region us-east-1

# Step 3: Get the build ID from the output above, then monitor it
# Replace <BUILD_ID> with actual ID from step 2
# aws codebuild batch-get-builds --ids <BUILD_ID> --region us-east-1 --query 'builds[0].{Status:buildStatus,Phase:currentPhase}'

# Step 4: Once build succeeds, update AgentCore Runtime
# aws bedrock-agentcore update-resource \
#   --resource-arn "arn:aws:bedrock-agentcore:us-east-1:689050397154:runtime/rfpsupplieragent-ODy0E42s5l" \
#   --image-uri "689050397154.dkr.ecr.us-east-1.amazonaws.com/rfp-agent:orchestrator-agentcore-arm64" \
#   --region us-east-1
