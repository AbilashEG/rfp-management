#!/bin/bash

# Container-based Lambda Deployment Script - RFP Management System
# Deploys using Docker images instead of ZIPs to properly handle rpds-py binary

set -e

echo "================================================================================"
echo "RFP Management System - Container Deployment"
echo "================================================================================"

# Configuration
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
ECR_REPO="rfp-agent"
IMAGE_TAG="latest"
FUNCTION_NAME="rfp-agentcore-orchestrator"

echo ""
echo "AWS Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo "ECR Repository: $ECR_REPO"
echo ""

# ============================================================================
# STEP 1: Create ECR Repository (if it doesn't exist)
# ============================================================================
echo "STEP 1: Creating ECR repository..."
echo "================================================================================"

aws ecr create-repository \
    --repository-name $ECR_REPO \
    --region $REGION 2>/dev/null || echo "✓ Repository already exists"

echo "✓ ECR repository ready"

# ============================================================================
# STEP 2: Login to ECR
# ============================================================================
echo ""
echo "STEP 2: Authenticating with ECR..."
echo "================================================================================"

aws ecr get-login-password --region $REGION | \
    docker login --username AWS \
    --password-stdin \
    $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "✓ Docker authenticated with ECR"

# ============================================================================
# STEP 3: Build Docker Image
# ============================================================================
echo ""
echo "STEP 3: Building Docker image..."
echo "================================================================================"

docker build -t $ECR_REPO:$IMAGE_TAG .

echo "✓ Docker image built successfully"

# ============================================================================
# STEP 4: Tag and Push to ECR
# ============================================================================
echo ""
echo "STEP 4: Pushing image to ECR..."
echo "================================================================================"

ECR_IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"

docker tag $ECR_REPO:$IMAGE_TAG $ECR_IMAGE_URI

docker push $ECR_IMAGE_URI

echo "✓ Image pushed to ECR: $ECR_IMAGE_URI"

# ============================================================================
# STEP 5: Check if Lambda exists and recreate as container type
# ============================================================================
echo ""
echo "STEP 5: Updating Lambda function..."
echo "================================================================================"

# Check if Lambda exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "Lambda function exists. Getting current type..."
    
    # Get current configuration
    CURRENT_TYPE=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.PackageType' --output text)
    
    if [ "$CURRENT_TYPE" = "Zip" ]; then
        echo "Current type: ZIP (must be converted to Image)"
        echo "Deleting existing ZIP-based Lambda..."
        
        aws lambda delete-function \
            --function-name $FUNCTION_NAME \
            --region $REGION
        
        echo "✓ Old Lambda deleted"
        
        # Wait for deletion
        sleep 5
        
        echo "Creating new container-based Lambda..."
        
        aws lambda create-function \
            --function-name $FUNCTION_NAME \
            --package-type Image \
            --code ImageUri=$ECR_IMAGE_URI \
            --role arn:aws:iam::$ACCOUNT_ID:role/rfp-agent-lambda-role \
            --timeout 300 \
            --memory-size 512 \
            --region $REGION
        
        echo "✓ Container-based Lambda created"
    else
        echo "Current type: Container (updating image URI)..."
        
        aws lambda update-function-code \
            --function-name $FUNCTION_NAME \
            --image-uri $ECR_IMAGE_URI \
            --region $REGION
        
        echo "✓ Lambda updated with new image URI"
    fi
else
    echo "Lambda function does not exist. Creating new container-based Lambda..."
    
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --package-type Image \
        --code ImageUri=$ECR_IMAGE_URI \
        --role arn:aws:iam::$ACCOUNT_ID:role/rfp-agent-lambda-role \
        --timeout 300 \
        --memory-size 512 \
        --region $REGION
    
    echo "✓ Container-based Lambda created"
fi

# ============================================================================
# STEP 6: Test Lambda
# ============================================================================
echo ""
echo "STEP 6: Testing Lambda function..."
echo "================================================================================"

echo "Invoking: $FUNCTION_NAME"

aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"body": "{\"message\": \"test\"}"}' \
    --region $REGION \
    response.json

echo ""
echo "Response:"
cat response.json

# Check for errors
if grep -q "errorMessage" response.json; then
    echo ""
    echo "❌ ERROR DETECTED in response:"
    grep "errorMessage" response.json
    echo ""
    echo "Check CloudWatch logs:"
    echo "  aws logs tail /aws/lambda/$FUNCTION_NAME --follow --region $REGION"
    exit 1
else
    echo ""
    echo "✓ Test successful - no errors in response"
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  ✓ ECR repository created/verified"
echo "  ✓ Docker image built and pushed to ECR"
echo "  ✓ Lambda function deployed as container type"
echo "  ✓ Lambda tested successfully"
echo ""
echo "Lambda Details:"
echo "  Function: $FUNCTION_NAME"
echo "  Type: Container"
echo "  Image URI: $ECR_IMAGE_URI"
echo "  Region: $REGION"
echo ""

