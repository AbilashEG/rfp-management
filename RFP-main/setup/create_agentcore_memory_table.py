"""
Create DynamoDB table for AgentCore Memory
Stores conversation history, preferences, and session state
"""

import boto3
import os

REGION = os.environ.get("REGION", "us-east-1")
TABLE_NAME = "agentcore-memory"

dynamodb = boto3.client("dynamodb", region_name=REGION)


def create_memory_table():
    """Create agentcore-memory DynamoDB table"""
    try:
        print(f"Creating DynamoDB table: {TABLE_NAME}")
        
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "session_id", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "user_id", "KeyType": "RANGE"}    # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "session_id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",  # Auto-scaling
            StreamSpecification={
                "StreamViewType": "NEW_AND_OLD_IMAGES"
            },
            Tags=[
                {"Key": "Environment", "Value": "production"},
                {"Key": "Application", "Value": "rfp-agent"},
                {"Key": "Component", "Value": "agentcore-memory"}
            ]
        )
        
        print(f"✅ Table {TABLE_NAME} created successfully")
        
        # Enable TTL for automatic session expiration
        print("Setting up TTL for session expiration...")
        dynamodb.update_time_to_live(
            TableName=TABLE_NAME,
            TimeToLiveSpecification={
                "AttributeName": "expires_at",
                "Enabled": True
            }
        )
        print("✅ TTL enabled (24 hours)")
        
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠️  Table {TABLE_NAME} already exists")
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        raise


if __name__ == "__main__":
    create_memory_table()
