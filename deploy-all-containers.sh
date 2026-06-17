#!/bin/bash

# Complete Container Deployment for All 7 Lambda Functions
# Orchestrator + 6 Tool Lambdas
# Deploys using Docker images instead of ZIPs to properly handle rpds-py binary

set -e

echo "================================================================================"
echo "RFP Management System - Complete Container Deployment (All 7 Lambdas)"
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

# Define all 7 Lambdas
declare -A LAMBDAS=(
    [orchestrator]="rfp-agentcore-orchestrator|./Dockerfile|agentcore_orchestrator.handler"
    [supplier_lookup]="rfp-supplier-lookup|./RFP-main/lambda/supplier_lookup_lambda.Dockerfile|supplier_lookup_lambda.handler"
    [rfp_generator]="rfp-rfp-generator|./RFP-main/lambda/rfp_generator_lambda.Dockerfile|rfp_generator_lambda.handler"
    [email_dispatch]="rfp-email-dispatch|./RFP-main/lambda/email_dispatch_lambda.Dockerfile|email_dispatch_lambda.handler"
    [proposal_fetch]="rfp-proposal-fetch|./RFP-main/lambda/proposal_fetch_lambda.Dockerfile|proposal_fetch_lambda.handler"
    [scoring]="rfp-scoring|./RFP-main/lambda/scoring_lambda.Dockerfile|scoring_lambda.handler"
    [recommendation]="rfp-recommendation|./RFP-main/lambda/recommendation_lambda.Dockerfile|recommendation_lambda.handler"
)

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
# STEP 3: Build, Push, and Deploy Each Lambda
# ============================================================================

for lambda_key in "${!LAMBDAS[@]}"; do
    IFS='|' read -r FUNCTION_NAME DOCKERFILE_PATH HANDLER <<< "${LAMBDAS[$lambda_key]}"
    
    ECR_IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$lambda_key"
    
    echo ""
    echo "================================================================================"
    echo "Processing: $FUNCTION_NAME"
    echo "================================================================================"
    
    # Check if Dockerfile exists
    if [ ! -f "$DOCKERFILE_PATH" ]; then
        echo "❌ ERROR: Dockerfile not found at $DOCKERFILE_PATH"
        exit 1
    fi
    
    # Build Docker Image
    echo ""
    echo "Step 3a: Building Docker image..."
    docker build -f "$DOCKERFILE_PATH" -t "$ECR_REPO:$lambda_key" .
    echo "✓ Docker image built"
    
    # Tag for ECR
    echo ""
    echo "Step 3b: Tagging for ECR..."
    docker tag "$ECR_REPO:$lambda_key" "$ECR_IMAGE_URI"
    echo "✓ Image tagged: $ECR_IMAGE_URI"
    
    # Push to ECR
    echo ""
    echo "Step 3c: Pushing to ECR..."
    docker push "$ECR_IMAGE_URI"
    echo "✓ Image pushed to ECR"
    
    # Update or Create Lambda
    echo ""
    echo "Step 3d: Updating Lambda function..."
    
    if aws lambda get-function --function-name "$FUNCTION_NAME" --region $REGION 2>/dev/null; then
        echo "Lambda exists. Checking package type..."
        
        CURRENT_TYPE=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region $REGION --query 'Configuration.PackageType' --output text)
        
        if [ "$CURRENT_TYPE" = "Zip" ]; then
            echo "Current type: ZIP (converting to Image)"
            
            # Delete old ZIP-based Lambda
            aws lambda delete-function \
                --function-name "$FUNCTION_NAME" \
                --region $REGION
            
            echo "✓ Old ZIP Lambda deleted, waiting for completion..."
            sleep 3
            
            # Create new container-based Lambda
            aws lambda create-function \
                --function-name "$FUNCTION_NAME" \
                --package-type Image \
                --code ImageUri="$ECR_IMAGE_URI" \
                --role "arn:aws:iam::$ACCOUNT_ID:role/rfp-agent-lambda-role" \
                --timeout 300 \
                --memory-size 512 \
                --region $REGION
            
            echo "✓ Container-based Lambda created"
        else
            echo "Current type: Container (updating image URI)"
            
            aws lambda update-function-code \
                --function-name "$FUNCTION_NAME" \
                --image-uri "$ECR_IMAGE_URI" \
                --region $REGION > /dev/null
            
            echo "✓ Lambda updated with new image"
        fi
    else
        echo "Lambda does not exist. Creating new container-based Lambda..."
        
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --package-type Image \
            --code ImageUri="$ECR_IMAGE_URI" \
            --role "arn:aws:iam::$ACCOUNT_ID:role/rfp-agent-lambda-role" \
            --timeout 300 \
            --memory-size 512 \
            --region $REGION
        
        echo "✓ Container-based Lambda created"
    fi
    
    # Wait for Lambda to be ready
    echo "Waiting for Lambda to be ready..."
    sleep 3
    
    # Verify Lambda is Active
    LAMBDA_STATE=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region $REGION --query 'Configuration.State' --output text 2>/dev/null)
    
    if [ "$LAMBDA_STATE" = "Active" ]; then
        echo "✓ Lambda is Active and ready"
    else
        echo "⚠️  Lambda state: $LAMBDA_STATE (may still be initializing)"
    fi
done

# ============================================================================
# FINAL SUMMARY
# ============================================================================
echo ""
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo ""
echo "Summary of Deployed Lambdas:"
echo "  1. rfp-agentcore-orchestrator (Orchestrator)"
echo "  2. rfp-supplier-lookup (Tool)"
echo "  3. rfp-rfp-generator (Tool)"
echo "  4. rfp-email-dispatch (Tool)"
echo "  5. rfp-proposal-fetch (Tool)"
echo "  6. rfp-scoring (Tool)"
echo "  7. rfp-recommendation (Tool)"
echo ""
echo "Deployment Details:"
echo "  Region: $REGION"
echo "  ECR Repository: $ECR_REPO"
echo "  Package Type: Container"
echo "  Memory: 512 MB"
echo "  Timeout: 300 seconds"
echo ""
echo "Next Steps:"
echo "  1. Test orchestrator end-to-end: aws lambda invoke --function-name rfp-agentcore-orchestrator --payload '{\"RequestID\":\"RFP-001\"}' --region $REGION response.json"
echo "  2. Check logs: aws logs tail /aws/lambda/rfp-agentcore-orchestrator --follow --region $REGION"
echo "  3. Push code to GitHub: git add . && git commit -m 'Deploy all 7 Lambdas as container images' && git push"
echo ""

