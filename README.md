# Returns & Refunds Strands Agent - Production Deployment

A production-ready AI agent built with Strands framework for handling customer returns and refunds, deployed on AWS AgentCore Runtime with full monitoring and debugging capabilities.

## Overview

This agent provides:
- Custom tools for checking return eligibility and calculating refunds
- Memory to remember customers across sessions
- External API integration via gateway for order lookups
- Knowledge base access for return policy information
- Production deployment on AWS AgentCore Runtime
- Monitoring and observability with CloudWatch

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentCore Runtime                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │         17_runtime_agent.py                        │     │
│  │  - Custom Tools (eligibility, refunds, formatting) │     │
│  │  - Bedrock Model (Claude Sonnet 4.5)               │     │
│  └────────────────────────────────────────────────────┘     │
│           │              │              │                   │
│           ▼              ▼              ▼                   │
│    ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│    │  Memory  │   │ Gateway  │   │Knowledge │               │
│    │          │   │          │   │   Base   │               │
│    └──────────┘   └──────────┘   └──────────┘               │
│                         │                                   │
│                         ▼                                   │
│                  ┌──────────┐                               │
│                  │  Lambda  │                               │
│                  │ (Orders) │                               │
│                  └──────────┘                               │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
                  ┌──────────┐
                  │ Cognito  │
                  │  (Auth)  │
                  └──────────┘
```

## Project Structure

### Core Agent
- **17_runtime_agent.py** - Production-ready agent with BedrockAgentCoreApp entrypoint (this is what gets deployed to production)

### Infrastructure Setup Scripts
- **03_create_memory.py** - Creates AgentCore Memory with 3 strategies (summary, preferences, semantic)
- **04_seed_memory.py** - Seeds memory with sample customer conversations (optional, for testing)
- **08_create_cognito.py** - Creates Cognito User Pool with OAuth2 authentication
- **09_create_gateway_role.py** - Creates IAM role for Gateway to invoke Lambda
- **10_create_lambda.py** - Creates Lambda function with mock order database
- **11_create_gateway.py** - Creates AgentCore Gateway with Cognito JWT auth
- **12_add_lambda_to_gateway.py** - Adds Lambda function as a gateway target (makes tools available)
- **16_create_runtime_role.py** - Creates IAM execution role for AgentCore Runtime

### Deployment & Operations Scripts
- **19_deploy_agent.py** - Deploys agent to AgentCore Runtime
- **20_check_status.py** - Checks deployment status
- **21_invoke_agent.py** - Tests production agent
- **22_get_dashboard.py** - Accesses monitoring dashboard
- **23_get_logs_info.py** - Views CloudWatch logs for debugging
- **24_clean_up_aws.py** - Safely deletes all AWS resources to avoid ongoing costs

### Configuration Files
- **requirements.txt** - Python dependencies
- **Dockerfile** - Container configuration
- **.dockerignore** - Docker build exclusions
- **.bedrock_agentcore.yaml** - AgentCore deployment configuration

### Generated Configuration Files
These files are created automatically by the setup scripts:
- **kb_config.json** - Knowledge base ID
- **memory_config.json** - Memory ID and configuration
- **gateway_config.json** - Gateway URL and ID
- **cognito_config.json** - Cognito authentication credentials
- **runtime_execution_role_config.json** - IAM role ARN
- **lambda_config.json** - Lambda function details
- **gateway_role_config.json** - Gateway IAM role details
- **runtime_config.json** - Runtime deployment details (created after deployment)

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Python 3.10+** installed
4. **Docker** installed (for containerization)
5. **Knowledge Base** already created in Amazon Bedrock

### Required AWS Permissions

Your AWS credentials need permissions for:
- IAM (create roles and policies)
- Lambda (create and invoke functions)
- Cognito (create user pools and clients)
- Bedrock AgentCore (create memory, gateway, runtime)
- ECR (create repositories and push images)
- CloudWatch (logs and metrics)
- CodeBuild (for container builds)

## Installation

1. Clone or download this project

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure you have a Knowledge Base created in Amazon Bedrock and note its ID

## Deployment Guide

### Important: What Gets Deployed

The deployment process packages and deploys:
- **17_runtime_agent.py** - Your main agent code (the entrypoint)
- **requirements.txt** - All Python dependencies
- **Dockerfile** - Container configuration
- **Configuration files** - Loaded as environment variables

The `19_deploy_agent.py` script orchestrates this deployment by building a Docker container with all these components and deploying it to AgentCore Runtime.

### Step 1: Create Knowledge Base Configuration

Create `kb_config.json` with your Knowledge Base ID:
```json
{
  "knowledge_base_id": "YOUR_KB_ID_HERE",
  "region": "us-west-2"
}
```

### Step 2: Set Up Infrastructure

Run the infrastructure setup scripts in order:

```bash
# 1. Create AgentCore Memory
python 03_create_memory.py

