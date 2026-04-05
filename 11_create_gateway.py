#!/usr/bin/env python3
"""
Script to create AgentCore Gateway.

Prerequisites:
- cognito_config.json (from Cognito setup)
- gateway_role_config.json (from IAM role setup)
"""

import json
import boto3

print("="*80)
print("CREATING AGENTCORE GATEWAY")
print("="*80)

# Load configuration
print("\n📝 Step 1: Loading configuration files...")

try:
    with open('cognito_config.json') as f:
        cognito_config = json.load(f)
    print(f"✓ Loaded Cognito config")
    print(f"  Client ID: {cognito_config['client_id']}")
    print(f"  Discovery URL: {cognito_config['discovery_url']}")
except FileNotFoundError:
    print("❌ Error: cognito_config.json not found")
    print("   Run 08_create_cognito.py first")
    exit(1)

try:
    with open('gateway_role_config.json') as f:
        role_config = json.load(f)
    print(f"✓ Loaded IAM role config")
    print(f"  Role ARN: {role_config['role_arn']}")
except FileNotFoundError:
    print("❌ Error: gateway_role_config.json not found")
    print("   Run 09_create_gateway_role.py first")
    exit(1)

# Initialize AgentCore control plane client
print("\n📝 Step 2: Initializing AgentCore client...")
gateway_client = boto3.client("bedrock-agentcore-control", region_name='us-west-2')
print("✓ Client initialized")

# Build auth configuration for Cognito JWT
print("\n📝 Step 3: Building authentication configuration...")
auth_config = {
    "customJWTAuthorizer": {
        "allowedClients": [cognito_config["client_id"]],
        "discoveryUrl": cognito_config["discovery_url"]
    }
}
print("✓ Auth config created with Cognito JWT authorizer")

# Create gateway
print("\n📝 Step 4: Creating AgentCore Gateway...")
print("   Name: ReturnsRefundsGateway")
print("   Protocol: MCP")
print("   Authorizer: CUSTOM_JWT")

try:
    create_response = gateway_client.create_gateway(
        name="ReturnsRefundsGateway",
        roleArn=role_config["role_arn"],
        protocolType="MCP",
        authorizerType="CUSTOM_JWT",
        authorizerConfiguration=auth_config,
        description="Gateway for returns and refunds agent to access order lookup tools"
    )
    
    # Extract gateway details
    gateway_id = create_response["gatewayId"]
    gateway_url = create_response["gatewayUrl"]
    gateway_arn = create_response["gatewayArn"]
    
    print(f"✓ Gateway created successfully!")
    print(f"  Gateway ID: {gateway_id}")
    print(f"  Gateway URL: {gateway_url}")
    print(f"  Gateway ARN: {gateway_arn}")
    
except Exception as e:
    print(f"❌ Error creating gateway: {str(e)}")
    exit(1)

# Save gateway config
print("\n📝 Step 5: Saving configuration to gateway_config.json...")

config = {
    "id": gateway_id,
    "gateway_id": gateway_id,
    "gateway_url": gateway_url,
    "gateway_arn": gateway_arn,
    "name": "ReturnsRefundsGateway",
    "region": "us-west-2"
}

with open('gateway_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Configuration saved to gateway_config.json")

# Summary
print("\n" + "="*80)
print("✅ GATEWAY CREATED SUCCESSFULLY")
print("="*80)
print(f"\nGateway Name: ReturnsRefundsGateway")
print(f"Gateway ID: {gateway_id}")
print(f"Gateway URL: {gateway_url}")
print(f"\nAuthentication:")
print(f"  Type: CUSTOM_JWT (Cognito)")
print(f"  Client ID: {cognito_config['client_id']}")
print(f"  Discovery URL: {cognito_config['discovery_url']}")
print(f"\nExecution Role:")
print(f"  {role_config['role_arn']}")
print("\n" + "="*80)
print("Next Steps:")
print("  1. Add Lambda function as a gateway target")
print("  2. Agent can discover and call tools through this gateway")
print("  3. Gateway handles authentication and routing automatically")
print("="*80)
