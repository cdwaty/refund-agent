#!/usr/bin/env python3
"""
Script to create IAM execution role for AgentCore Runtime.

This script creates an IAM role with minimal required permissions for running
agents in AgentCore Runtime.
"""

import json
import boto3
import time

# Configuration
REGION = "us-west-2"
ROLE_NAME = f"AgentCoreRuntimeExecutionRole-{int(time.time())}"
POLICY_NAME = f"AgentCoreRuntimePolicy-{int(time.time())}"

# Create IAM client
iam_client = boto3.client('iam', region_name=REGION)

print("="*80)
print("CREATING IAM EXECUTION ROLE FOR AGENTCORE RUNTIME")
print("="*80)

# Get AWS account ID
sts_client = boto3.client('sts', region_name=REGION)
account_id = sts_client.get_caller_identity()['Account']
print(f"\n✓ AWS Account: {account_id}")
print(f"✓ Region: {REGION}")

# Step 1: Define trust policy for bedrock-agentcore.amazonaws.com
print("\n📝 Step 1: Creating IAM role with trust policy...")
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

try:
    role_response = iam_client.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="Execution role for AgentCore Runtime with minimal required permissions"
    )
    role_arn = role_response['Role']['Arn']
    print(f"✓ Role created: {ROLE_NAME}")
    print(f"✓ Role ARN: {role_arn}")
except Exception as e:
    print(f"❌ Error creating role: {e}")
    exit(1)

