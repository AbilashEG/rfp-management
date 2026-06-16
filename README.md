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

### Quick Start - CloudShell (5 minutes)

1. **Open AWS CloudShell** and download repository:
   ```bash
   wget https://github.com/AbilashEG/rfp-management/archive/main.zip
   unzip main.zip
   cd rfp-management-main
   ```

2. **Run automated deployment script**:
   ```bash
   bash cloudshell-deploy.sh
   ```

   This script automatically:
   - ✓ Installs Python dependencies
   - ✓ Builds 7 Lambda ZIPs with correct structure (dependencies at root)
   - ✓ Uploads all ZIPs to S3
   - ✓ Deploys code to all 7 Lambda functions
   - ✓ Tests orchestrator Lambda
   - ✓ Displays results and API endpoint

3. **Verify deployment**:
   ```bash
   # Check logs
   aws logs tail /aws/lambda/rfp-agent-orchestrator-v2 --follow --region us-east-1
   ```

**See [CLOUDSHELL_DEPLOYMENT.md](CLOUDSHELL_DEPLOYMENT.md) for detailed guide and troubleshooting.**

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
