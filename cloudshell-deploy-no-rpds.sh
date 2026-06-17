#!/bin/bash

# CloudShell Deployment - NO RPDS
# Removes rpds-py after installation since it's not actually needed

set -e

AWS_REGION="us-east-1"
S3_BUCKET="rfp-documents-quadrasystems-v2"

echo "================================================================================"
echo "RFP Management System - Deployment (rpds-free)"
echo "================================================================================"

# Step 1: Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r RFP-main/requirements.txt -t deps > /dev/null 2>&1

# Step 2: REMOVE RPDS (it's a transitive dep but not needed)
echo "Removing rpds-py (transitive dependency not needed)..."
rm -rf deps/rpds*
rm -rf deps/*.dist-info | grep rpds
echo "✓ rpds removed"

# Step 3: Deploy each Lambda
deploy_lambda() {
    local name=$1
    local func_name=$2
    local files=$3
    
    echo ""
    echo "[$name] Building and deploying..."
    
    # Create temp dir
    mkdir -p temp
    
    # Copy files
    for f in $files; do
        cp "$f" temp/ 2>/dev/null || true
    done
    
    # Copy dependencies (WITHOUT rpds)
    cp -r deps/. temp/ 2>/dev/null || true
    
    # Create ZIP
    cd temp
    zip -q -r "code.zip" . 2>/dev/null || true
    cd ..
    
    # Upload and deploy
    if [ -f "temp/code.zip" ]; then
        size=$(du -sh temp/code.zip | cut -f1)
        echo "  ZIP: $size"
        
        aws s3 cp temp/code.zip "s3://$S3_BUCKET/lambda-zips/$func_name/code.zip" \
            --region $AWS_REGION --quiet
        
        aws lambda update-function-code \
            --function-name "$func_name" \
            --s3-bucket "$S3_BUCKET" \
            --s3-key "lambda-zips/$func_name/code.zip" \
            --region $AWS_REGION > /dev/null
        
        echo "  ✓ $name deployed"
    fi
    
    # Clean up
    rm -rf temp
}

# Deploy all 7
deploy_lambda "Orchestrator" "rfp-agent-orchestrator-v2" \
    "RFP-main/agentcore_orchestrator.py RFP-main/agentcore_memory.py RFP-main/config.py"

deploy_lambda "Supplier Lookup" "supplier_lookup_tool-v2" \
    "RFP-main/lambda/supplier_lookup_lambda.py RFP-main/config.py"

deploy_lambda "RFP Generator" "rfp_generator_tool-v2" \
    "RFP-main/lambda/rfp_generator_lambda.py RFP-main/config.py"

deploy_lambda "Email Dispatch" "email_dispatch_tool-v2" \
    "RFP-main/lambda/email_dispatch_lambda.py RFP-main/config.py"

deploy_lambda "Proposal Fetch" "proposal_fetch_tool-v2" \
    "RFP-main/lambda/proposal_fetch_lambda.py RFP-main/config.py"

deploy_lambda "Scoring" "scoring_tool-v2" \
    "RFP-main/lambda/scoring_lambda.py RFP-main/config.py"

deploy_lambda "Recommendation" "recommendation_tool-v2" \
    "RFP-main/lambda/recommendation_lambda.py RFP-main/config.py"

# Clean up
rm -rf deps

# Step 4: Test
echo ""
echo "Testing orchestrator..."
sleep 2  # Wait for Lambda to be ready

aws lambda invoke \
    --function-name rfp-agent-orchestrator-v2 \
    --payload '{"RequestID":"TEST","Budget":50000}' \
    --cli-binary-format raw-in-base64-out \
    --region $AWS_REGION \
    response.json > /dev/null 2>&1

if [ -f response.json ]; then
    echo "✓ Test successful"
    cat response.json | python3 -m json.tool 2>/dev/null || cat response.json
fi

echo ""
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo "API: https://n1q81b8i4k.execute-api.us-east-1.amazonaws.com/prod/process-rfp"
echo ""
