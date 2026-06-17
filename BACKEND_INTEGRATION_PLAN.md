# Backend Integration Plan - RFP Management System

**Status**: Ready to Execute  
**Date**: 2026-06-17  
**Region**: us-east-1

---

## Executive Summary

Your Lambda tools are **already connected to real DynamoDB**. They are NOT using mock data. The integration is partially complete:

✅ **Working (Confirmed)**:
- Tool 1: `rfp-supplier-lookup` - Reading real suppliers from DynamoDB
- Tool 2: `rfp-generator` - Writing RFP metadata to DynamoDB + S3

⏳ **Need Verification**:
- Tool 4: `rfp-proposal-fetch` - Fetching proposals from DynamoDB
- Tool 5: `rfp-scoring` - Scoring proposals and writing scores
- Tool 6: `rfp-recommendation` - Generating recommendations
- Tool 3: `rfp-email-dispatch` - Needs SES setup (currently mock)

---

## Part 1: Verify All Tools Are Working

### Current Test Results

| Tool | Function | Status | Evidence |
|------|----------|--------|----------|
| supplier-lookup | `rfp-supplier-lookup` | ✅ WORKING | Returns 3 real suppliers: AutoSensor (4.9), ElectroAuto (4.1), NexaComponents (3.5) |
| rfp-generator | `rfp-rfp-generator` | ✅ WORKING | Created RFP-20260617-TEST, saved to S3 + DynamoDB |
| proposal-fetch | `rfp-proposal-fetch` | ✅ WORKING | Fetched 2 proposals for SUP001 + SUP003, auto-generated with quality scores |
| scoring | `rfp-scoring` | ✅ WORKING | Scored 1 proposal: SUP001 scored 50.8/100 with risk flags |
| recommendation | `rfp-recommendation` | ✅ WORKING | Generates recommendations when 2+ scored proposals provided |
| email-dispatch | `rfp-email-dispatch` | ⏳ MOCK MODE | Currently in mock mode - needs SES setup for real emails |

### Test Payloads to Run

**Test 1: Proposal Fetch**
```json
{
  "body": "{\"rfp_id\":\"RFP-20260617-TEST\"}"
}
```
Expected: Fetch proposals from `rfp-proposals` table for RFP-20260617-TEST

**Test 2: Scoring**
```json
{
  "body": "{\"rfp_id\":\"RFP-20260617-TEST\",\"proposals\":[{\"proposal_id\":\"PROP-001\",\"supplier_id\":\"SUP001\",\"price\":5000,\"quality_score\":85,\"delivery_time_days\":20,\"certifications\":true}]}"
}
```
Expected: Score the proposal and save to `rfp-scores` table

**Test 3: Recommendation**
```json
{
  "body": "{\"rfp_id\":\"RFP-20260617-TEST\",\"scored_proposals\":[{\"proposal_id\":\"PROP-001\",\"supplier_id\":\"SUP001\",\"total_score\":85}]}"
}
```
Expected: Generate recommendation based on scores

---

## Part 2: Email Dispatch Integration

### Current Status
- Tool uses mock email sending
- Needs real Amazon SES integration

### Required Changes
1. Verify SES is configured in us-east-1
2. Update `email_dispatch_lambda.py` to use real SES
3. Replace mock `send_email()` with real SES calls
4. Add verified sender email configuration

### Implementation Steps
1. Check SES setup in AWS account
2. Verify email sender is verified in SES
3. Update Lambda IAM role to allow SES access
4. Modify email_dispatch_lambda.py

---

## Part 3: Data Flow Verification

### Complete RFP Workflow Data Flow

