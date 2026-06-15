# config.py
REGION = "us-east-1"
BEDROCK_MODEL_ID = "amazon.nova-pro-v1:0"

# DynamoDB
SUPPLIERS_TABLE = "rfp-suppliers"
REQUESTS_TABLE  = "rfp-requests"
PROPOSALS_TABLE = "rfp-proposals"
SCORES_TABLE    = "rfp-scores"

# S3
RFP_DOCS_BUCKET = "rfp-documents-quadrasystems"
RFP_DOCS_PREFIX = "rfp-docs/"

# SES
SES_SENDER_EMAIL = "rfp-agent@quadrasystems.com"
SES_MOCK_MODE    = True  # Set False when SES identity is verified

# Cognito
COGNITO_USER_POOL_ID  = "us-east-1_2oMHgTNMY"
COGNITO_APP_CLIENT_ID = "52ca8g1uj400486dhokooeful7"

# ECR / Lambda
AWS_ACCOUNT_ID  = "689050397154"
ECR_URI         = "689050397154.dkr.ecr.us-east-1.amazonaws.com/supplier-rfp-agent"
LAMBDA_ROLE_ARN = "arn:aws:iam::689050397154:role/rfp-agent-lambda-role"

# AgentCore  — fill after AgentCore Memory + Runtime are created
AGENTCORE_MEMORY_ID = ""   # e.g. "mem-xxxxxxxxxxxxxxxx"
AGENTCORE_AGENT_ID  = ""   # e.g. "agent-xxxxxxxxxxxxxxxx"

# Scoring Weights
PRICE_WEIGHT      = 0.30
QUALITY_WEIGHT    = 0.30
DELIVERY_WEIGHT   = 0.20
COMPLIANCE_WEIGHT = 0.20
