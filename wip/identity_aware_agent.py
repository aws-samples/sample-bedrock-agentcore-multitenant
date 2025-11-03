from strands import Agent
import json
import base64
from bedrock_agentcore.runtime import BedrockAgentCoreApp, BedrockAgentCoreContext
from strands.models import BedrockModel

app = BedrockAgentCoreApp()

def decode_jwt(token):
    """Decode JWT payload without verification"""
    try:
        parts = token.split('.')
        if len(parts) < 2:
            return None
        payload = parts[1]
        padding = 4 - (len(payload) % 4)
        if padding != 4:
            payload += '=' * padding
        return json.loads(base64.b64decode(payload))
    except Exception as e:
        print(f"JWT decode error: {e}")
        return None

def extract_user_identity(jwt_claims):
    """Extract user identity from JWT claims"""
    if not jwt_claims:
        return {
            'authenticated': False,
            'tenant_id': None,
            'user_role': None,
            'username': None,
            'sub': None
        }
    
    return {
        'authenticated': True,
        'tenant_id': jwt_claims.get('custom:tenant_id'),
        'user_role': jwt_claims.get('custom:user_role'),
        'username': jwt_claims.get('username') or jwt_claims.get('cognito:username'),
        'sub': jwt_claims.get('sub')
    }

# Initialize model and agent
model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0")
agent = Agent(
    model=model,
    system_prompt="You're a helpful assistant with access to user context."
)

@app.entrypoint
def identity_aware_agent(payload):
    """Process requests with user identity awareness"""
    
    # Extract JWT from Authorization header
    headers = BedrockAgentCoreContext.get_request_headers() or {}
    auth_header = headers.get('authorization') or headers.get('Authorization')
    
    jwt_claims = None
    user_identity = None
    
    if auth_header:
        token = auth_header.replace('Bearer ', '').replace('bearer ', '')
        jwt_claims = decode_jwt(token)
        user_identity = extract_user_identity(jwt_claims)
    else:
        user_identity = extract_user_identity(None)
    
    # Log for CloudWatch
    print(f"User Identity: {json.dumps(user_identity, indent=2)}")
    
    # Process request
    user_input = payload.get("prompt", "")
    response = agent(user_input)
    agent_response = response.message['content'][0]['text']
    
    return {
        "response": agent_response,
        "user_identity": user_identity,
        "debug": {
            "request_id": BedrockAgentCoreContext.get_request_id(),
            "has_auth_header": bool(auth_header),
            "token_type": jwt_claims.get('token_use') if jwt_claims else None
        }
    }

if __name__ == "__main__":
    app.run()
