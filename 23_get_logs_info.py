#!/usr/bin/env python3
"""
Script to get CloudWatch log group information for agent logs.
"""

import json
from datetime import datetime

# Load configuration
with open('runtime_config.json') as f:
    runtime_config = json.load(f)

agent_arn = runtime_config["agent_arn"]

# Extract agent ID from ARN
agent_id = agent_arn.split('/')[-1]

# Build log group name
log_group = f"/aws/bedrock-agentcore/runtimes/{agent_id}-DEFAULT"

# Get current date for log stream prefix
current_date = datetime.now().strftime("%Y/%m/%d")

# Build CLI commands
tail_command = f'aws logs tail {log_group} --log-stream-name-prefix "{current_date}/[runtime-logs]" --follow'
recent_command = f'aws logs tail {log_group} --log-stream-name-prefix "{current_date}/[runtime-logs]" --since 1h'

print("CloudWatch Logs Information")
print("=" * 80)
print(f"\nAgent ARN: {agent_arn}")
print(f"Agent ID: {agent_id}")
print(f"Log Group: {log_group}")
print(f"Region: us-west-2")
print("\nCLI Commands:")
print(f"\nTail logs (real-time):")
print(f"  {tail_command}")
print(f"\nView recent logs (last hour):")
print(f"  {recent_command}")
