# RFP Management Agent

Complete RFP (Request for Proposal) management system powered by AWS Lambda, DynamoDB, and S3.

## Features

- **6 Integrated Tools**: Supplier lookup, RFP generation, email dispatch, proposal fetch, scoring, recommendations
- **Lambda**: Docker container (Python 3.12)
- **DynamoDB**: 4 tables (suppliers, requests, proposals, scores)
- **S3**: Document storage
- **API Gateway**: REST endpoint

## Deployment

Push to `main` branch triggers automatic GitHub Actions deployment:
```bash
git push origin main
```

## Quick Test

```bash
aws lambda invoke \
  --function-name rfp-agent-handler \
  --payload '{"body":"{\"message\":\"We need 500 brake sensors...\"}"}' \
  --region us-east-1 \
  /tmp/response.json

cat /tmp/response.json
```

## Configuration

See `config.py` for AWS settings, table names, and scoring weights.

## Author

Quadra Systems - RFP Management
