#!/usr/bin/env python3
"""
Script to create AgentCore Memory.

This script creates an AgentCore Memory resource with memory strategies.
"""

import json
from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager

# Define memory strategies in boto3 tagged union format
strategies = [
    {
        "summaryMemoryStrategy": {
            "name": "summary",
            "namespaces": [
                "app/{actorId}/{sessionId}/summary"
            ]
        }
    },
    {
        "userPreferenceMemoryStrategy": {
            "name": "preferences",
            "namespaces": [
                "app/{actorId}/preferences"
            ]
        }
    },
    {
        "semanticMemoryStrategy": {
            "name": "semantic",
            "namespaces": [
                "app/{actorId}/semantic"
            ]
        }
    }
]

# Create memory manager
memory_manager = MemoryManager(region_name='us-west-2')

# Create memory
print("Creating AgentCore Memory...")
memory = memory_manager.get_or_create_memory(
    name="returns_refunds_memory",
    description="Stores customer interactions, preferences, and return history",
    strategies=strategies
)

# Extract memory_id
memory_id = memory["id"]

# Save memory_id to config file
config = {
    "memory_id": memory_id,
    "name": "returns_refunds_memory",
    "region": "us-west-2"
}

with open('memory_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"✓ Memory created successfully!")
print(f"  Memory ID: {memory_id}")
print(f"✓ Configuration saved to memory_config.json")
