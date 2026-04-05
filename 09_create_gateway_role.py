#!/usr/bin/env python3
"""
Script to create IAM role for AgentCore Gateway.

This script creates an IAM role that allows the gateway to invoke Lambda functions.
"""

import json
import boto3
import time
from botocore.exceptions import ClientError

REGION = 'us-west-2'

# Initialize IAM and STS clients
iam_client = boto3.client('iam')
sts_client = boto3.client('sts', region_name=REGION)

print("="*80)
print("CREATING IAM ROLE FOR AGENTCORE GATEWAY")
print("="*80)

# Get AWS account ID
try:
    account_id = sts_client.get_caller_identity()['Account']
    print(f"\n✓ AWS Account ID: {account_id}")
except Exception as e:
    print(f"\n❌ Error getting account ID: {str(e)}")
    exit(1)

# Generate unique role name
role_name = f"ReturnsGatewayExecutionRole-{int(time.time())}"

try:
    # Step 1: Define trust policy (who can assume this role)
    print("\n📝 Step 1: Creating trust policy...")
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    print("✓ Trust policy created for bedrock-agentcore.amazonaws.com")
    
    # Step 2: Create IAM role
    print(f"\n📝 Step 2: Creating IAM role: {role_name}...")
    
    create_role_response = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Execution role for AgentCore Gateway to invoke Lambda functions',
        MaxSessionDuration=3600
    )
    
    role_arn = create_role_response['Role']['Arn']
    print(f"✓ Role created: {role_arn}")
    
    # Step 3: Define permissions policy (what this role can do)
    print("\n📝 Step 3: Creating permissions policy...")
    
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": f"arn:aws:logs:{REGION}:{account_id}:log-group:/aws/bedrock-agentcore/gateway/*"
            }
        ]
    }
    
    print("✓ Permissions policy created")
    print("  - Lambda: InvokeFunction on all functions")
    print("  - CloudWatch Logs: Create and write logs")
    
    # Step 4: Attach inline policy to role
    print("\n📝 Step 4: Attaching permissions policy to role...")
    
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName='GatewayExecutionPolicy',
        PolicyDocument=json.dumps(permissions_policy)
    )
    
    print("✓ Policy attached to role")
    
    # Step 5: Wait for role to propagate
    print("\n📝 Step 5: Waiting for IAM role to propagate...")
    time.sleep(10)
    print("✓ Role propagation complete")
    
    # Step 6: Save configuration
    print("\n📝 Step 6: Saving configuration to gateway_role_config.json...")
    
    config = {
        "role_arn": role_arn,
        "role_name": role_name,
        "region": REGION,
        "account_id": account_id
    }
    
    with open('gateway_role_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✓ Configuration saved to gateway_role_config.json")
    
    # Summary
    print("\n" + "="*80)
    print("✅ GATEWAY IAM ROLE CREATED SUCCESSFULLY")
    print("="*80)
    print(f"\nRole Name: {role_name}")
    print(f"Role ARN: {role_arn}")
    print(f"\nPermissions:")
    print(f"  • Invoke Lambda functions in {REGION}")
    print(f"  • Write CloudWatch logs")
    print(f"\nTrust Policy:")
    print(f"  • bedrock-agentcore.amazonaws.com can assume this role")
    print("\n" + "="*80)
    print("Next Steps:")
    print("  1. Use this role ARN when creating the AgentCore Gateway")
    print("  2. Gateway will use this role to invoke Lambda functions")
    print("  3. Create Lambda functions that the gateway will call")
    print("="*80)

except ClientError as e:
    error_code = e.response['Error']['Code']
    error_message = e.response['Error']['Message']
    
    if error_code == 'EntityAlreadyExists':
        print(f"\n⚠️  Role already exists: {role_name}")
        print("   Retrieving existing role ARN...")
        
        try:
            get_role_response = iam_client.get_role(RoleName=role_name)
            role_arn = get_role_response['Role']['Arn']
            
            config = {
                "role_arn": role_arn,
                "role_name": role_name,
                "region": REGION,
                "account_id": account_id
            }
            
            with open('gateway_role_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✓ Using existing role: {role_arn}")
            print("✓ Configuration saved to gateway_role_config.json")
        except Exception as e2:
            print(f"❌ Error retrieving existing role: {str(e2)}")
            exit(1)
    else:
        print(f"\n❌ Error: {error_message}")
        print(f"   Error Code: {error_code}")
        exit(1)
        
except Exception as e:
    print(f"\n❌ Unexpected error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
