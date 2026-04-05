#!/usr/bin/env python3
"""
Script to seed AgentCore Memory with sample customer conversations.

This script adds sample conversations to demonstrate memory capabilities.
"""

import json
import time

try:
    from bedrock_agentcore.memory import MemoryClient
except ImportError:
    print("✗ Error: bedrock_agentcore package not found")
    print("  Install with: pip install bedrock-agentcore")
    exit(1)

# Load memory_id from config
with open('memory_config.json') as f:
    config = json.load(f)
    memory_id = config['memory_id']

print(f"Using Memory ID: {memory_id}")
print(f"Customer ID: user_001")
print("="*80)

# Create memory client
memory_client = MemoryClient(region_name='us-west-2')

# Conversation 1: Customer mentions email preference and previous laptop return
print("\n📝 Storing Conversation 1: Email preference and laptop return history")
conversation_1 = [
    ("Hello, I have a question about my recent order", "USER"),
    ("Hello! I'd be happy to help you with your order. What can I assist you with?", "ASSISTANT"),
    ("I prefer to receive updates via email rather than text messages. Also, I previously returned a defective laptop last month and want to make sure this order doesn't have the same issues.", "USER"),
    ("Thank you for letting me know your preference for email notifications. I've noted that. I can see you had a previous return for a defective laptop. I'm sorry you experienced that issue. Rest assured, we'll make sure your current order meets your expectations. What specific concerns do you have about this order?", "ASSISTANT"),
    ("Just wanted to confirm the return policy in case I need it. The laptop I returned was defective and the process was smooth, but I want to be prepared.", "USER"),
    ("Absolutely! For electronics like laptops, you have a 30-day return window from delivery. Since your previous laptop was defective, you received a full refund. The same policy applies to your current order. If there are any issues, you can initiate a return through your order history, and we'll send you email notifications throughout the process as you prefer.", "ASSISTANT")
]

memory_client.create_event(
    memory_id=memory_id,
    actor_id="user_001",
    session_id="session_001",
    messages=conversation_1
)
print(f"✓ Stored {len(conversation_1)} messages from Conversation 1")

# Conversation 2: Customer asks about return windows for electronics
print("\n📝 Storing Conversation 2: Return window inquiry for electronics")
conversation_2 = [
    ("Hi, I'm thinking about buying some electronics and want to understand the return policy first", "USER"),
    ("Great question! I'm happy to explain our return policy for electronics. What specific items are you considering?", "ASSISTANT"),
    ("I'm looking at tablets and headphones. How long do I have to return them if they don't work out?", "USER"),
    ("For most electronics including tablets and headphones, you have a 30-day return window from the delivery date. The items should be in their original condition with all accessories, packaging, and documentation. If the item is defective, you'll receive a full refund regardless of condition.", "ASSISTANT"),
    ("That's helpful! And what if I just change my mind about the purchase?", "USER"),
    ("If you change your mind, you can still return within the 30-day window. The refund amount may vary based on the item's condition - items in new, unopened condition receive 100% refund, while opened items typically receive 90% of the purchase price. Since I see you prefer email notifications, you'll receive updates via email throughout the return process.", "ASSISTANT")
]

memory_client.create_event(
    memory_id=memory_id,
    actor_id="user_001",
    session_id="session_002",
    messages=conversation_2
)
print(f"✓ Stored {len(conversation_2)} messages from Conversation 2")

# Wait for memory processing
print("\n" + "="*80)
print("⏳ Waiting 30 seconds for memory processing...")
print("   Memory system is extracting:")
print("   - User preferences (email notifications)")
print("   - Semantic facts (previous laptop return, return policies)")
print("   - Conversation summaries")
print("="*80)

time.sleep(30)

print("\n✅ Memory seeding complete!")
print(f"   Total conversations stored: 2")
print(f"   Total messages: {len(conversation_1) + len(conversation_2)}")
print(f"   Customer ID: user_001")
print("\nMemory should now contain:")
print("  • Preference: Customer prefers email notifications")
print("  • Fact: Customer previously returned a defective laptop")
print("  • Fact: Customer inquired about return windows for electronics")
print("  • Summary: Conversations about return policies and preferences")