# Step 2: Create comprehensive permissions policy
print("\n📝 Step 2: Creating permissions policy...")
permissions_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ECRAccess",
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchLogsAccess",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
                "logs:DescribeLogGroups"
            ],
            "Resource": [
                f"arn:aws:logs:{REGION}:{account_id}:log-group:/aws/bedrock-agentcore/*",
                f"arn:aws:logs:{REGION}:{account_id}:log-group:*"
            ]
        },
        {
            "Sid": "XRayAccess",
            "Effect": "Allow",
            "Action": [
                "xray:PutTraceSegments",
                "xray:PutTelemetryRecords",
                "xray:GetSamplingRules",
                "xray:GetSamplingTargets"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchMetrics",
            "Effect": "Allow",
            "Action": "cloudwatch:PutMetricData",
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "cloudwatch:namespace": "bedrock-agentcore"
                }
            }
        },
        {
            "Sid": "BedrockModelAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ApplyGuardrail"
            ],
            "Resource": "*"
        },
        {
            "Sid": "BedrockKnowledgeBaseAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock-agent:Retrieve"
            ],
            "Resource": f"arn:aws:bedrock:{REGION}:{account_id}:knowledge-base/*"
        },
        {
            "Sid": "AgentCoreMemoryAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:GetMemory",
                "bedrock-agentcore:CreateEvent",
                "bedrock-agentcore:GetLastKTurns",
                "bedrock-agentcore:RetrieveMemory",
                "bedrock-agentcore:ListEvents",
                "bedrock-agentcore:GetMemoryRecord",
                "bedrock-agentcore:RetrieveMemoryRecords",
                "bedrock-agentcore:ListMemoryRecords"
            ],
            "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:memory/*"
        },
        {
            "Sid": "AgentCoreGatewayAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:InvokeGateway",
                "bedrock-agentcore:GetGateway",
                "bedrock-agentcore:ListGatewayTargets"
            ],
            "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:gateway/*"
        },
        {
            "Sid": "WorkloadIdentityAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:GetWorkloadAccessToken",
                "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
            ],
            "Resource": [
                f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:workload-identity-directory/default",
                f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:workload-identity-directory/default/workload-identity/*"
            ]
        },
        {
            "Sid": "STSAccess",
            "Effect": "Allow",
            "Action": [
                "sts:AssumeRole",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SSMParameterAccess",
            "Effect": "Allow",
            "Action": "ssm:GetParameter",
            "Resource": f"arn:aws:ssm:{REGION}:{account_id}:parameter/app/*"
        },
        {
            "Sid": "MarketplaceAccess",
            "Effect": "Allow",
            "Action": [
                "aws-marketplace:ViewSubscriptions",
                "aws-marketplace:Subscribe"
            ],
            "Resource": "*"
        }
    ]
}

try:
    policy_response = iam_client.create_policy(
        PolicyName=POLICY_NAME,
        PolicyDocument=json.dumps(permissions_policy),
        Description="Minimal required permissions for AgentCore Runtime"
    )
    policy_arn = policy_response['Policy']['Arn']
    print(f"✓ Policy created: {POLICY_NAME}")
    print(f"✓ Policy ARN: {policy_arn}")
except Exception as e:
    print(f"❌ Error creating policy: {e}")
    print(f"Cleaning up role: {ROLE_NAME}")
    try:
        iam_client.delete_role(RoleName=ROLE_NAME)
    except:
        pass
    exit(1)

# Step 3: Attach policy to role
print("\n📝 Step 3: Attaching policy to role...")
try:
    iam_client.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn=policy_arn
    )
    print(f"✓ Policy attached to role")
except Exception as e:
    print(f"❌ Error attaching policy: {e}")
    print(f"Cleaning up resources...")
    try:
        iam_client.delete_policy(PolicyArn=policy_arn)
        iam_client.delete_role(RoleName=ROLE_NAME)
    except:
        pass
    exit(1)

# Step 4: Wait for role to propagate
print("\n📝 Step 4: Waiting for role to propagate...")
try:
    waiter = iam_client.get_waiter('role_exists')
    waiter.wait(RoleName=ROLE_NAME)
    print("✓ Role propagation confirmed")
except Exception as e:
    print(f"⚠️  Waiter not available, using 10-second sleep")
    time.sleep(10)
    print("✓ Role propagation wait complete")

# Save configuration
print("\n📝 Step 5: Saving configuration...")
config = {
    "role_name": ROLE_NAME,
    "role_arn": role_arn,
    "policy_name": POLICY_NAME,
    "policy_arn": policy_arn,
    "region": REGION,
    "account_id": account_id
}

with open('runtime_execution_role_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Configuration saved to runtime_execution_role_config.json")

# Summary
print("\n" + "="*80)
print("✅ RUNTIME EXECUTION ROLE CREATED SUCCESSFULLY")
print("="*80)
print(f"\nRole Name: {ROLE_NAME}")
print(f"Role ARN: {role_arn}")
print(f"Policy ARN: {policy_arn}")
print("\nPermissions Granted:")
print("  ✓ Bedrock - InvokeModel, InvokeModelWithResponseStream")
print("  ✓ Knowledge Base - bedrock-agent:Retrieve")
print("  ✓ Memory - GetMemory, CreateEvent, GetLastKTurns, RetrieveMemory, ListEvents")
print("  ✓ Gateway - InvokeGateway, GetGateway, ListGatewayTargets")
print("  ✓ CloudWatch Logs - CreateLogGroup, CreateLogStream, PutLogEvents, DescribeLogStreams")
print("  ✓ X-Ray - PutTraceSegments, PutTelemetryRecords")
print("  ✓ ECR - GetAuthorizationToken, BatchCheckLayerAvailability, GetDownloadUrlForLayer, BatchGetImage")
print("  ✓ Workload Identity - Secure credential management")
print("  ✓ STS - Role assumption and identity")
print("  ✓ SSM Parameter Store - Configuration access")
print("\nTrust Policy:")
print("  ✓ bedrock-agentcore.amazonaws.com can assume this role")
print("\n" + "="*80)
print("Next Steps:")
print("  1. Use this role ARN when deploying to AgentCore Runtime")
print("  2. Runtime will use this role to access all required services")
print("  3. Deploy your agent with: agentcore configure && agentcore launch")
print("="*80)
