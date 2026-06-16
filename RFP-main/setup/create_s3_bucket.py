"""
Creates the S3 bucket for RFP documents (idempotent).
Usage: python setup/create_s3_bucket.py
"""
import boto3
from botocore.exceptions import ClientError
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REGION, RFP_DOCS_BUCKET

s3 = boto3.client("s3", region_name=REGION)

try:
    if REGION == "us-east-1":
        s3.create_bucket(Bucket=RFP_DOCS_BUCKET)
    else:
        s3.create_bucket(
            Bucket=RFP_DOCS_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
    # Block all public access
    s3.put_public_access_block(
        Bucket=RFP_DOCS_BUCKET,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls":       True,
            "IgnorePublicAcls":      True,
            "BlockPublicPolicy":     True,
            "RestrictPublicBuckets": True,
        },
    )
    print(f"✅ Created S3 bucket: {RFP_DOCS_BUCKET}")
except ClientError as e:
    if e.response["Error"]["Code"] in ("BucketAlreadyExists",
                                        "BucketAlreadyOwnedByYou"):
        print(f"⚠️  Bucket already exists: {RFP_DOCS_BUCKET}")
    else:
        raise
