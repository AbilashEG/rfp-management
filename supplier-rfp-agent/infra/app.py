#!/usr/bin/env python3
"""
CDK app entry — deploys DynamoDB, S3, and Lambda stacks.
Usage: cdk deploy --all
"""
import aws_cdk as cdk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra.dynamodb_tables  import DynamoDBStack
from infra.s3_bucket        import S3Stack
from infra.lambda_function  import LambdaStack
from config                 import REGION, AWS_ACCOUNT_ID

app = cdk.App()

env = cdk.Environment(account=AWS_ACCOUNT_ID, region=REGION)

dynamo_stack = DynamoDBStack(app, "RfpDynamoDBStack",  env=env)
s3_stack     = S3Stack(app,      "RfpS3Stack",         env=env)
lambda_stack = LambdaStack(app,  "RfpLambdaStack",
                           env=env,
                           dynamo_stack=dynamo_stack,
                           s3_stack=s3_stack)

app.synth()
