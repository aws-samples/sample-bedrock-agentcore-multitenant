from strands import Agent
import json
import base64
from bedrock_agentcore.runtime import BedrockAgentCoreApp, BedrockAgentCoreContext
from strands.models import BedrockModel

app = BedrockAgentCoreApp()

def decode_jwt(token):
    """Decode JWT payload"""
    try:
        parts = token.split('.')
        payload = parts[1]
        padding = 4 - (len(payload) % 4)
        if padding != 4:
            payload += '=' * padding
        return json.loads(base64.b64decode(payload))
    except:
        return None

model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0")
agent = Agent(model=model, system_prompt="You're a helpful assistant.")

@app.entrypoint
def simple_auth_agent(payload):
    """Simple authentication - extract basic user info from Access Token"""

    # Get Authorization header
    headers = BedrockAgentCoreContext.get_request_headers() or {}
    auth = headers.get('authorization') or headers.get('Authorization')

    if not auth:
        return {
            "response": "Not authenticated",
            "user_info": {"authenticated": False}
        }

    # Decode Access Token
    token = auth.replace('Bearer ', '')
    claims = decode_jwt(token)

    if not claims:
        return {
            "response": "Invalid token",
            "user_info": {"authenticated": False}
        }

    # Extract basic info (what's available in Access Token)
    user_info = {
        "authenticated": True,
        "sub": claims.get('sub'),           # User ID
        "username": claims.get('username'),  # Username
        "client_id": claims.get('client_id'), # Client ID
        "token_use": claims.get('token_use')  # Should be 'access'
    }

    print(f"Authenticated user: {user_info['username']} (sub: {user_info['sub'][:20]}...)")

    # Process request
    user_input = payload.get("prompt", "")
    response = agent(user_input)

    return {
        "response": response.message['content'][0]['text'],
        "user_info": user_info
    }

if __name__ == "__main__":
    app.run()
