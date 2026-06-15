from aws_cdk import (Stack, RemovalPolicy)
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (SUPPLIERS_TABLE, REQUESTS_TABLE,
                    PROPOSALS_TABLE, SCORES_TABLE)


class DynamoDBStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Table 1: rfp-suppliers
        self.suppliers_table = dynamodb.Table(
            self, "SuppliersTable",
            table_name=SUPPLIERS_TABLE,
            partition_key=dynamodb.Attribute(
                name="supplier_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Table 2: rfp-requests
        self.requests_table = dynamodb.Table(
            self, "RequestsTable",
            table_name=REQUESTS_TABLE,
            partition_key=dynamodb.Attribute(
                name="rfp_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Table 3: rfp-proposals  (+ GSI on rfp_id)
        self.proposals_table = dynamodb.Table(
            self, "ProposalsTable",
            table_name=PROPOSALS_TABLE,
            partition_key=dynamodb.Attribute(
                name="proposal_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(
                name="rfp_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
        self.proposals_table.add_global_secondary_index(
            index_name="rfp_id-index",
            partition_key=dynamodb.Attribute(
                name="rfp_id", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Table 4: rfp-scores
        self.scores_table = dynamodb.Table(
            self, "ScoresTable",
            table_name=SCORES_TABLE,
            partition_key=dynamodb.Attribute(
                name="score_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(
                name="proposal_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
