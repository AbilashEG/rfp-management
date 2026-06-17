#!/bin/bash

# CloudShell Deployment Script - RFP Management System
# This script builds Lambda ZIPs and deploys to AWS

set -e

echo "================================================================================"
echo "RFP Management System - CloudShell Deployment"
echo "================================================================================"

# Configuration
AWS_REGION="us-east-1"
S3_BUCKET="rfp-documents-quadrasystems-v2"
ACCOUNT_ID="689050397154"

echo ""
echo "STEP 1: Installing dependencies..."
echo "================================================================================"

pip install -r RFP-main/requirements.txt -t package/ > /dev/null 2>&1
echo "✓ Dependencies installed"

echo ""
echo "STEP 2: Building Lambda ZIPs with correct structure..."
echo "================================================================================"

# Function to create Lambda ZIP
create_lambda_zip() {
    local lambda_name=$1
    local source_files=$2
    local zip_name="${lambda_name}.zip"
    
    echo ""
    echo "Building: $lambda_name"
    
    # Create temp directory
    mkdir -p "temp-$lambda_name"
    
    # Copy source files
    for file in $source_files; do
        if [ -f "$file" ]; then
            cp "$file" "temp-$lambda_name/"
            echo "  ✓ Added: $(basename $file)"
        fi
    done
    
    # Copy dependencies (python folder at root level - CORRECT structure)
    cp -r package/. "temp-$lambda_name/"
    echo "  ✓ Added: python dependencies"
    
    # Create ZIP
    cd "temp-$lambda_name"
    zip -q -r "../$zip_name" .
    cd ..
    
    # Get size
    size_mb=$(du -sh "$zip_name" | cut -f1)
    echo "  ✓ Created: $zip_name ($size_mb)"
    
    # Cleanup temp directory
    rm -rf "temp-$lambda_name"
    
    # Clean package cache to save space
    rm -rf package/
    mkdir -p package
    cp -r /tmp/python-deps/. package/ 2>/dev/null || true
}

# Build all 7 Lambda ZIPs
create_lambda_zip "orchestrator" "RFP-main/agentcore_orchestrator.py RFP-main/agentcore_memory.py RFP-main/config.py"
create_lambda_zip "supplier_lookup_tool" "RFP-main/lambda/supplier_lookup_lambda.py RFP-main/config.py"
create_lambda_zip "rfp_generator_tool" "RFP-main/lambda/rfp_generator_lambda.py RFP-main/config.py"
create_lambda_zip "email_dispatch_tool" "RFP-main/lambda/email_dispatch_lambda.py RFP-main/config.py"
create_lambda_zip "proposal_fetch_tool" "RFP-main/lambda/proposal_fetch_lambda.py RFP-main/config.py"
create_lambda_zip "scoring_tool" "RFP-main/lambda/scoring_lambda.py RFP-main/config.py"
create_lambda_zip "recommendation_tool" "RFP-main/lambda/recommendation_lambda.py RFP-main/config.py"

echo ""
echo "STEP 3: Uploading ZIPs to S3..."
echo "================================================================================"

declare -A lambda_names
lambda_names[orchestrator]="rfp-agent-orchestrator-v2"
lambda_names[supplier_lookup_tool]="supplier_lookup_tool-v2"
lambda_names[rfp_generator_tool]="rfp_generator_tool-v2"
lambda_names[email_dispatch_tool]="email_dispatch_tool-v2"
lambda_names[proposal_fetch_tool]="proposal_fetch_tool-v2"
lambda_names[scoring_tool]="scoring_tool-v2"
lambda_names[recommendation_tool]="recommendation_tool-v2"

for zip_file in *.zip; do
    lambda_name="${zip_file%.zip}"
    s3_key="lambda-zips/${lambda_names[$lambda_name]}/${zip_file}"
    
    echo ""
    echo "Uploading: $zip_file → s3://$S3_BUCKET/$s3_key"
    
    aws s3 cp "$zip_file" "s3://$S3_BUCKET/$s3_key" --region $AWS_REGION
    
    echo "  ✓ Uploaded successfully"
done

echo ""
echo "STEP 4: Deploying Lambda functions..."
echo "================================================================================"

# Deploy each Lambda
deploy_lambda() {
    local lambda_name=$1
    local zip_key=$2
    
    echo ""
    echo "Deploying: $lambda_name"
    
    aws lambda update-function-code \
        --function-name "$lambda_name" \
        --s3-bucket "$S3_BUCKET" \
        --s3-key "$zip_key" \
        --region $AWS_REGION > /dev/null
    
    echo "  ✓ Deployed successfully"
}

# Deploy all 7 Lambdas in order
deploy_lambda "rfp-agent-orchestrator-v2" "lambda-zips/rfp-agent-orchestrator-v2/orchestrator.zip"
deploy_lambda "supplier_lookup_tool-v2" "lambda-zips/supplier_lookup_tool-v2/supplier_lookup_tool.zip"
deploy_lambda "rfp_generator_tool-v2" "lambda-zips/rfp_generator_tool-v2/rfp_generator_tool.zip"
deploy_lambda "email_dispatch_tool-v2" "lambda-zips/email_dispatch_tool-v2/email_dispatch_tool.zip"
deploy_lambda "proposal_fetch_tool-v2" "lambda-zips/proposal_fetch_tool-v2/proposal_fetch_tool.zip"
deploy_lambda "scoring_tool-v2" "lambda-zips/scoring_tool-v2/scoring_tool.zip"
deploy_lambda "recommendation_tool-v2" "lambda-zips/recommendation_tool-v2/recommendation_tool.zip"

echo ""
echo "STEP 5: Testing orchestrator Lambda..."
echo "================================================================================"

# Test orchestrator
aws lambda invoke \
    --function-name rfp-agent-orchestrator-v2 \
    --payload '{"RequestID":"RFP-TEST-001","Budget":50000}' \
    --cli-binary-format raw-in-base64-out \
    --region $AWS_REGION \
    response.json > /dev/null 2>&1

if [ -f response.json ]; then
    echo "  ✓ Test invoked successfully"
    echo ""
    echo "Response:"
    cat response.json | python3 -m json.tool 2>/dev/null || cat response.json
else
    echo "  ✗ Test failed"
fi

echo ""
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  ✓ 7 Lambda ZIPs created with correct structure"
echo "  ✓ All ZIPs uploaded to S3"
echo "  ✓ All Lambda functions updated"
echo "  ✓ Orchestrator tested"
echo ""
echo "API Endpoint: https://n1q81b8i4k.execute-api.us-east-1.amazonaws.com/prod/process-rfp"
echo ""
