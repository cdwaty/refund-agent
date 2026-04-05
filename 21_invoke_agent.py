#!/usr/bin/env python3
"""
Script to invoke deployed AgentCore Runtime agent.

This script:
1. Loads Cognito credentials
2. Gets OAuth token
3. Invokes the agent
4. Displays the response
"""

import json
import os
import sys
import requests
from bedrock_agentcore_starter_toolkit import Runtime

print("="*80)
print("INVOKING AGENTCORE RUNTIME AGENT")
print("="*80)

# Check if runtime config exists
if not os.path.exists('runtime_config.json'):
    print("\n❌ Error: Agent not deployed yet")
    print("   Run 19_deploy_agent.py first")
    sys.exit(1)

# Load runtime config
with open('runtime_config.json') as f:
    runtime_config = json.load(f)
    agent_name = runtime_config.get('agent_name', 'returns_refunds_agent')
    agent_arn = runtime_config.get('agent_arn')

print(f"\n✓ Agent Name: {agent_name}")
print(f"✓ Agent ARN: {agent_arn}")

# Load Cognito configuration
print("\n📝 Step 1: Loading Cognito credentials...")
try:
    with open('cognito_config.json') as f:
        cognito_config = json.load(f)
    print(f"✓ Client ID: {cognito_config['client_id']}")
    print(f"✓ Discovery URL: {cognito_config['discovery_url']}")
except FileNotFoundError:
    print("❌ Error: cognito_config.json not found")
    print("   Run 08_create_cognito.py first")
    sys.exit(1)

# Load runtime execution role config
try:
    with open('runtime_execution_role_config.json') as f:
        role_config = json.load(f)
except FileNotFoundError:
    print("❌ Error: runtime_execution_role_config.json not found")
    sys.exit(1)

# Load YAML config
if not os.path.exists('.bedrock_agentcore.yaml'):
    print("❌ Error: .bedrock_agentcore.yaml not found")
    print("   Run 19_deploy_agent.py first")
    sys.exit(1)

import yaml
with open('.bedrock_agentcore.yaml') as f:
    yaml_config = yaml.safe_load(f)

default_agent = yaml_config.get('default_agent')
agent_config = yaml_config.get('agents', {}).get(default_agent, {})
entrypoint = agent_config.get('entrypoint', '17_runtime_agent.py')

# Step 2: Get OAuth token
print("\n📝 Step 2: Getting OAuth bearer token...")

try:
    # Get token endpoint from discovery URL
    discovery_response = requests.get(cognito_config['discovery_url'], timeout=10)
    discovery_response.raise_for_status()
    token_endpoint = discovery_response.json()['token_endpoint']
    
    print(f"✓ Token endpoint: {token_endpoint}")
    
    # Request token using client credentials flow
    token_response = requests.post(
        token_endpoint,
        data={
            'grant_type': 'client_credentials',
            'client_id': cognito_config['client_id'],
            'client_secret': cognito_config['client_secret'],
            'scope': 'gateway-api/read gateway-api/write'
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=10
    )
    
    token_response.raise_for_status()
    bearer_token = token_response.json()['access_token']
    
    print("✓ OAuth token obtained")
    
except Exception as e:
    print(f"❌ Error getting OAuth token: {e}")
    print("\nTroubleshooting:")
    print("  1. Check Cognito configuration")
    print("  2. Verify client ID and secret are correct")
    print("  3. Check network connectivity")
    sys.exit(1)

# Step 3: Initialize Runtime
print("\n📝 Step 3: Initializing Runtime SDK...")
runtime = Runtime()

# Build authorizer configuration
auth_config = {
    "customJWTAuthorizer": {
        "allowedClients": [cognito_config["client_id"]],
        "discoveryUrl": cognito_config["discovery_url"]
    }
}

# Configure runtime
print("📝 Step 4: Loading runtime configuration...")
print("\nNote: The SDK may show 'memory disabled' below - this is expected.")
print("Memory is managed via environment variables (MEMORY_ID), not runtime config.")
print("Your agent still has full memory capabilities!\n")

try:
    # Load memory config if available
    memory_mode = "NO_MEMORY"
    if os.path.exists('memory_config.json'):
        with open('memory_config.json') as f:
            memory_cfg = json.load(f)
            memory_id = memory_cfg.get('memory_id')
            if memory_id:
                print(f"✓ Agent will use Memory ID: {memory_id} (via environment variable)")
    
    runtime.configure(
        entrypoint=entrypoint,
        agent_name=agent_name,
        execution_role=role_config["role_arn"],
        auto_create_ecr=True,
        memory_mode="NO_MEMORY",  # Memory managed via env vars, not runtime
        requirements_file="requirements.txt",
        region="us-west-2",
        authorizer_configuration=auth_config
    )
    print("\n✓ Configuration loaded")
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    sys.exit(1)

# Step 5: Invoke agent
print("\n📝 Step 5: Invoking agent...")
print("\nRequest:")
print("  Actor ID: user_001")
print("  Prompt: 'Can you look up my order ORD-001 and help me with a return?'")

payload = {
    "prompt": "Can you look up my order ORD-001 and help me with a return?",
    "actor_id": "user_001"
}

print("\n" + "="*80)
print("SENDING REQUEST TO AGENT")
print("="*80)

try:
    response = runtime.invoke(
        payload,
        bearer_token=bearer_token
    )
    
    print("\n" + "="*80)
    print("✅ AGENT RESPONSE")
    print("="*80)
    print(f"\n{response}\n")
    print("="*80)
    
    # Check if response contains expected elements
    response_lower = str(response).lower()
    
    print("\nResponse Analysis:")
    checks = {
        "Order Lookup": any(word in response_lower for word in ['ord-001', 'dell', 'xps', 'laptop', '1299']),
        "Return Eligibility": any(word in response_lower for word in ['eligible', 'return', 'days']),
        "Memory/Personalization": any(word in response_lower for word in ['email', 'preference', 'remember'])
    }
    
    for capability, found in checks.items():
        status = "✓" if found else "✗"
        print(f"  {status} {capability}: {'Detected' if found else 'Not detected'}")
    
    print("\n" + "="*80)
    print("INVOCATION COMPLETE")
    print("="*80)
    
except Exception as e:
    print("\n" + "="*80)
    print("❌ ERROR INVOKING AGENT")
    print("="*80)
    print(f"\nError: {e}")
    
    import traceback
    traceback.print_exc()
    
    print("\n" + "="*80)
    print("TROUBLESHOOTING")
    print("="*80)
    print("\n1. Check agent status:")
    print("   python3 20_check_status.py")
    print("\n2. Verify agent is in READY state")
    print("\n3. Check CloudWatch logs:")
    print(f"   aws logs tail /aws/bedrock-agentcore/runtime/{agent_name} --follow")
    print("\n4. Verify OAuth token is valid")
    print("\n5. Check that all environment variables are set correctly")
    print("="*80)
    sys.exit(1)
