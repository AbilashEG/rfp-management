name: rfp-supplier-agent

runtime:
  framework: strands
  model: amazon.nova-pro-v1:0
  region: us-east-1
  entry_point: agentcore_orchestrator.handler

performance:
  memory_size: 512
  timeout: 300
  ephemeral_storage: 10240

memory:
  enabled: true
  table_name: agentcore-memory-v2
  ttl_days: 30
  persistence:
    strategy: dynamodb
    auto_cleanup: true

identity:
  provider: cognito
  enabled: true
  user_pool_id: us-east-1_XXXXXXXXX  # Will be replaced during deploy
  client_id: auto
  token_validation: true

observability:
  enabled: true
  tracing: xray
  log_group: /agentcore/rfp-supplier-agent
  log_retention_days: 30
  metrics:
    namespace: RFPAgent
    enabled: true

policy:
  human_approval:
    enabled: true
    trigger_field: approval_required
    trigger_value: true
    approval_sqs_queue: rfp-approval-queue

gateway:
  mcp:
    enabled: true
    tools:
      - name: supplier_lookup_tool
        source: RFP-main/lambda/supplier_lookup_lambda.py
        handler: handler
        description: "Find qualified suppliers by category"
        
      - name: rfp_generator_tool
        source: RFP-main/lambda/rfp_generator_lambda.py
        handler: handler
        description: "Generate RFP document and store in S3"
        
      - name: email_dispatch_tool
        source: RFP-main/lambda/email_dispatch_lambda.py
        handler: handler
        description: "Send RFP emails to suppliers"
        
      - name: proposal_fetch_tool
        source: RFP-main/lambda/proposal_fetch_lambda.py
        handler: handler
        description: "Fetch supplier proposals"
        
      - name: scoring_tool
        source: RFP-main/lambda/scoring_lambda.py
        handler: handler
        description: "Score proposals with weighted criteria"
        
      - name: recommendation_tool
        source: RFP-main/lambda/recommendation_lambda.py
        handler: handler
        description: "Generate supplier recommendations"

environment:
  REGION: us-east-1
  LOG_LEVEL: INFO
  MODEL_ID: amazon.nova-pro-v1:0
  AGENT_NAME: rfp-supplier-agent

tags:
  Environment: production
  Team: rfp-management
  Application: rfp-agent
