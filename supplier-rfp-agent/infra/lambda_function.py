from aws_cdk import (Stack, Duration)
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ecr as ecr
from constructs import Construct
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ECR_URI, LAMBDA_ROLE_ARN, REGION


class LambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 dynamo_stack, s3_stack, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        execution_role = iam.Role.from_role_arn(
            self, "RfpLambdaRole", LAMBDA_ROLE_ARN)

        # Reference existing ECR repository
        repo = ecr.Repository.from_repository_uri(
            self, "RfpAgentRepo", repository_uri=ECR_URI)

        self.rfp_lambda = lambda_.DockerImageFunction(
            self, "RfpAgentLambda",
            function_name="rfp-agent-handler",
            code=lambda_.DockerImageCode.from_ecr(
                repository=repo,
                tag_or_digest="latest",
            ),
            role=execution_role,
            memory_size=512,
            timeout=Duration.seconds(300),
            environment={
                "AWS_DEFAULT_REGION": REGION,
            },
        )

        # Grant permissions to DynamoDB tables
        dynamo_stack.suppliers_table.grant_read_write_data(self.rfp_lambda)
        dynamo_stack.requests_table.grant_read_write_data(self.rfp_lambda)
        dynamo_stack.proposals_table.grant_read_write_data(self.rfp_lambda)
        dynamo_stack.scores_table.grant_read_write_data(self.rfp_lambda)

        # Grant permissions to S3
        s3_stack.rfp_bucket.grant_read_write(self.rfp_lambda)
