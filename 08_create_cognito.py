#!/usr/bin/env python3
"""
Script to create Cognito User Pool for Gateway authentication.

This script sets up OAuth2 authentication infrastructure for AgentCore Gateway.
"""

import json
import boto3
import time
from botocore.exceptions import ClientError

REGION = 'us-west-2'

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name=REGION)

print("="*80)
print("CREATING COGNITO USER POOL FOR GATEWAY AUTHENTICATION")
print("="*80)

# Generate unique domain prefix using timestamp
domain_prefix = f"returns-gateway-{int(time.time())}"

try:
    # Step 1: Create User Pool
    print("\n📝 Step 1: Creating Cognito User Pool...")
    
    user_pool_response = cognito_client.create_user_pool(
        PoolName='ReturnsGatewayUserPool',
        Policies={
            'PasswordPolicy': {
                'MinimumLength': 8,
                'RequireUppercase': False,
                'RequireLowercase': False,
                'RequireNumbers': False,
                'RequireSymbols': False
            }
        },
        AutoVerifiedAttributes=[],
        Schema=[
            {
                'Name': 'email',
                'AttributeDataType': 'String',
                'Required': False,
                'Mutable': True
            }
        ]
    )
    
    user_pool_id = user_pool_response['UserPool']['Id']
    print(f"✓ User Pool created: {user_pool_id}")
    
    # Step 2: Create User Pool Domain
    print(f"\n📝 Step 2: Creating User Pool Domain...")
    print(f"   Domain prefix: {domain_prefix}")
    
    try:
        cognito_client.create_user_pool_domain(
            Domain=domain_prefix,
            UserPoolId=user_pool_id
        )
        print(f"✓ Domain created: {domain_prefix}.auth.{REGION}.amazoncognito.com")
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidParameterException':
            # Domain might already exist, try with a different suffix
            domain_prefix = f"returns-gateway-{int(time.time())}-alt"
            print(f"   Retrying with: {domain_prefix}")
            cognito_client.create_user_pool_domain(
                Domain=domain_prefix,
                UserPoolId=user_pool_id
            )
            print(f"✓ Domain created: {domain_prefix}.auth.{REGION}.amazoncognito.com")
        else:
            raise
    
    # Step 3: Create Resource Server with scopes
    print("\n📝 Step 3: Creating Resource Server with OAuth scopes...")
    
    cognito_client.create_resource_server(
        UserPoolId=user_pool_id,
        Identifier='gateway-api',
        Name='GatewayAPI',
        Scopes=[
            {
                'ScopeName': 'read',
                'ScopeDescription': 'Read access to gateway'
            },
            {
                'ScopeName': 'write',
                'ScopeDescription': 'Write access to gateway'
            }
        ]
    )
    print("✓ Resource server created with read/write scopes")
    
    # Step 4: Create App Client for machine-to-machine authentication
    print("\n📝 Step 4: Creating App Client for machine-to-machine auth...")
    
    app_client_response = cognito_client.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName='ReturnsGatewayClient',
        GenerateSecret=True,
        ExplicitAuthFlows=[],
        AllowedOAuthFlows=['client_credentials'],
        AllowedOAuthScopes=[
            'gateway-api/read',
            'gateway-api/write'
        ],
        AllowedOAuthFlowsUserPoolClient=True,
        SupportedIdentityProviders=['COGNITO']
    )
    
    client_id = app_client_response['UserPoolClient']['ClientId']
    print(f"✓ App Client created: {client_id}")
    
    # Step 5: Get client secret
    print("\n📝 Step 5: Retrieving client secret...")
    
    client_details = cognito_client.describe_user_pool_client(
        UserPoolId=user_pool_id,
        ClientId=client_id
    )
    
    client_secret = client_details['UserPoolClient']['ClientSecret']
    print("✓ Client secret retrieved")
    
    # Step 6: Construct endpoints
    print("\n📝 Step 6: Constructing OAuth endpoints...")
    
    # Token endpoint (hosted UI domain)
    token_endpoint = f"https://{domain_prefix}.auth.{REGION}.amazoncognito.com/oauth2/token"
    
    # Discovery URL (IDP domain - CRITICAL for AgentCore)
    discovery_url = f"https://cognito-idp.{REGION}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    
    print(f"✓ Token endpoint: {token_endpoint}")
    print(f"✓ Discovery URL: {discovery_url}")
    
    # Step 7: Save configuration
    print("\n📝 Step 7: Saving configuration to cognito_config.json...")
    
    config = {
        "user_pool_id": user_pool_id,
        "domain_prefix": domain_prefix,
        "client_id": client_id,
        "client_secret": client_secret,
        "token_endpoint": token_endpoint,
        "discovery_url": discovery_url,
        "region": REGION
    }
    
    with open('cognito_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✓ Configuration saved to cognito_config.json")
    
    # Summary
    print("\n" + "="*80)
    print("✅ COGNITO SETUP COMPLETE")
    print("="*80)
    print(f"\nUser Pool ID: {user_pool_id}")
    print(f"Domain Prefix: {domain_prefix}")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {client_secret[:10]}...{client_secret[-10:]}")
    print(f"\nOAuth Scopes: gateway-api/read, gateway-api/write")
    print(f"Auth Flow: client_credentials (machine-to-machine)")
    print("\n" + "="*80)
    print("Next Steps:")
    print("  1. Use these credentials to create an AgentCore Gateway")
    print("  2. Gateway will use this Cognito pool for authentication")
    print("  3. Agents will get OAuth tokens to call gateway tools")
    print("="*80)

except ClientError as e:
    print(f"\n❌ Error: {e.response['Error']['Message']}")
    print(f"   Error Code: {e.response['Error']['Code']}")
    exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
