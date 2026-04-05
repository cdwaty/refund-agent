#!/usr/bin/env python3
"""
Script to safely delete all AWS resources created for the returns agent.

This script will delete:
1. AgentCore Runtime agent
2. AgentCore Gateway and targets
3. AgentCore Memory resource
4. Lambda function and its IAM role
5. Cognito User Pool (with domain and clients)
6. IAM roles (gateway and runtime execution roles)
7. ECR repository

Includes a 5-second warning before deletion.
"""

import json
import os
import sys
import time
import boto3
from botocore.exceptions import ClientError

REGION = "us-west-2"

print("="*80)
print("AWS RESOURCE CLEANUP SCRIPT")
print("="*80)

# Load configurations
configs = {}
config_files = [
    'runtime_config.json',
    'gateway_config.json', 
    'memory_config.json',
    'lambda_config.json',
    'cognito_config.json',
    'gateway_role_config.json',
    'runtime_execution_role_config.json'
]

print("\n📝 Loading configurations...")
for config_file in config_files:
    try:
        with open(config_file) as f:
            configs[config_file] = json.load(f)
            print(f"  ✓ Loaded {config_file}")
    except FileNotFoundError:
        print(f"  ⚠️  {config_file} not found (may already be deleted)")
        configs[config_file] = {}

# Display what will be deleted
print("\n" + "="*80)
print("RESOURCES TO BE DELETED")
print("="*80)

resources_to_delete = []

if configs.get('runtime_config.json', {}).get('agent_arn'):
    resources_to_delete.append(f"Runtime Agent: {configs['runtime_config.json']['agent_name']}")
    
if configs.get('gateway_config.json', {}).get('gateway_id'):
    gateway_config = configs['gateway_config.json']
    resources_to_delete.append(f"Gateway: {gateway_config.get('name', 'ReturnsRefundsGateway')}")
    if gateway_config.get('targets'):
        for target in gateway_config['targets']:
            resources_to_delete.append(f"  └─ Target: {target['target_name']}")

if configs.get('memory_config.json', {}).get('memory_id'):
    resources_to_delete.append(f"Memory: {configs['memory_config.json']['name']}")

if configs.get('lambda_config.json', {}).get('function_arn'):
    resources_to_delete.append(f"Lambda: {configs['lambda_config.json']['function_name']}")
    if configs['lambda_config.json'].get('lambda_role_arn'):
        resources_to_delete.append(f"  └─ Lambda IAM Role")

if configs.get('cognito_config.json', {}).get('user_pool_id'):
    resources_to_delete.append(f"Cognito User Pool: {configs['cognito_config.json']['user_pool_id']}")
    resources_to_delete.append(f"  └─ Domain: {configs['cognito_config.json'].get('domain_prefix', 'N/A')}")
    resources_to_delete.append(f"  └─ App Client: {configs['cognito_config.json'].get('client_id', 'N/A')}")

if configs.get('gateway_role_config.json', {}).get('role_arn'):
    resources_to_delete.append(f"Gateway IAM Role: {configs['gateway_role_config.json']['role_name']}")

if configs.get('runtime_execution_role_config.json', {}).get('role_arn'):
    runtime_role = configs['runtime_execution_role_config.json']
    resources_to_delete.append(f"Runtime IAM Role: {runtime_role['role_name']}")
    if runtime_role.get('policy_arn'):
        resources_to_delete.append(f"  └─ IAM Policy: {runtime_role['policy_name']}")

# Check for ECR repository
if configs.get('runtime_config.json', {}).get('agent_name'):
    agent_name = configs['runtime_config.json']['agent_name']
    resources_to_delete.append(f"ECR Repository: {agent_name} (if exists)")

if not resources_to_delete:
    print("\n✓ No resources found to delete. Everything is already clean!")
    sys.exit(0)

for resource in resources_to_delete:
    print(f"  • {resource}")

# Warning countdown
print("\n" + "="*80)
print("⚠️  WARNING: This will permanently delete all resources listed above!")
print("="*80)
print("\nStarting deletion in:")
for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)
print("\n🗑️  Starting cleanup...\n")

