#!/bin/bash
# API Gateway Setup for RFP Agent Orchestrator
# Creates HTTP API endpoint with Lambda integration

set -e

REGION=${1:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
API_NAME="rfp-agent-api"
LAMBDA_FUNCTION="rfp-agentcore-orchestrator"

echo "=========================================="
echo "API Gateway Setup"
echo "=========================================="
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo "Function: $LAMBDA_FUNCTION"
echo ""

# Step 1: Create REST API
echo "Step 1: Creating REST API..."
API_RESPONSE=$(aws apigateway create-rest-api \
    --name $API_NAME \
    --description "RFP Agent Orchestrator API" \
    --region $REGION 2>/dev/null || \
aws apigateway get-rest-apis \
    --region $REGION \
    --query "items[?name=='$API_NAME']" \
    --output json)

API_ID=$(echo $API_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -z "$API_ID" ]; then
    API_ID=$(aws apigateway get-rest-apis \
        --region $REGION \
        --query "items[?name=='$API_NAME'].id" \
        --output text)
fi

echo "✓ API Gateway ID: $API_ID"
echo ""

# Step 2: Get Root Resource
echo "Step 2: Getting root resource..."
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $REGION \
    --query "items[?path=='/'].id" \
    --output text)

echo "✓ Root Resource ID: $ROOT_RESOURCE_ID"
echo ""

# Step 3: Create /process-rfp Resource
echo "Step 3: Creating /process-rfp resource..."
RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_RESOURCE_ID \
    --path-part process-rfp \
    --region $REGION \
    --query 'id' \
    --output text 2>/dev/null || \
aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $REGION \
    --query "items[?path=='/process-rfp'].id" \
    --output text)

echo "✓ Resource ID: $RESOURCE_ID"
echo ""

# Step 4: Create POST Method
echo "Step 4: Creating POST method..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --authorization-type NONE \
    --region $REGION > /dev/null 2>&1

echo "✓ POST method created"
echo ""

# Step 5: Create Method Response
echo "Step 5: Creating method response..."
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --status-code 200 \
    --region $REGION > /dev/null 2>&1

echo "✓ Method response configured"
echo ""

# Step 6: Create Integration
echo "Step 6: Creating Lambda integration..."
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_FUNCTION}/invocations" \
    --region $REGION > /dev/null 2>&1

echo "✓ Lambda integration created"
echo ""

# Step 7: Create Integration Response
echo "Step 7: Creating integration response..."
aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --status-code 200 \
    --region $REGION > /dev/null 2>&1

echo "✓ Integration response configured"
echo ""

# Step 8: Grant API Gateway Permission
echo "Step 8: Granting API Gateway invoke permission..."
aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION \
    --statement-id ApiGatewayInvoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/*" \
    --region $REGION 2>/dev/null || echo "✓ Permission already exists"

echo "✓ Lambda invoke permission granted"
echo ""

# Step 9: Deploy API
echo "Step 9: Deploying API..."
DEPLOYMENT_ID=$(aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $REGION \
    --query 'id' \
    --output text 2>/dev/null || echo "exists")

echo "✓ API deployed"
echo ""

# Step 10: Get Endpoint
echo "=========================================="
echo "✅ API GATEWAY SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Endpoint: https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/process-rfp"
echo ""
echo "Test Command:"
echo "curl -X POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/process-rfp \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"body\": \"{\\\"message\\\": \\\"Create RFP for sensors\\\"}\"}'"
echo ""