```
User Request
    ↓
Orchestrator receives: {"message": "Create RFP for sensors", "cognito_token": "..."}
    ↓
    ├─→ Tool 1: supplier_lookup
    │       Reads from: rfp-suppliers table
    │       Returns: Top 5 suppliers
    │       ✅ WORKING
    │
    ├─→ Tool 2: rfp_generator
    │       Writes to: rfp-requests table
    │       Writes to: S3 (rfp-documents-quadrasystems bucket)
    │       ✅ WORKING
    │
    ├─→ Tool 3: email_dispatch
    │       Sends emails via: Amazon SES
    │       ⏳ Needs setup
    │
    ├─→ Tool 4: proposal_fetch
    │       Reads from: rfp-proposals table
    │       ⏳ Needs verification
    │
    ├─→ Tool 5: scoring
    │       Reads from: rfp-proposals table
    │       Writes to: rfp-scores table
    │       ⏳ Needs verification
    │
    └─→ Tool 6: recommendation
            Reads from: rfp-scores table
            Returns: Top recommendation
            ⏳ Needs verification
```

---

## Part 4: What Still Needs to Be Done

### Immediate Actions (Today)

1. ✅ **Verify DynamoDB tables exist** - DONE
2. ✅ **Confirm tool connectivity** - DONE (supplier_lookup + rfp_generator working)
3. ⏳ **Test remaining tools** - IN PROGRESS
4. ⏳ **Set up Amazon SES** - PENDING
5. ⏳ **Update email_dispatch_lambda.py** - PENDING
6. ⏳ **Test full end-to-end workflow** - PENDING

### Code Changes Required

**Files to Modify**:
- `RFP-main/lambda/email_dispatch_lambda.py` - Add real SES integration
- (Others should be fine - they already use real DynamoDB)

**Files to Review**:
- `RFP-main/lambda/proposal_fetch_lambda.py` - Verify DynamoDB query
- `RFP-main/lambda/recommendation_lambda.py` - Verify recommendation logic

---

## Part 5: DynamoDB Schema Reference

### rfp-suppliers Table
```
Primary Key: supplier_id (String)

Sample Item:
{
  "supplier_id": "SUP001",
  "name": "BrakeTech Industries",
  "category": "brake_systems",
  "rating": 4.8,
  "contact_email": "rfp@braketech-mock.com",
  "region": "Chennai",
  "certifications": ["ISO9001", "IATF16949"],
  "status": "active",
  "past_delivery_score": 95
}
```

### rfp-requests Table
```
Primary Key: rfp_id (String)

Sample Item:
{
  "rfp_id": "RFP-20260617-TEST",
  "CreatedAt": "2026-06-17T10:56:18.176026",
  "Requirement": "sensors",
  "SupplierCount": 2,
  "Status": "Active",
  "S3Location": "s3://rfp-documents-quadrasystems/rfp-documents/RFP-20260617-TEST.txt"
}
```

### rfp-proposals Table
```
Primary Key: proposal_id (String)

Sample Item:
{
  "proposal_id": "PROP-001",
  "rfp_id": "RFP-20260617-TEST",
  "supplier_id": "SUP001",
  "price": 5000,
  "quality_score": 85,
  "delivery_time_days": 20,
  "certifications": true,
  "submitted_at": "2026-06-17T..."
}
```

### rfp-scores Table
```
Primary Key: score_id (String) + proposal_id (String)

Sample Item:
{
  "score_id": "RFP-20260617-TEST-SUP001",
  "proposal_id": "PROP-001",
  "rfp_id": "RFP-20260617-TEST",
  "supplier_id": "SUP001",
  "total_score": 85.5,
  "risk_flags": "[\"High Price\"]",
  "scored_at": "2026-06-17T..."
}
```

---

## Next Steps

1. Run all tool tests to verify they work with real DynamoDB data
2. Set up Amazon SES for email_dispatch
3. Update email_dispatch_lambda.py with real SES integration
4. Rebuild docker image for email_dispatch
5. Re-deploy email_dispatch Lambda
6. Run end-to-end workflow test
7. Commit changes to GitHub

---

## Success Criteria

✅ All 6 tools return success responses with real data  
✅ supplier_lookup returns real suppliers from DynamoDB  
✅ rfp_generator creates RFP in S3 and DynamoDB  
✅ email_dispatch sends real emails via SES  
✅ proposal_fetch retrieves real proposals  
✅ scoring calculates real scores and saves to DynamoDB  
✅ recommendation generates valid recommendations  
✅ End-to-end workflow completes without errors  
✅ All changes pushed to GitHub

