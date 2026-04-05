#!/usr/bin/env python3
"""
Script to create Lambda function for order lookup.

This script creates a Lambda function that looks up order details by order ID.
"""

import json
import boto3
import time
import zipfile
import io
from botocore.exceptions import ClientError

REGION = 'us-west-2'

# Initialize clients
lambda_client = boto3.client('lambda', region_name=REGION)
iam_client = boto3.client('iam')
sts_client = boto3.client('sts', region_name=REGION)

print("="*80)
print("CREATING LAMBDA FUNCTION FOR ORDER LOOKUP")
print("="*80)

# Get AWS account ID
try:
    account_id = sts_client.get_caller_identity()['Account']
    print(f"\n✓ AWS Account ID: {account_id}")
except Exception as e:
    print(f"\n❌ Error getting account ID: {str(e)}")
    exit(1)

# Lambda function code
lambda_code = '''
import json
from datetime import datetime, timedelta

def lambda_handler(event, context):
    """
    Look up order details by order ID.
    
    Args:
        event: Contains 'order_id' parameter
        
    Returns:
        Order details including eligibility for return
    """
    
    # Mock order database
    orders = {
        "ORD-001": {
            "order_id": "ORD-001",
            "product_name": "Dell XPS 15 Laptop",
            "purchase_date": (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
            "amount": 1299.99,
            "category": "electronics",
            "condition": "delivered",
            "return_eligible": True,
            "days_remaining": 15
        },
        "ORD-002": {
            "order_id": "ORD-002",
            "product_name": "iPhone 13 Pro",
            "purchase_date": (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d'),
            "amount": 999.99,
            "category": "electronics",
            "condition": "delivered",
            "return_eligible": False,
            "days_remaining": 0
        },
        "ORD-003": {
            "order_id": "ORD-003",
            "product_name": "Samsung Galaxy Tab S8",
            "purchase_date": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            "amount": 649.99,
            "category": "electronics",
            "condition": "defective",
            "return_eligible": True,
            "days_remaining": 25
        }
    }
    
    # Extract order_id from event
    order_id = event.get('order_id', '').upper()
    
    if not order_id:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Missing order_id parameter'
            })
        }
    
    # Look up order
    order = orders.get(order_id)
    
    if not order:
        return {
            'statusCode': 404,
            'body': json.dumps({
                'error': f'Order {order_id} not found',
                'available_orders': list(orders.keys())
            })
        }
    
    # Return order details
    return {
        'statusCode': 200,
        'body': json.dumps(order)
    }
'''

try:
    # Step 1: Create Lambda execution role
    print("\n📝 Step 1: Creating Lambda execution role...")
    
    lambda_role_name = f"OrderLookupLambdaRole-{int(time.time())}"
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        create_role_response = iam_client.create_role(
            RoleName=lambda_role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Execution role for OrderLookupFunction Lambda'
        )
        lambda_role_arn = create_role_response['Role']['Arn']
        print(f"✓ Lambda role created: {lambda_role_arn}")
        
        # Attach basic Lambda execution policy
        iam_client.attach_role_policy(
            RoleName=lambda_role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        print("✓ Attached AWSLambdaBasicExecutionRole policy")
        
        # Wait for role to propagate
        print("⏳ Waiting for IAM role to propagate (10 seconds)...")
        time.sleep(10)
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"⚠️  Role already exists, retrieving ARN...")
            get_role_response = iam_client.get_role(RoleName=lambda_role_name)
            lambda_role_arn = get_role_response['Role']['Arn']
            print(f"✓ Using existing role: {lambda_role_arn}")
        else:
            raise
    
    # Step 2: Create deployment package
    print("\n📝 Step 2: Creating Lambda deployment package...")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('lambda_function.py', lambda_code)
    
    zip_buffer.seek(0)
    deployment_package = zip_buffer.read()
    
    print(f"✓ Deployment package created ({len(deployment_package)} bytes)")
    
    # Step 3: Create Lambda function
    print("\n📝 Step 3: Creating Lambda function: OrderLookupFunction...")
    
    function_name = 'OrderLookupFunction'
    
    try:
        create_function_response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.10',
            Role=lambda_role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': deployment_package},
            Description='Look up order details by order ID for returns processing',
            Timeout=30,
            MemorySize=128,
            Environment={
                'Variables': {
                    'REGION': REGION
                }
            }
        )
        
        function_arn = create_function_response['FunctionArn']
        print(f"✓ Lambda function created: {function_arn}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print(f"⚠️  Function already exists, retrieving ARN...")
            get_function_response = lambda_client.get_function(FunctionName=function_name)
            function_arn = get_function_response['Configuration']['FunctionArn']
            print(f"✓ Using existing function: {function_arn}")
        else:
            raise
    
    # Step 4: Define tool schema for Gateway
    print("\n📝 Step 4: Creating tool schema for Gateway...")
    
    tool_schema = {
        "name": "lookup_order",
        "description": "Look up order details by order ID. Returns order information including product name, purchase date, amount, and return eligibility. Use this to check if a customer's order can be returned.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to look up (e.g., ORD-001, ORD-002, ORD-003)"
                }
            },
            "required": ["order_id"]
        }
    }
    
    print("✓ Tool schema created")
    
    # Step 5: Save configuration
    print("\n📝 Step 5: Saving configuration to lambda_config.json...")
    
    config = {
        "function_name": function_name,
        "function_arn": function_arn,
        "lambda_role_arn": lambda_role_arn,
        "region": REGION,
        "tool_schema": tool_schema,
        "sample_orders": [
            "ORD-001: Dell XPS 15 Laptop (recent, eligible)",
            "ORD-002: iPhone 13 Pro (old, not eligible)",
            "ORD-003: Samsung Galaxy Tab S8 (defective, eligible)"
        ]
    }
    
    with open('lambda_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✓ Configuration saved to lambda_config.json")
    
    # Step 6: Test the function
    print("\n📝 Step 6: Testing Lambda function...")
    
    test_event = {"order_id": "ORD-001"}
    
    try:
        invoke_response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        response_payload = json.loads(invoke_response['Payload'].read())
        print("✓ Lambda function test successful")
        print(f"  Test result: {json.dumps(response_payload, indent=2)}")
        
    except Exception as e:
        print(f"⚠️  Lambda test failed: {str(e)}")
        print("  Function created but may need time to initialize")
    
    # Summary
    print("\n" + "="*80)
    print("✅ LAMBDA FUNCTION CREATED SUCCESSFULLY")
    print("="*80)
    print(f"\nFunction Name: {function_name}")
    print(f"Function ARN: {function_arn}")
    print(f"Runtime: Python 3.10")
    print(f"Handler: lambda_function.lambda_handler")
    print(f"\nTool Name: lookup_order")
    print(f"\nSample Orders:")
    print(f"  • ORD-001: Dell XPS 15 Laptop (purchased 15 days ago, eligible)")
    print(f"  • ORD-002: iPhone 13 Pro (purchased 45 days ago, not eligible)")
    print(f"  • ORD-003: Samsung Galaxy Tab S8 (purchased 5 days ago, defective, eligible)")
    print("\n" + "="*80)
    print("Next Steps:")
    print("  1. Create AgentCore Gateway")
    print("  2. Add this Lambda function as a gateway target")
    print("  3. Agent can call lookup_order tool through the gateway")
    print("="*80)

except ClientError as e:
    print(f"\n❌ Error: {e.response['Error']['Message']}")
    print(f"   Error Code: {e.response['Error']['Code']}")
    exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
