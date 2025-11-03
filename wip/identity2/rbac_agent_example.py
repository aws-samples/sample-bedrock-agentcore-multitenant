from strands import Agent, tool
import json
import base64
from bedrock_agentcore.runtime import BedrockAgentCoreApp, BedrockAgentCoreContext
from strands.models import BedrockModel

app = BedrockAgentCoreApp()

# Mock data by tenant
TENANT_DATA = {
    'tenant-a': {'orders': ['order-a1', 'order-a2'], 'revenue': 50000},
    'tenant-b': {'orders': ['order-b1'], 'revenue': 30000}
}

def decode_jwt(token):
    try:
        parts = token.split('.')
        payload = parts[1]
        padding = 4 - (len(payload) % 4)
        if padding != 4:
            payload += '=' * padding
        return json.loads(base64.b64decode(payload))
    except:
        return None

def create_tenant_tools(tenant_id, user_role):
    """Create tools scoped to tenant and filtered by role"""

    @tool
    def get_orders() -> str:
        f"""Get orders for tenant {tenant_id}"""
        orders = TENANT_DATA.get(tenant_id, {}).get('orders', [])
        return f"Orders for {tenant_id}: {', '.join(orders)}"

    @tool
    def get_revenue() -> str:
        f"""Get revenue for tenant {tenant_id} (admin only)"""
        if user_role != 'admin':
            return "Permission denied: Admin role required"
        revenue = TENANT_DATA.get(tenant_id, {}).get('revenue', 0)
        return f"Revenue for {tenant_id}: ${revenue}"

    # Return tools based on role
    if user_role == 'admin':
        return [get_orders, get_revenue]
    else:
        return [get_orders]  # Read-only for non-admin

@app.entrypoint
def rbac_agent(payload):
    # Extract JWT
    headers = BedrockAgentCoreContext.get_request_headers() or {}
    auth = headers.get('Authorization')

    if not auth:
        return {"error": "Unauthorized"}

    claims = decode_jwt(auth.replace('Bearer ', ''))
    if not claims:
        return {"error": "Invalid token"}

    tenant_id = claims.get('custom:tenant_id')
    user_role = claims.get('custom:user_role')
    username = claims.get('cognito:username')

    # Create tenant-scoped and role-filtered tools
    tools = create_tenant_tools(tenant_id, user_role)

    # Create agent with appropriate tools
    model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    agent = Agent(
        model=model,
        tools=tools,
        system_prompt=f"You are assisting {username} from {tenant_id}. "
                     f"User role: {user_role}. Only access data for this tenant."
    )

    response = agent(payload.get("prompt", ""))

    return {
        "response": response.message['content'][0]['text'],
        "user_context": {
            "username": username,
            "tenant_id": tenant_id,
            "role": user_role,
            "available_tools": [t.__name__ for t in tools]
        }
    }

if __name__ == "__main__":
    app.run()
