#!/usr/bin/env python3
"""
Script to get CloudWatch GenAI Observability dashboard URL.
"""

# Build dashboard URL
region = "us-west-2"
dashboard_url = f"https://console.aws.amazon.com/cloudwatch/home?region={region}#gen-ai-observability/agent-core"

print("CloudWatch GenAI Observability Dashboard")
print("=" * 80)
print(f"\nDashboard URL: {dashboard_url}")
print(f"Region: {region}")
print("\nFeatures:")
print("  - Agent performance metrics")
print("  - Request traces and spans")
print("  - Session history")
print("  - Error rates and patterns")
print("  - Tool invocation details")
print("\nOpen this URL in your browser to view the dashboard")
