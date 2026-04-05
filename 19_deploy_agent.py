#!/usr/bin/env python3
"""
Script to deploy agent to AgentCore Runtime.

This script:
1. Loads all configuration files
2. Configures runtime deployment settings
3. Sets environment variables
4. Deploys to AgentCore Runtime
5. Saves agent ARN to runtime_config.json
"""

import json
import os
import sys
from bedrock_agentcore_starter_toolkit import Runtime

print("="*80)
print("DEPLOYING AGENT TO AGENTCORE RUNTIME")
print("="*80)

# Step 1: Load all configuration files
print("\n📝 Step 1: Loading configuration files...")

configs = {}

# Load Memory config
try:
    with open('memory_config.json') as f:
        configs['memory'] = json.load(f)
        print(f"✓ Memory ID: {configs['memory']['memory_id']}")
except FileNotFoundError:
    print("⚠️  memory_config.json not found - agent will run without memory")
    configs['memory'] = None

# Load Knowledge Base config
try:
    with open('kb_config.json') as f:
        configs['kb'] = json.load(f)
        print(f"✓ Knowledge Base ID: {configs['kb']['knowledge_base_id']}")
except FileNotFoundError:
    print("❌ Error: kb_config.json not found")
    print("   Run the knowledge base setup first")
    sys.exit(1)

# Load Gateway config
try:
    with open('gateway_config.json') as f:
        configs['gateway'] = json.load(f)
        print(f"✓ Gateway URL: {configs['gateway']['gateway_url']}")
except FileNotFoundError:
    print("⚠️  gateway_config.json not found - agent will run without gateway")
    configs['gateway'] = None

# Load Cognito config
try:
    with open('cognito_config.json') as f:
        configs['cognito'] = json.load(f)
        print(f"✓ Cognito Client ID: {configs['cognito']['client_id']}")
except FileNotFoundError:
    print("❌ Error: cognito_config.json not found")
    print("   Run 08_create_cognito.py first")
    sys.exit(1)

# Load Runtime Execution Role config
try:
    with open('runtime_execution_role_config.json') as f:
        configs['role'] = json.load(f)
        print(f"✓ Execution Role ARN: {configs['role']['role_arn']}")
except FileNotFoundError:
    print("❌ Error: runtime_execution_role_config.json not found")
    print("   Run 16_create_runtime_role.py first")
    sys.exit(1)

# Step 2: Initialize Runtime
print("\n📝 Step 2: Initializing AgentCore Runtime...")
runtime = Runtime()
print("✓ Runtime initialized")

# Step 3: Build authorizer configuration
print("\n📝 Step 3: Building authentication configuration...")
auth_config = {
    "customJWTAuthorizer": {
        "allowedClients": [configs['cognito']["client_id"]],
        "discoveryUrl": configs['cognito']["discovery_url"]
    }
}
print("✓ Auth config created with Cognito JWT authorizer")

# Step 4: Configure runtime deployment
print("\n📝 Step 4: Configuring runtime deployment settings...")
print("   Entrypoint: 17_runtime_agent.py")
print("   Agent name: returns_refunds_agent")
print("   Region: us-west-2")

try:
    runtime.configure(
        entrypoint="17_runtime_agent.py",
        agent_name="returns_refunds_agent",
        execution_role=configs['role']["role_arn"],
        auto_create_ecr=True,
        memory_mode="NO_MEMORY",  # Memory is handled via env vars
        requirements_file="requirements.txt",
        region="us-west-2",
        authorizer_configuration=auth_config
    )
    print("✓ Runtime configured successfully")
    print("  Configuration saved to .bedrock_agentcore.yaml")
except Exception as e:
    print(f"❌ Error configuring runtime: {e}")
    sys.exit(1)

# Step 5: Build environment variables
print("\n📝 Step 5: Building environment variables...")

env_vars = {}

# Knowledge Base (required)
env_vars["KNOWLEDGE_BASE_ID"] = configs['kb']["knowledge_base_id"]
print(f"  ✓ KNOWLEDGE_BASE_ID: {env_vars['KNOWLEDGE_BASE_ID']}")

