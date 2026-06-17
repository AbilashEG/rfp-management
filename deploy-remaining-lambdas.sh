#!/bin/bash

# Deploy Only the 4 Remaining Tool Lambdas
# (Assumes orchestrator + supplier_lookup + rfp_generator already deployed)

set -e

echo "================================================================================"
echo "RFP Management System - Deploy Remaining 4 Tool Lambdas"
echo "================================================================================"

# Configuration
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
ECR_REPO="rfp-agent"
IMAGE_TAG="latest"

echo ""
echo "AWS Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo "ECR Repository: $ECR_REPO"
echo ""

# ============================================================================
# STEP 1: Authenticate with ECR
# ============================================================================
echo "STEP 1: Authenticating with ECR..."
echo "================================================================================"

aws ecr get-login-password --region $REGION | \
    docker login --username AWS \
    --password-stdin \
    $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "✓ Docker authenticated with ECR"

# ============================================================================
# STEP 2: Deploy Remaining 4 Tool Lambdas
# ============================================================================

# Array of remaining Lambdas to deploy
declare -a REMAINING_LAMBDAS=(
    "scoring|rfp-scoring"
    "email_dispatch|rfp-email-dispatch"
    "proposal_fetch|rfp-proposal-fetch"
    "recommendation|rfp-recommendation"
)

for lambda_info in "${REMAINING_LAMBDAS[@]}"; do
    IFS='|' read -r docker_tag function_name <<< "$lambda_info"
    
    echo ""
    echo "================================================================================"
    echo "Deploying: $function_name"
    echo "================================================================================"
    
    # Step 1: Build Docker Image
    echo ""
    echo "Step 1: Building Docker image..."
    docker build -f ./RFP-main/lambda/${docker_tag}_lambda.Dockerfile -t $ECR_REPO:$docker_tag .
    echo "✓ Docker image built"
    
    # Step 2: Tag for ECR
    echo ""
    echo "Step 2: Tagging for ECR..."
    ECR_IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$docker_tag"
    docker tag $ECR_REPO:$docker_tag $ECR_IMAGE_URI
    echo "✓ Image tagged: $ECR_IMAGE_URI"
    
    # Step 3: Push to ECR
    echo ""
    echo "Step 3: Pushing to ECR..."
    docker push $ECR_IMAGE_URI
    echo "✓ Image pushed to ECR"
    
    # Step 4: Create or Update Lambda
    echo ""
    echo "Step 4: Creating/Updating Lambda function..."
    
    if aws lambda get-function --function-name "$function_name" --region $REGION 2>/dev/null; then
        echo "Lambda exists. Updating image URI..."
        
        aws lambda update-function-code \
            --function-name "$function_name" \
            --image-uri "$ECR_IMAGE_URI" \
            --region $REGION > /dev/null
        
        echo "✓ Lambda updated with new image"
    else
        echo "Lambda does not exist. Creating new container-based Lambda..."
        
        aws lambda create-function \
            --function-name "$function_name" \
            --package-type Image \
            --code ImageUri="$ECR_IMAGE_URI" \
            --role "arn:aws:iam::$ACCOUNT_ID:role/rfp-agent-lambda-role" \
            --timeout 300 \
            --memory-size 512 \
            --region $REGION > /dev/null
        
        echo "✓ Container-based Lambda created"
    fi
    
    # Wait for Lambda to be ready
    echo "Waiting for Lambda to be ready..."
    sleep 3
    
    # Verify Lambda is Active
    LAMBDA_STATE=$(aws lambda get-function --function-name "$function_name" --region $REGION --query 'Configuration.State' --output text 2>/dev/null)
    
    if [ "$LAMBDA_STATE" = "Active" ]; then
        echo "✓ Lambda is Active and ready"
    else
        echo "⚠️  Lambda state: $LAMBDA_STATE (may still be initializing)"
    fi
done

# ============================================================================
# FINAL VERIFICATION
# ============================================================================
echo ""
echo "================================================================================"
echo "✅ REMAINING LAMBDAS DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  ✓ 4 Tool Lambdas deployed as container types"
echo "  ✓ All images pushed to ECR"
echo ""
echo "All Deployed Lambdas (should be 7 total):"
aws lambda list-functions --region $REGION \
  --query 'Functions[?contains(FunctionName, `rfp-`)].{Name:FunctionName,Type:PackageType,State:State}' \
  --output table
echo ""
echo "Images in ECR:"
aws ecr describe-images --repository-name $ECR_REPO --region $REGION \
  --query 'imageDetails[].{Tag:imageTags[0],Size:imageSizeInBytes}' \
  --output table
echo ""
