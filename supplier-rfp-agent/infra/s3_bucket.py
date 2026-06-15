from aws_cdk import (Stack, RemovalPolicy)
from aws_cdk import aws_s3 as s3
from constructs import Construct
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RFP_DOCS_BUCKET


class S3Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.rfp_bucket = s3.Bucket(
            self, "RfpDocsBucket",
            bucket_name=RFP_DOCS_BUCKET,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN,
        )
