#!/usr/bin/env python3
"""
Script to add Lambda target to AgentCore Gateway.

Prerequisites:
- gateway_config.json (from gateway creation)
- lambda_config.json (from Lambda creation)
"""

import json
import boto3

print("="*80)
print("ADDING LAMBDA TARGET TO GATEWAY")
print("="*80)

# Load gateway configuration
print("\n📝 Step 1: Loading configuration files...")

try:
    with open('gateway_config.json') as f:
        gateway_config = json.load(f)
    print(f"✓ Loaded gateway config")
    print(f"  Gateway ID: {gateway_config['gateway_id']}")
except FileNotFoundError:
    print("❌ Error: gateway_config.json not found")
    print("   Run 11_create_gateway.py first")
    exit(1)

try:
    with open('lambda_config.json') as f:
        lambda_config = json.load(f)
    print(f"✓ Loaded Lambda config")
    print(f"  Function ARN: {lambda_config['function_arn']}")
    print(f"  Tool: {lambda_config['tool_schema']['name']}")
except FileNotFoundError:
    print("❌ Error: lambda_config.json not found")
    print("   Run 10_create_lambda.py first")
    exit(1)

# Initialize AgentCore control plane client
print("\n📝 Step 2: Initializing AgentCore client...")
gateway_client = boto3.client("bedrock-agentcore-control", region_name='us-west-2')
print("✓ Client initialized")

# Build Lambda target configuration with MCP protocol
print("\n📝 Step 3: Building Lambda target configuration...")

lambda_arn = lambda_config['function_arn']
tool_schema = [lambda_config['tool_schema']]

lambda_target_config = {
    "mcp": {
        "lambda": {
            "lambdaArn": lambda_arn,
            "toolSchema": {
                "inlinePayload": tool_schema
            }
        }
    }
}

# Use gateway's IAM role for Lambda invocation
credential_config = [{"credentialProviderType": "GATEWAY_IAM_ROLE"}]

print("✓ Target configuration created")
print(f"  Protocol: MCP")
print(f"  Lambda ARN: {lambda_arn}")
print(f"  Tool Schema: {tool_schema[0]['name']}")

# Create target
print("\n📝 Step 4: Adding Lambda target to gateway...")
print(f"  Gateway ID: {gateway_config['gateway_id']}")
print(f"  Target Name: OrderLookup")

try:
    create_response = gateway_client.create_gateway_target(
        gatewayIdentifier=gateway_config["gateway_id"],
        name="OrderLookup",
        description="Lambda function to look up order details by order ID",
        targetConfiguration=lambda_target_config,
        credentialProviderConfigurations=credential_config
    )
    
    target_id = create_response["targetId"]
    
    print(f"✓ Lambda target added successfully!")
    print(f"  Target ID: {target_id}")
    
except Exception as e:
    print(f"❌ Error adding target: {str(e)}")
    exit(1)

# Update gateway config with target info
print("\n📝 Step 5: Updating gateway_config.json...")

gateway_config['targets'] = gateway_config.get('targets', [])
gateway_config['targets'].append({
    "target_id": target_id,
    "target_name": "OrderLookup",
    "tool_name": "lookup_order",
    "lambda_arn": lambda_arn
})

with open('gateway_config.json', 'w') as f:
    json.dump(gateway_config, f, indent=2)

print("✓ Configuration updated")

# Summary
print("\n" + "="*80)
print("✅ LAMBDA TARGET ADDED SUCCESSFULLY")
print("="*80)
print(f"\nGateway: {gateway_config['name']}")
print(f"Gateway ID: {gateway_config['gateway_id']}")
print(f"\nTarget Name: OrderLookup")
print(f"Target ID: {target_id}")
print(f"\nTool Available: lookup_order")
print(f"Tool Description: {tool_schema[0]['description']}")
print(f"\nLambda Function: {lambda_config['function_name']}")
print(f"Lambda ARN: {lambda_arn}")
print("\n" + "="*80)
print("Next Steps:")
print("  1. Agent can now discover the lookup_order tool through the gateway")
print("  2. Agent calls lookup_order with order_id parameter")
print("  3. Gateway authenticates, routes to Lambda, and returns results")
print("  4. Test the gateway integration with your agent")
print("="*80)
