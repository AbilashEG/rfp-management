# RFP Management System - AWS Lambda Agent

Production-ready AWS Lambda-based RFP (Request for Proposal) management system using Amazon Nova Pro with Strands Agents SDK.

## Architecture

**Multi-Lambda Design:**
- **Orchestrator Lambda** - Main coordinator using Strands Agents framework
- **7 Tool Lambdas** - Independent specialized handlers:
  - `supplier_lookup_tool` - Supplier database lookup
  - `rfp_generator_tool` - RFP document generation
  - `email_dispatch_tool` - Email notifications
  - `proposal_fetch_tool` - Fetch proposals
  - `scoring_tool` - Proposal scoring with risk analysis
  - `recommendation_tool` - Top 2 supplier recommendations

## Deployment

### Prerequisites
- AWS Account with appropriate IAM permissions
- CloudShell access
- Python 3.12 or higher

### Quick Start

1. **Clone repository**
   ```bash
   git clone https://github.com/AbilashEG/rfp-management.git
   cd rfp-management
   ```

2. **In CloudShell:**
   ```bash
   # Download from GitHub
   wget https://github.com/AbilashEG/rfp-management/archive/main.zip
   unzip main.zip
   cd rfp-management-main

   # Deploy infrastructure
   aws cloudformation create-stack \
     --stack-name rfp-production-stack \
     --template-body file://RFP-main/cloudformation-deployment.yaml \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-east-1
   
   # Wait for stack creation
   aws cloudformation wait stack-create-complete \
     --stack-name rfp-production-stack \
     --region us-east-1
   ```

3. **Create Lambda functions from ZIP**
   ```bash
   # Install dependencies
   pip install -r RFP-main/requirements.txt -t package/

   # Build ZIPs for each Lambda
   cd RFP-main
   
   # Orchestrator ZIP
   cp agentcore_orchestrator.py agentcore_memory.py config.py ../package/
   cd ../package && zip -r orchestrator.zip . && cd ..
   
   # Tool ZIPs (similar process for each tool)
   # ... repeat for each tool Lambda
   ```

## Configuration

### Environment Variables (Lambda)
- `REGION` - AWS region (default: us-east-1)
- `MODEL` - LLM model (default: amazon.nova-pro-v1:0)
- `DYNAMODB_REGION` - DynamoDB region

### Database
- **DynamoDB Tables**: rfp-metadata, proposals, scores, suppliers, recommendations
- **S3 Bucket**: rfp-documents-quadrasystems-v2

## Project Structure

```
RFP-main/
├── agentcore_orchestrator.py     # Main orchestrator Lambda
├── agentcore_memory.py           # Conversation memory management
├── config.py                     # Configuration
├── requirements.txt              # Python dependencies
├── cloudformation-deployment.yaml # Infrastructure as Code
├── lambda/
│   ├── supplier_lookup_lambda.py
│   ├── rfp_generator_lambda.py
│   ├── email_dispatch_lambda.py
│   ├── proposal_fetch_lambda.py
│   ├── scoring_lambda.py
│   └── recommendation_lambda.py
└── setup/
    └── (optional setup scripts)
```

## Technology Stack

- **Compute**: AWS Lambda (Python 3.12)
- **AI Model**: Amazon Nova Pro v1
- **Framework**: Strands Agents SDK 0.2.0
- **Database**: AWS DynamoDB
- **Storage**: Amazon S3
- **Infrastructure**: AWS CloudFormation

## Key Features

✅ Multi-Lambda architecture for scalability
✅ Strands Agents for intelligent orchestration
✅ Risk flagging and scoring system
✅ Automated email notifications
✅ Supplier recommendation engine
✅ DynamoDB persistence
✅ Zero pydantic dependency (pure dict-based)

## Notes

- All Lambda functions use dict-based responses (no Pydantic)
- Strands Agents framework handles all AI/LLM orchestration
- CloudFormation stack creates all required infrastructure
- IAM role included for Lambda→DynamoDB/S3 access

---

For deployment details, see CloudShell instructions in Quick Start.