# Initialize boto3 clients
iam_client = boto3.client('iam', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
cognito_client = boto3.client('cognito-idp', region_name=REGION)
ecr_client = boto3.client('ecr', region_name=REGION)
agentcore_client = boto3.client('bedrock-agentcore-control', region_name=REGION)

deletion_summary = {
    'success': [],
    'failed': [],
    'skipped': []
}

# ============================================================================
# 1. DELETE RUNTIME AGENT
# ============================================================================
print("="*80)
print("STEP 1: Deleting AgentCore Runtime Agent")
print("="*80)

runtime_config = configs.get('runtime_config.json', {})
if runtime_config.get('agent_arn'):
    try:
        agent_name = runtime_config['agent_name']
        print(f"Deleting runtime agent: {agent_name}...")
        
        # Extract agent runtime ID from ARN
        agent_runtime_id = runtime_config['agent_arn'].split('/')[-1]
        
        agentcore_client.delete_agent_runtime(
            agentRuntimeId=agent_runtime_id
        )
        
        print(f"✓ Runtime agent deleted: {agent_name}")
        deletion_summary['success'].append(f"Runtime Agent: {agent_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"⚠️  Runtime agent not found (may already be deleted)")
            deletion_summary['skipped'].append(f"Runtime Agent: {agent_name}")
        else:
            print(f"❌ Error deleting runtime agent: {e}")
            deletion_summary['failed'].append(f"Runtime Agent: {agent_name}")
    except Exception as e:
        print(f"❌ Error deleting runtime agent: {e}")
        deletion_summary['failed'].append(f"Runtime Agent: {agent_name}")
else:
    print("⚠️  No runtime agent configured")
    deletion_summary['skipped'].append("Runtime Agent")

# ============================================================================
# 2. DELETE GATEWAY AND TARGETS
# ============================================================================
print("\n" + "="*80)
print("STEP 2: Deleting AgentCore Gateway and Targets")
print("="*80)

gateway_config = configs.get('gateway_config.json', {})
if gateway_config.get('gateway_id'):
    gateway_id = gateway_config['gateway_id']
    
    # Delete targets first
    if gateway_config.get('targets'):
        for target in gateway_config['targets']:
            try:
                target_id = target['target_id']
                target_name = target['target_name']
                print(f"Deleting gateway target: {target_name}...")
                
                agentcore_client.delete_gateway_target(
                    gatewayIdentifier=gateway_id,
                    targetId=target_id
                )
                
                print(f"✓ Gateway target deleted: {target_name}")
                deletion_summary['success'].append(f"Gateway Target: {target_name}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    print(f"⚠️  Target not found (may already be deleted)")
                    deletion_summary['skipped'].append(f"Gateway Target: {target_name}")
                else:
                    print(f"❌ Error deleting target: {e}")
                    deletion_summary['failed'].append(f"Gateway Target: {target_name}")
            except Exception as e:
                print(f"❌ Error deleting target: {e}")
                deletion_summary['failed'].append(f"Gateway Target: {target_name}")
    
    # Delete gateway
    try:
        gateway_name = gateway_config.get('name', 'ReturnsRefundsGateway')
        print(f"\nDeleting gateway: {gateway_name}...")
        
        agentcore_client.delete_gateway(
            gatewayIdentifier=gateway_id
        )
        
        print(f"✓ Gateway deleted: {gateway_name}")
        deletion_summary['success'].append(f"Gateway: {gateway_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"⚠️  Gateway not found (may already be deleted)")
            deletion_summary['skipped'].append(f"Gateway: {gateway_name}")
        else:
            print(f"❌ Error deleting gateway: {e}")
            deletion_summary['failed'].append(f"Gateway: {gateway_name}")
    except Exception as e:
        print(f"❌ Error deleting gateway: {e}")
        deletion_summary['failed'].append(f"Gateway: {gateway_name}")
else:
    print("⚠️  No gateway configured")
    deletion_summary['skipped'].append("Gateway")

# ============================================================================
# 3. DELETE MEMORY RESOURCE
# ============================================================================
print("\n" + "="*80)
print("STEP 3: Deleting AgentCore Memory")
print("="*80)

memory_config = configs.get('memory_config.json', {})
if memory_config.get('memory_id'):
    try:
        memory_id = memory_config['memory_id']
        memory_name = memory_config['name']
        print(f"Deleting memory: {memory_name}...")
        
        agentcore_client.delete_memory(
            memoryId=memory_id
        )
        
        print(f"✓ Memory deleted: {memory_name}")
        deletion_summary['success'].append(f"Memory: {memory_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"⚠️  Memory not found (may already be deleted)")
            deletion_summary['skipped'].append(f"Memory: {memory_name}")
        else:
            print(f"❌ Error deleting memory: {e}")
            deletion_summary['failed'].append(f"Memory: {memory_name}")
    except Exception as e:
        print(f"❌ Error deleting memory: {e}")
        deletion_summary['failed'].append(f"Memory: {memory_name}")
else:
    print("⚠️  No memory configured")
    deletion_summary['skipped'].append("Memory")

# ============================================================================
# 4. DELETE LAMBDA FUNCTION AND ROLE
# ============================================================================
print("\n" + "="*80)
print("STEP 4: Deleting Lambda Function and IAM Role")
print("="*80)

lambda_config = configs.get('lambda_config.json', {})
if lambda_config.get('function_name'):
    function_name = lambda_config['function_name']
    
    # Delete Lambda function
    try:
        print(f"Deleting Lambda function: {function_name}...")
        
        lambda_client.delete_function(
            FunctionName=function_name
        )
        
        print(f"✓ Lambda function deleted: {function_name}")
        deletion_summary['success'].append(f"Lambda: {function_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"⚠️  Lambda function not found (may already be deleted)")
            deletion_summary['skipped'].append(f"Lambda: {function_name}")
        else:
            print(f"❌ Error deleting Lambda function: {e}")
            deletion_summary['failed'].append(f"Lambda: {function_name}")
    except Exception as e:
        print(f"❌ Error deleting Lambda function: {e}")
        deletion_summary['failed'].append(f"Lambda: {function_name}")
    
    # Delete Lambda IAM role
    if lambda_config.get('lambda_role_arn'):
        try:
            role_name = lambda_config['lambda_role_arn'].split('/')[-1]
            print(f"\nDeleting Lambda IAM role: {role_name}...")
            
            # Detach managed policies
            try:
                attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
                for policy in attached_policies['AttachedPolicies']:
                    iam_client.detach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy['PolicyArn']
                    )
                    print(f"  ✓ Detached policy: {policy['PolicyName']}")
            except Exception as e:
                print(f"  ⚠️  Error detaching policies: {e}")
            
            # Delete role
            iam_client.delete_role(RoleName=role_name)
            
            print(f"✓ Lambda IAM role deleted: {role_name}")
            deletion_summary['success'].append(f"Lambda IAM Role: {role_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                print(f"⚠️  Lambda IAM role not found (may already be deleted)")
                deletion_summary['skipped'].append(f"Lambda IAM Role: {role_name}")
            else:
                print(f"❌ Error deleting Lambda IAM role: {e}")
                deletion_summary['failed'].append(f"Lambda IAM Role: {role_name}")
        except Exception as e:
            print(f"❌ Error deleting Lambda IAM role: {e}")
            deletion_summary['failed'].append(f"Lambda IAM Role: {role_name}")
else:
    print("⚠️  No Lambda function configured")
    deletion_summary['skipped'].append("Lambda")

# ============================================================================
# 5. DELETE COGNITO USER POOL
# ============================================================================
print("\n" + "="*80)
print("STEP 5: Deleting Cognito User Pool")
print("="*80)

cognito_config = configs.get('cognito_config.json', {})
if cognito_config.get('user_pool_id'):
    user_pool_id = cognito_config['user_pool_id']
    
    # Delete domain first
    if cognito_config.get('domain_prefix'):
        try:
            domain_prefix = cognito_config['domain_prefix']
            print(f"Deleting Cognito domain: {domain_prefix}...")
            
            cognito_client.delete_user_pool_domain(
                Domain=domain_prefix,
                UserPoolId=user_pool_id
            )
            
            print(f"✓ Cognito domain deleted: {domain_prefix}")
            deletion_summary['success'].append(f"Cognito Domain: {domain_prefix}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"⚠️  Cognito domain not found (may already be deleted)")
                deletion_summary['skipped'].append(f"Cognito Domain: {domain_prefix}")
            else:
                print(f"❌ Error deleting Cognito domain: {e}")
                deletion_summary['failed'].append(f"Cognito Domain: {domain_prefix}")
        except Exception as e:
            print(f"❌ Error deleting Cognito domain: {e}")
            deletion_summary['failed'].append(f"Cognito Domain: {domain_prefix}")
    
    # Delete user pool
    try:
        print(f"\nDeleting Cognito user pool: {user_pool_id}...")
        
        cognito_client.delete_user_pool(
            UserPoolId=user_pool_id
        )
        
        print(f"✓ Cognito user pool deleted: {user_pool_id}")
        deletion_summary['success'].append(f"Cognito User Pool: {user_pool_id}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"⚠️  Cognito user pool not found (may already be deleted)")
            deletion_summary['skipped'].append(f"Cognito User Pool: {user_pool_id}")
        else:
            print(f"❌ Error deleting Cognito user pool: {e}")
            deletion_summary['failed'].append(f"Cognito User Pool: {user_pool_id}")
    except Exception as e:
        print(f"❌ Error deleting Cognito user pool: {e}")
        deletion_summary['failed'].append(f"Cognito User Pool: {user_pool_id}")
else:
    print("⚠️  No Cognito user pool configured")
    deletion_summary['skipped'].append("Cognito User Pool")

# ============================================================================
# 6. DELETE GATEWAY IAM ROLE
# ============================================================================
print("\n" + "="*80)
print("STEP 6: Deleting Gateway IAM Role")
print("="*80)

gateway_role_config = configs.get('gateway_role_config.json', {})
if gateway_role_config.get('role_name'):
    try:
        role_name = gateway_role_config['role_name']
        print(f"Deleting gateway IAM role: {role_name}...")
        
        # Detach managed policies
        try:
            attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
            for policy in attached_policies['AttachedPolicies']:
                iam_client.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy['PolicyArn']
                )
                print(f"  ✓ Detached policy: {policy['PolicyName']}")
        except Exception as e:
            print(f"  ⚠️  Error detaching policies: {e}")
        
        # Delete role
        iam_client.delete_role(RoleName=role_name)
        
        print(f"✓ Gateway IAM role deleted: {role_name}")
        deletion_summary['success'].append(f"Gateway IAM Role: {role_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"⚠️  Gateway IAM role not found (may already be deleted)")
            deletion_summary['skipped'].append(f"Gateway IAM Role: {role_name}")
        else:
            print(f"❌ Error deleting gateway IAM role: {e}")
            deletion_summary['failed'].append(f"Gateway IAM Role: {role_name}")
    except Exception as e:
        print(f"❌ Error deleting gateway IAM role: {e}")
        deletion_summary['failed'].append(f"Gateway IAM Role: {role_name}")
else:
    print("⚠️  No gateway IAM role configured")
    deletion_summary['skipped'].append("Gateway IAM Role")

# ============================================================================
# 7. DELETE RUNTIME EXECUTION ROLE AND POLICY
# ============================================================================
print("\n" + "="*80)
print("STEP 7: Deleting Runtime Execution IAM Role and Policy")
print("="*80)

runtime_role_config = configs.get('runtime_execution_role_config.json', {})
if runtime_role_config.get('role_name'):
    role_name = runtime_role_config['role_name']
    
    # Detach and delete custom policy
    if runtime_role_config.get('policy_arn'):
        try:
            policy_arn = runtime_role_config['policy_arn']
            policy_name = runtime_role_config['policy_name']
            print(f"Detaching and deleting IAM policy: {policy_name}...")
            
            # Detach from role
            iam_client.detach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"  ✓ Detached policy from role")
            
            # Delete policy
            iam_client.delete_policy(PolicyArn=policy_arn)
            
            print(f"✓ IAM policy deleted: {policy_name}")
            deletion_summary['success'].append(f"Runtime IAM Policy: {policy_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                print(f"⚠️  IAM policy not found (may already be deleted)")
                deletion_summary['skipped'].append(f"Runtime IAM Policy: {policy_name}")
            else:
                print(f"❌ Error deleting IAM policy: {e}")
                deletion_summary['failed'].append(f"Runtime IAM Policy: {policy_name}")
        except Exception as e:
            print(f"❌ Error deleting IAM policy: {e}")
            deletion_summary['failed'].append(f"Runtime IAM Policy: {policy_name}")
    
    # Delete role
    try:
        print(f"\nDeleting runtime IAM role: {role_name}...")
        
        # Detach any remaining managed policies
        try:
            attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
            for policy in attached_policies['AttachedPolicies']:
                iam_client.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy['PolicyArn']
                )
                print(f"  ✓ Detached policy: {policy['PolicyName']}")
        except Exception as e:
            print(f"  ⚠️  Error detaching policies: {e}")
        
        # Delete role
        iam_client.delete_role(RoleName=role_name)
        
        print(f"✓ Runtime IAM role deleted: {role_name}")
        deletion_summary['success'].append(f"Runtime IAM Role: {role_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"⚠️  Runtime IAM role not found (may already be deleted)")
            deletion_summary['skipped'].append(f"Runtime IAM Role: {role_name}")
        else:
            print(f"❌ Error deleting runtime IAM role: {e}")
            deletion_summary['failed'].append(f"Runtime IAM Role: {role_name}")
    except Exception as e:
        print(f"❌ Error deleting runtime IAM role: {e}")
        deletion_summary['failed'].append(f"Runtime IAM Role: {role_name}")
else:
    print("⚠️  No runtime IAM role configured")
    deletion_summary['skipped'].append("Runtime IAM Role")

# ============================================================================
# 8. DELETE ECR REPOSITORY
# ============================================================================
print("\n" + "="*80)
print("STEP 8: Deleting ECR Repository")
print("="*80)

if runtime_config.get('agent_name'):
    try:
        agent_name = runtime_config['agent_name']
        print(f"Deleting ECR repository: {agent_name}...")
        
        ecr_client.delete_repository(
            repositoryName=agent_name,
            force=True  # Delete even if it contains images
        )
        
        print(f"✓ ECR repository deleted: {agent_name}")
        deletion_summary['success'].append(f"ECR Repository: {agent_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'RepositoryNotFoundException':
            print(f"⚠️  ECR repository not found (may not have been created)")
            deletion_summary['skipped'].append(f"ECR Repository: {agent_name}")
        else:
            print(f"❌ Error deleting ECR repository: {e}")
            deletion_summary['failed'].append(f"ECR Repository: {agent_name}")
    except Exception as e:
        print(f"❌ Error deleting ECR repository: {e}")
        deletion_summary['failed'].append(f"ECR Repository: {agent_name}")
else:
    print("⚠️  No ECR repository configured")
    deletion_summary['skipped'].append("ECR Repository")

# ============================================================================
# CLEANUP SUMMARY
# ============================================================================
print("\n" + "="*80)
print("CLEANUP SUMMARY")
print("="*80)

print(f"\n✅ Successfully Deleted ({len(deletion_summary['success'])}):")
for item in deletion_summary['success']:
    print(f"  • {item}")

if deletion_summary['skipped']:
    print(f"\n⚠️  Skipped ({len(deletion_summary['skipped'])}):")
    for item in deletion_summary['skipped']:
        print(f"  • {item}")

if deletion_summary['failed']:
    print(f"\n❌ Failed ({len(deletion_summary['failed'])}):")
    for item in deletion_summary['failed']:
        print(f"  • {item}")

print("\n" + "="*80)
print("CLEANUP COMPLETE")
print("="*80)

if deletion_summary['failed']:
    print("\n⚠️  Some resources failed to delete. Check the errors above.")
    print("You may need to manually delete these resources in the AWS Console.")
else:
    print("\n✅ All resources have been successfully cleaned up!")
    print("\nYou can now safely delete the configuration JSON files if desired.")

print("="*80)
