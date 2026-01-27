# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os

class Config:
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
    
    # Cognito - Tutorial 02 (RLS Agent)
    RLS_COGNITO_USER_POOL_ID = os.getenv('RLS_COGNITO_USER_POOL_ID')
    RLS_COGNITO_CLIENT_ID = os.getenv('RLS_COGNITO_CLIENT_ID')
    
    # Cognito - Tutorial 01 (RAG Agent)
    RAG_COGNITO_USER_POOL_ID = os.getenv('RAG_COGNITO_USER_POOL_ID')
    RAG_COGNITO_CLIENT_ID = os.getenv('RAG_COGNITO_CLIENT_ID')
    
    # Agent ARNs
    RAG_AGENT_ARN = os.getenv('RAG_AGENT_ARN')
    RLS_AGENT_ARN = os.getenv('RLS_AGENT_ARN')