# 2. (Optional) Seed memory with sample customer data for testing
python 04_seed_memory.py

# 3. Create Cognito User Pool for authentication
python 08_create_cognito.py

# 4. Create IAM role for Gateway
python 09_create_gateway_role.py

# 5. Create Lambda function for order lookup
python 10_create_lambda.py

# 6. Create AgentCore Gateway
python 11_create_gateway.py

# 7. Add Lambda as a gateway target (makes lookup_order tool available)
python 12_add_lambda_to_gateway.py

# 8. Create Runtime execution role
python 16_create_runtime_role.py
```

Each script will:
- Create the necessary AWS resources
- Save configuration to JSON files
- Display success messages with resource IDs

**Note:** These scripts are idempotent where possible - if a resource already exists, they'll retrieve and use it.

**Optional Step 2:** `04_seed_memory.py` adds sample customer conversations to memory:
- Customer preference: Email notifications
- Previous interaction: Returned a defective laptop
- Conversation history about return policies
- Useful for testing memory recall capabilities
- Can be skipped for production if you want memory to start empty

**Important:** Step 7 (`12_add_lambda_to_gateway.py`) is critical - it connects the Lambda function to the Gateway, making the `lookup_order` tool available to your agent. Without this step, the gateway will exist but have no tools.

### Step 3: Deploy Agent to Production

Deploy the agent to AgentCore Runtime:

```bash
python 19_deploy_agent.py
```

This script will:
1. Load all configuration files
2. Configure runtime deployment settings using `17_runtime_agent.py` as the entrypoint
3. Build Docker container with the agent code
4. Push container to Amazon ECR
5. Deploy to AgentCore Runtime

**What gets deployed:**
- `17_runtime_agent.py` - Your production agent code
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- All configuration JSON files (as environment variables)

**Expected time:** 5-10 minutes

### Step 4: Check Deployment Status

Monitor the deployment:

```bash
python 20_check_status.py
```

Wait until status shows **READY** before proceeding.

### Step 5: Test Production Agent

Once deployed and ready, test the agent:

```bash
python 21_invoke_agent.py
```

This will send a test query to your production agent and display the response.

## Monitoring & Debugging

### View Monitoring Dashboard

Access CloudWatch GenAI Observability dashboard:

```bash
python 22_get_dashboard.py
```

This provides:
- Request metrics
- Latency statistics
- Error rates
- Token usage

### View Logs

Access CloudWatch logs for debugging:

```bash
python 23_get_logs_info.py
```

This shows:
- Agent execution logs
- Tool invocations
- Error traces
- Performance metrics

## Agent Capabilities

### Custom Tools

1. **check_return_eligibility** - Checks if an item is eligible for return based on purchase date and category
2. **calculate_refund_amount** - Calculates refund amount based on item condition and return reason
3. **format_policy_response** - Formats policy information in a customer-friendly way

### Integrated Tools

1. **retrieve** - Accesses Knowledge Base for return policy documents
2. **current_time** - Gets current date/time
3. **lookup_order** - Looks up order details via Gateway/Lambda (order IDs: ORD-001, ORD-002, ORD-003)

### Memory Strategies

1. **Summary** - Conversation context per session
2. **Preferences** - Customer preferences across sessions
3. **Semantic** - Factual details about customers

## Configuration Details

### Memory Configuration
- **Namespace:** `app/{actorId}/{sessionId}/summary`, `app/{actorId}/preferences`, `app/{actorId}/semantic`
- **Strategies:** Summary, User Preference, Semantic
- **Region:** us-west-2

### Gateway Configuration
- **Protocol:** MCP (Model Context Protocol)
- **Authentication:** Custom JWT (Cognito)
- **OAuth Scopes:** gateway-api/read, gateway-api/write
- **Auth Flow:** client_credentials (machine-to-machine)

### Lambda Function
- **Runtime:** Python 3.10
- **Handler:** lambda_function.lambda_handler
- **Timeout:** 30 seconds
- **Memory:** 128 MB
- **Sample Orders:** ORD-001, ORD-002, ORD-003

### Runtime Configuration
- **Model:** Claude Sonnet 4.5 (us.anthropic.claude-sonnet-4-5-20250929-v1:0)
- **Temperature:** 0.3
- **Region:** us-west-2
- **Platform:** linux/arm64
- **Observability:** Enabled (CloudWatch)

## Environment Variables

The agent uses these environment variables (set automatically during deployment):

- `KNOWLEDGE_BASE_ID` - Knowledge base for return policies
- `MEMORY_ID` - AgentCore Memory ID
- `GATEWAY_URL` - Gateway endpoint URL
- `COGNITO_CLIENT_ID` - Cognito client ID
- `COGNITO_CLIENT_SECRET` - Cognito client secret
- `COGNITO_DISCOVERY_URL` - Cognito OIDC discovery URL

## Troubleshooting

### Deployment Fails

1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify all config files exist in the project directory
3. Check CloudWatch logs for detailed error messages
4. Ensure IAM permissions are sufficient

### Agent Not Responding

1. Check status: `python 20_check_status.py`
2. Verify status is READY (not CREATING or FAILED)
3. Check CloudWatch logs: `python 23_get_logs_info.py`
4. Verify all integrations (Memory, Gateway, Knowledge Base) are configured

### Gateway Tools Not Working

1. Verify Cognito configuration in `cognito_config.json`
2. Check Gateway status in AWS Console
3. Verify Lambda function is active and has correct permissions
4. Check Gateway role has Lambda invoke permissions

### Memory Not Persisting

1. Verify Memory ID in `memory_config.json`
2. Check Runtime execution role has Memory permissions
3. Verify actor_id and session_id are consistent across invocations

## Cost Considerations

Running this agent incurs costs for:
- **AgentCore Runtime** - Per-request pricing
- **Bedrock Model** - Per-token pricing (Claude Sonnet 4.5)
- **AgentCore Memory** - Storage and retrieval
- **AgentCore Gateway** - Per-request pricing
- **Lambda** - Per-invocation pricing
- **Cognito** - Per-MAU pricing
- **CloudWatch** - Logs and metrics storage
- **ECR** - Container image storage

## Security Best Practices

1. **Credentials** - Never commit `cognito_config.json` or other files with secrets to version control
2. **IAM Roles** - Use least-privilege permissions
3. **Authentication** - Gateway uses OAuth2 with JWT tokens
4. **Network** - Runtime uses PUBLIC network mode (consider VPC for production)
5. **Secrets** - Consider using AWS Secrets Manager for sensitive configuration

## Cleanup

To remove all AWS resources and avoid ongoing costs, use the automated cleanup script:

```bash
python 24_clean_up_aws.py
```

This script will safely delete all resources in the following order:

1. **AgentCore Runtime agent** - Stops and removes the deployed agent
2. **AgentCore Gateway and targets** - Removes gateway and Lambda integrations
3. **AgentCore Memory** - Deletes memory storage
4. **Lambda function and IAM role** - Removes order lookup function
5. **Cognito User Pool** - Deletes authentication (domain, clients, pool)
6. **Gateway IAM role** - Removes gateway execution role
7. **Runtime execution IAM role and policy** - Removes runtime permissions
8. **ECR repository** - Deletes container images

**Features:**
- 5-second warning before deletion starts
- Shows all resources that will be deleted
- Handles missing resources gracefully (safe to re-run)
- Provides detailed summary of what was deleted, skipped, or failed
- Idempotent - safe to run multiple times

**After cleanup:**
- All AWS resources are removed
- No ongoing costs
- Configuration JSON files remain (can be manually deleted)
- You can re-deploy by running the setup scripts again

**Manual cleanup alternative:**
If you prefer to delete resources manually or if the script fails, you can delete resources through the AWS Console in this order:
1. AgentCore Runtime agent
2. AgentCore Gateway
3. AgentCore Memory
4. Lambda function
5. Cognito User Pool
6. IAM roles and policies
7. ECR repository
8. CloudWatch log groups

## Support

For issues related to:
- **Strands Framework** - Check Strands documentation
- **AgentCore Runtime** - Check AWS Bedrock AgentCore documentation
- **AWS Services** - Check AWS documentation or support

## License

This project is provided as-is for educational and production use.
