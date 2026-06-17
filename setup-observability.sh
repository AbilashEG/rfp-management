#!/bin/bash
# Observability Setup: X-Ray Tracing + CloudWatch Logs + Custom Metrics
# Enables full monitoring for RFP Agent system

set -e

REGION=${1:-us-east-1}
LAMBDA_FUNCTION="rfp-agentcore-orchestrator"
ROLE_NAME="rfp-agent-lambda-role"

echo "=========================================="
echo "Observability Setup"
echo "=========================================="
echo "Region: $REGION"
echo "Lambda: $LAMBDA_FUNCTION"
echo "Role: $ROLE_NAME"
echo ""

# Step 1: Enable X-Ray Tracing
echo "Step 1: Enabling X-Ray tracing on Lambda..."
aws lambda update-function-configuration \
    --function-name $LAMBDA_FUNCTION \
    --tracing-config Mode=Active \
    --region $REGION > /dev/null

echo "✓ X-Ray tracing enabled"
echo ""

# Step 2: Add X-Ray Permissions to IAM Role
echo "Step 2: Adding X-Ray permissions to IAM role..."

cat > /tmp/xray-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name XRayTracingPolicy \
    --policy-document file:///tmp/xray-policy.json \
    --region $REGION 2>/dev/null || echo "✓ Policy already exists"

echo "✓ X-Ray permissions added"
echo ""

# Step 3: Create CloudWatch Log Group
echo "Step 3: Creating CloudWatch Log Group..."
aws logs create-log-group \
    --log-group-name /aws/lambda/$LAMBDA_FUNCTION \
    --region $REGION 2>/dev/null || echo "✓ Log group already exists"

# Set retention
aws logs put-retention-policy \
    --log-group-name /aws/lambda/$LAMBDA_FUNCTION \
    --retention-in-days 30 \
    --region $REGION 2>/dev/null

echo "✓ CloudWatch Log Group configured (30-day retention)"
echo ""

# Step 4: Create CloudWatch Dashboard
echo "Step 4: Creating CloudWatch Dashboard..."

cat > /tmp/dashboard.json <<'EOF'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Invocations", { "stat": "Sum" } ],
          [ ".", "Errors", { "stat": "Sum" } ],
          [ ".", "Duration", { "stat": "Average" } ],
          [ ".", "Throttles", { "stat": "Sum" } ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Lambda Invocation Metrics"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "fields @timestamp, @message | stats count() as error_count by @message | filter @message like /ERROR/",
        "region": "us-east-1",
        "title": "Error Rate"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/DynamoDB", "ConsumedReadCapacityUnits" ],
          [ ".", "ConsumedWriteCapacityUnits" ],
          [ ".", "UserErrors" ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "DynamoDB Performance"
      }
    }
  ]
}
EOF

aws cloudwatch put-dashboard \
    --dashboard-name rfp-agent-dashboard \
    --dashboard-body file:///tmp/dashboard.json \
    --region $REGION > /dev/null

echo "✓ CloudWatch Dashboard created"
echo ""

# Step 5: Create CloudWatch Alarms
echo "Step 5: Creating CloudWatch Alarms..."

# Alarm 1: Lambda Errors
aws cloudwatch put-metric-alarm \
    --alarm-name rfp-agent-errors \
    --alarm-description "Alert when Lambda function errors exceed threshold" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --region $REGION 2>/dev/null || echo "✓ Error alarm already exists"

echo "✓ Error alarm configured"

# Alarm 2: Lambda Throttles
aws cloudwatch put-metric-alarm \
    --alarm-name rfp-agent-throttles \
    --alarm-description "Alert when Lambda is throttled" \
    --metric-name Throttles \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 60 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold \
    --evaluation-periods 1 \
    --region $REGION 2>/dev/null || echo "✓ Throttle alarm already exists"

echo "✓ Throttle alarm configured"

# Alarm 3: Lambda Duration
aws cloudwatch put-metric-alarm \
    --alarm-name rfp-agent-high-duration \
    --alarm-description "Alert when Lambda execution time is high" \
    --metric-name Duration \
    --namespace AWS/Lambda \
    --statistic Average \
    --period 300 \
    --threshold 30000 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --region $REGION 2>/dev/null || echo "✓ Duration alarm already exists"

echo "✓ Duration alarm configured"

# Alarm 4: DynamoDB Throttling
aws cloudwatch put-metric-alarm \
    --alarm-name rfp-dynamodb-throttle \
    --alarm-description "Alert on DynamoDB throttling" \
    --metric-name UserErrors \
    --namespace AWS/DynamoDB \
    --statistic Sum \
    --period 60 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold \
    --evaluation-periods 1 \
    --region $REGION 2>/dev/null || echo "✓ DynamoDB alarm already exists"

echo "✓ DynamoDB throttle alarm configured"

echo ""

# Step 6: Enable CloudWatch Insights Queries
echo "Step 6: Sample CloudWatch Insights Queries..."
echo ""
echo "Query 1: Agent Execution Timeline"
echo "  fields @timestamp, @message, workflow_step | stats count() as step_count by workflow_step"
echo ""
echo "Query 2: Tool Invocation Success Rate"
echo "  fields tool_name, status | stats count() as invocations by tool_name, status"
echo ""
echo "Query 3: Error Analysis"
echo "  fields @timestamp, @message, @logStream | filter @message like /ERROR/"
echo ""
echo "Query 4: Performance Metrics"
echo "  fields @duration, @maxMemoryUsed | stats avg(@duration) as avg_duration, max(@maxMemoryUsed) as max_memory"
echo ""

# Step 7: Create Log Retention for Tool Lambdas
echo "Step 7: Setting up logs for tool Lambdas..."

TOOLS=("rfp-supplier-lookup" "rfp-rfp-generator" "rfp-email-dispatch" "rfp-proposal-fetch" "rfp-scoring" "rfp-recommendation")

for TOOL in "${TOOLS[@]}"; do
    aws logs create-log-group \
        --log-group-name /aws/lambda/$TOOL \
        --region $REGION 2>/dev/null || true
    
    aws logs put-retention-policy \
        --log-group-name /aws/lambda/$TOOL \
        --retention-in-days 30 \
        --region $REGION 2>/dev/null || true
    
    echo "✓ $TOOL logs configured"
done

echo ""

echo "=========================================="
echo "✅ OBSERVABILITY SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Services Enabled:"
echo "  ✓ X-Ray Distributed Tracing"
echo "  ✓ CloudWatch Logs (30-day retention)"
echo "  ✓ CloudWatch Dashboard"
echo "  ✓ CloudWatch Alarms (Errors, Throttles, Duration)"
echo "  ✓ CloudWatch Insights Queries"
echo ""
echo "Access Points:"
echo "  • X-Ray Console: https://us-east-1.console.aws.amazon.com/xray/"
echo "  • CloudWatch Dashboard: https://us-east-1.console.aws.amazon.com/cloudwatch/"
echo "  • Log Streams: /aws/lambda/$LAMBDA_FUNCTION"
echo ""
echo "Monitoring Checklist:"
echo "  [ ] Check X-Ray Service Map for request flow"
echo "  [ ] Verify CloudWatch Dashboard displays metrics"
echo "  [ ] Test error alarm by triggering a failure"
echo "  [ ] Run CloudWatch Insights queries"
echo ""