# Memory (optional)
if configs['memory']:
    env_vars["MEMORY_ID"] = configs['memory']["memory_id"]
    print(f"  ✓ MEMORY_ID: {env_vars['MEMORY_ID']}")
else:
    print("  ⚠️  MEMORY_ID: Not set")

# Gateway (optional)
if configs['gateway']:
    env_vars["GATEWAY_URL"] = configs['gateway']["gateway_url"]
    print(f"  ✓ GATEWAY_URL: {env_vars['GATEWAY_URL']}")
else:
    print("  ⚠️  GATEWAY_URL: Not set")

# Cognito credentials (required for gateway)
env_vars["COGNITO_CLIENT_ID"] = configs['cognito']["client_id"]
env_vars["COGNITO_CLIENT_SECRET"] = configs['cognito']["client_secret"]
env_vars["COGNITO_DISCOVERY_URL"] = configs['cognito']["discovery_url"]
print(f"  ✓ COGNITO_CLIENT_ID: {env_vars['COGNITO_CLIENT_ID']}")
print(f"  ✓ COGNITO_CLIENT_SECRET: ***")
print(f"  ✓ COGNITO_DISCOVERY_URL: {env_vars['COGNITO_DISCOVERY_URL']}")

# Step 6: Launch to runtime
print("\n" + "="*80)
print("LAUNCHING AGENT TO AGENTCORE RUNTIME")
print("="*80)
print("\nThis process will:")
print("  1. Create CodeBuild project")
print("  2. Build Docker container from your agent code")
print("  3. Push container to Amazon ECR")
print("  4. Deploy to AgentCore Runtime")
print("\n⏱️  Expected time: 5-10 minutes")
print("\n☕ Grab a coffee while the deployment runs...")
print("="*80 + "\n")

try:
    launch_result = runtime.launch(
        env_vars=env_vars,
        auto_update_on_conflict=True
    )
    
    agent_arn = launch_result.agent_arn
    
    print("\n" + "="*80)
    print("✅ DEPLOYMENT INITIATED SUCCESSFULLY")
    print("="*80)
    print(f"\nAgent ARN: {agent_arn}")
    
except Exception as e:
    print(f"\n❌ Error launching agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 7: Save runtime configuration
print("\n📝 Step 7: Saving runtime configuration...")

runtime_config = {
    "agent_arn": agent_arn,
    "agent_name": "returns_refunds_agent",
    "region": "us-west-2",
    "entrypoint": "17_runtime_agent.py"
}

# Add optional configs
if configs['memory']:
    runtime_config["memory_id"] = configs['memory']["memory_id"]

if configs['gateway']:
    runtime_config["gateway_url"] = configs['gateway']["gateway_url"]
    runtime_config["gateway_id"] = configs['gateway']["gateway_id"]

runtime_config["knowledge_base_id"] = configs['kb']["knowledge_base_id"]

with open('runtime_config.json', 'w') as f:
    json.dump(runtime_config, f, indent=2)

print("✓ Configuration saved to runtime_config.json")

# Summary
print("\n" + "="*80)
print("DEPLOYMENT SUMMARY")
print("="*80)
print(f"\nAgent Name: returns_refunds_agent")
print(f"Agent ARN: {agent_arn}")
print(f"Region: us-west-2")
print(f"\nIntegrations:")
print(f"  ✓ Knowledge Base: {configs['kb']['knowledge_base_id']}")
if configs['memory']:
    print(f"  ✓ Memory: {configs['memory']['memory_id']}")
else:
    print(f"  ✗ Memory: Not configured")
if configs['gateway']:
    print(f"  ✓ Gateway: {configs['gateway']['gateway_id']}")
else:
    print(f"  ✗ Gateway: Not configured")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("\n1. Monitor deployment status:")
print("   The agent is being built and deployed (5-10 minutes)")
print("   Check status with: agentcore status")
print("\n2. Wait for status to show 'READY'")
print("   The agent must be in READY state before invocation")
print("\n3. Once READY, test your agent:")
print("   agentcore invoke '{\"prompt\": \"Hello!\"}'")
print("\n4. View logs:")
print("   Check CloudWatch logs for agent execution details")
print("="*80)
