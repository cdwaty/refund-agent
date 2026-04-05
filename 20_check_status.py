#!/usr/bin/env python3
"""
Script to check AgentCore Runtime deployment status.

This script monitors the deployment and displays current state.
"""

import json
import os
import sys
import time
from bedrock_agentcore_starter_toolkit import Runtime

print("="*80)
print("CHECKING AGENTCORE RUNTIME STATUS")
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

# Load other required configs
try:
    with open('runtime_execution_role_config.json') as f:
        role_config = json.load(f)
except FileNotFoundError:
    print("\n❌ Error: runtime_execution_role_config.json not found")
    sys.exit(1)

try:
    with open('cognito_config.json') as f:
        cognito_config = json.load(f)
except FileNotFoundError:
    print("\n❌ Error: cognito_config.json not found")
    sys.exit(1)

# Check if .bedrock_agentcore.yaml exists
if not os.path.exists('.bedrock_agentcore.yaml'):
    print("\n❌ Error: .bedrock_agentcore.yaml not found")
    print("   Run 19_deploy_agent.py first")
    sys.exit(1)

# Load YAML config
import yaml
with open('.bedrock_agentcore.yaml') as f:
    yaml_config = yaml.safe_load(f)

default_agent = yaml_config.get('default_agent')
agent_config = yaml_config.get('agents', {}).get(default_agent, {})
entrypoint = agent_config.get('entrypoint', '17_runtime_agent.py')

# Initialize Runtime
print("\n📝 Initializing Runtime SDK...")
runtime = Runtime()

# Build authorizer configuration
auth_config = {
    "customJWTAuthorizer": {
        "allowedClients": [cognito_config["client_id"]],
        "discoveryUrl": cognito_config["discovery_url"]
    }
}

# Configure runtime (to load existing configuration)
print("📝 Loading runtime configuration...")
try:
    runtime.configure(
        entrypoint=entrypoint,
        agent_name=agent_name,
        execution_role=role_config["role_arn"],
        auto_create_ecr=True,
        memory_mode="NO_MEMORY",
        requirements_file="requirements.txt",
        region="us-west-2",
        authorizer_configuration=auth_config
    )
    print("✓ Configuration loaded")
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    sys.exit(1)

# Check status with optional monitoring
print("\n" + "="*80)
print("DEPLOYMENT STATUS")
print("="*80)

def check_status():
    """Check and display current status"""
    try:
        status_response = runtime.status()
        endpoint = status_response.endpoint
        status = endpoint.get("status", "UNKNOWN")
        
        return status, endpoint
    except Exception as e:
        print(f"\n❌ Error checking status: {e}")
        return None, None

# Initial status check
status, endpoint = check_status()

if status is None:
    sys.exit(1)

# Display status
print(f"\nCurrent Status: {status}")

if endpoint:
    print(f"\nEndpoint Details:")
    print(f"  Status: {endpoint.get('status', 'N/A')}")
    if 'endpointUrl' in endpoint:
        print(f"  URL: {endpoint['endpointUrl']}")
    if 'createdAt' in endpoint:
        print(f"  Created: {endpoint['createdAt']}")
    if 'updatedAt' in endpoint:
        print(f"  Updated: {endpoint['updatedAt']}")

# Status-specific messages
print("\n" + "="*80)

if status == "READY":
    print("✅ AGENT IS READY")
    print("="*80)
    print("\nYour agent is deployed and ready to receive requests!")
    print("\nNext Steps:")
    print("  1. Test your agent:")
    print("     agentcore invoke '{\"prompt\": \"Hello!\"}'")
    print("\n  2. View logs:")
    print(f"     aws logs tail /aws/bedrock-agentcore/runtime/{agent_name} --follow")
    print("\n  3. Monitor performance:")
    print("     Check CloudWatch metrics for request counts and latency")
    
elif status in ["CREATING", "UPDATING"]:
    print("⏳ DEPLOYMENT IN PROGRESS")
    print("="*80)
    print(f"\nThe agent is currently {status.lower()}...")
    print("This is normal and can take 5-10 minutes.")
    print("\nOptions:")
    print("  1. Wait and check again:")
    print("     python3 20_check_status.py")
    print("\n  2. Monitor continuously (checks every 30 seconds):")
    print("     Run this script with --monitor flag")
    
    # Ask if user wants to monitor
    if '--monitor' in sys.argv or '-m' in sys.argv:
        print("\n" + "="*80)
        print("MONITORING MODE - Checking every 30 seconds")
        print("Press Ctrl+C to stop")
        print("="*80)
        
        try:
            while status in ["CREATING", "UPDATING"]:
                time.sleep(30)
                print(f"\n[{time.strftime('%H:%M:%S')}] Checking status...")
                status, endpoint = check_status()
                
                if status is None:
                    break
                    
                print(f"Status: {status}")
                
                if status == "READY":
                    print("\n" + "="*80)
                    print("✅ AGENT IS NOW READY!")
                    print("="*80)
                    break
                elif status in ["CREATE_FAILED", "UPDATE_FAILED"]:
                    print("\n" + "="*80)
                    print("❌ DEPLOYMENT FAILED")
                    print("="*80)
                    break
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
    
elif status in ["CREATE_FAILED", "UPDATE_FAILED"]:
    print("❌ DEPLOYMENT FAILED")
    print("="*80)
    print("\nThe deployment encountered an error.")
    print("\nTroubleshooting Steps:")
    print("  1. Check CloudWatch logs:")
    print(f"     aws logs tail /aws/bedrock-agentcore/runtime/{agent_name}")
    print("\n  2. Common issues:")
    print("     - IAM role permissions")
    print("     - Container build errors")
    print("     - Invalid environment variables")
    print("     - Memory or gateway configuration issues")
    print("\n  3. Try redeploying:")
    print("     python3 19_deploy_agent.py")
    
elif status == "DELETING":
    print("🗑️  AGENT IS BEING DELETED")
    print("="*80)
    print("\nThe agent is being removed from runtime.")
    
else:
    print(f"⚠️  UNKNOWN STATUS: {status}")
    print("="*80)
    print("\nThis is an unexpected status.")
    print("Check the AWS console or CloudWatch logs for details.")

print("="*80)
