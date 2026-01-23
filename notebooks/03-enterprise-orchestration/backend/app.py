import os
import logging
import urllib.parse
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import boto3
import requests
from functools import wraps
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)

# Initialize AWS
cognito_client = boto3.client('cognito-idp', region_name=Config.AWS_REGION)

logger.info(f"Region: {Config.AWS_REGION}")
logger.info(f"RLS Cognito: {Config.RLS_COGNITO_USER_POOL_ID}")
logger.info(f"RAG Cognito: {Config.RAG_COGNITO_USER_POOL_ID}")
logger.info(f"RLS Agent: {Config.RLS_AGENT_ARN}")
logger.info(f"RAG Agent: {Config.RAG_AGENT_ARN}")


def cognito_sign_in(username: str, password: str, user_pool_id: str, client_id: str) -> dict:
    """Sign in to Cognito and return tokens"""
    try:
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': username, 'PASSWORD': password}
        )
        
        auth_result = response['AuthenticationResult']
        return {
            'success': True,
            'access_token': auth_result['AccessToken'],
            'id_token': auth_result['IdToken']
        }
    except Exception as e:
        logger.error(f"Cognito sign in failed: {e}")
        return {'success': False, 'error': str(e)}


def invoke_agent(agent_arn: str, prompt: str, access_token: str, session_id: str = None) -> dict:
    """Invoke AgentCore agent with OAuth token via HTTPS"""
    try:
        encoded_arn = urllib.parse.quote(agent_arn, safe='')
        endpoint = f"https://bedrock-agentcore.{Config.AWS_REGION}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        
        payload = json.dumps({'prompt': prompt})
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        # Add session ID for conversation history
        if session_id:
            headers['X-Runtime-Session-Id'] = session_id
        
        logger.info(f"Calling agent: {agent_arn.split('/')[-1]} (session: {session_id})")
        response = requests.post(endpoint, data=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Agent call failed: {response.status_code} - {response.text[:200]}")
            return {'error': f"Agent call failed: {response.status_code}"}
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        return {'error': str(e)}


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/demo-login', methods=['POST'])
def demo_login():
    """Demo login - authenticate and return real tokens"""
    data = request.json
    username = data.get('username')
    agent_type = data.get('agent_type', 'rls')
    
    # All demo users use same password
    password = 'Pass123!'
    
    # Select Cognito pool based on agent type
    if agent_type == 'rag':
        user_pool_id = Config.RAG_COGNITO_USER_POOL_ID
        client_id = Config.RAG_COGNITO_CLIENT_ID
    else:
        user_pool_id = Config.RLS_COGNITO_USER_POOL_ID
        client_id = Config.RLS_COGNITO_CLIENT_ID
    
    logger.info(f"Demo login: {username} (agent_type={agent_type})")
    
    auth_result = cognito_sign_in(username, password, user_pool_id, client_id)
    
    if auth_result['success']:
        # Map username to tenant info
        tenant_map = {
            # RLS users
            'mike-broker-a': ('broker-a', 'Broker A'),
            'emma-broker-b': ('broker-b', 'Broker B'),
            # RAG users
            'john-regular': ('regular', 'Regular Tier'),
            'sarah-platinum': ('platinum', 'Platinum Tier')
        }
        tenant_id, tenant_name = tenant_map.get(username, ('unknown', 'Unknown'))
        
        return jsonify({
            'success': True,
            'email': f'{username}@example.com',
            'tenant_id': tenant_id,
            'tenant_name': tenant_name,
            'agent_type': agent_type,
            'access_token': auth_result['access_token'],
            'id_token': auth_result['id_token'],
            'user_info': {
                'given_name': username.split('-')[0].capitalize(),
                'family_name': '',
                'email': f'{username}@example.com'
            }
        }), 200
    else:
        return jsonify({'error': auth_result.get('error', 'Authentication failed')}), 401


@app.route('/api/query', methods=['POST'])
def query():
    """Query via appropriate agent based on agent_type header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing authorization'}), 401
    
    token = auth_header.split(' ')[1]
    tenant_id = request.headers.get('X-Tenant-Id', 'unknown')
    agent_type = request.headers.get('X-Agent-Type', 'rls')
    session_id = request.headers.get('X-Session-Id')
    
    data = request.json
    user_query = data.get('query', '')
    
    logger.info(f"Query from {tenant_id} ({agent_type}): {user_query}")
    
    # Select agent based on type
    if agent_type == 'rag':
        agent_arn = Config.RAG_AGENT_ARN
        query_type = 'unstructured'
    else:
        agent_arn = Config.RLS_AGENT_ARN
        query_type = 'structured'
    
    result = invoke_agent(agent_arn, user_query, token, session_id)
    
    if 'error' in result:
        return jsonify({'error': result['error']}), 500
    
    return jsonify({
        'success': True,
        'response': result.get('response', str(result)),
        'query_type': query_type,
        'tenant_id': tenant_id
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
