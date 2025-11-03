# Identity Propagation with ID Token (Multi-Tenant)

This example demonstrates multi-tenant authentication using ID Tokens with custom attributes for Amazon Bedrock AgentCore.

## When to Use ID Token

✅ **Use ID Token when:**
- Multi-tenant application
- Need custom attributes (tenant_id, user_role)
- Need detailed user profile information
- Implementing role-based access control (RBAC)

❌ **Don't use ID Token when:**
- Single-tenant application with basic auth needs
- Following strict OAuth 2.0 API authorization patterns

## What ID Token Contains (Cognito)

```json
{
  "sub": "user-uuid",
  "aud": "3jea6...",                    // ✓ Audience (client_id)
  "cognito:username": "user-a",
  "custom:tenant_id": "tenant-a",       // ✓ Custom attribute
  "custom:user_role": "admin",          // ✓ Custom attribute
  "token_use": "id"
  // ❌ No client_id field
}
```

## Architecture

```
┌─────────────┐    ID Token (JWT)    ┌──────────────────┐
│   Cognito   │ ─────────────────-─> │  AgentCore       │
│  User Pool  │   with custom attrs  │  Runtime         │
└─────────────┘                      │  - Validates JWT │
                                     │  - Forwards header│
                                     └──────────────────┘
                                              │
                                              │ Authorization header
                                              │ BedrockAgentCoreContext
                                              ▼
                                     ┌──────────────────┐
                                     │  Strands Agent   │
                                     │  - Decode JWT    │
                                     │  - Extract claims│
                                     │  - RBAC logic    │
                                     │  - Tenant filter │
                                     └──────────────────┘
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the notebook:
```bash
jupyter notebook agentcore-identity-propagation-multitenant-idtoken.ipynb
```

The notebook will:
- Create Cognito User Pool with custom attributes (tenant_id, user_role)
- Create test users for different tenants
- Deploy AgentCore Runtime with ID Token validation
- Test identity propagation and multi-tenant isolation
- Demonstrate role-based access control

## Key Configuration

### Cognito User Pool with Custom Attributes

```python
user_pool_response = cognito_client.create_user_pool(
    PoolName=user_pool_name,
    Schema=[
        {'Name': 'email', 'AttributeDataType': 'String', 'Required': True},
        {'Name': 'tenant_id', 'AttributeDataType': 'String', 'Mutable': True},
        {'Name': 'user_role', 'AttributeDataType': 'String', 'Mutable': True}
    ]
)
```

### AgentCore Configuration

```python
authorizer_configuration={
    "customJWTAuthorizer": {
        "discoveryUrl": cognito_discovery_url,
        "allowedAudience": [client_id]  # For ID Token (validates aud)
    }
}

# IMPORTANT: Add Authorization header forwarding
request_header_configuration={
    "requestHeaderAllowlist": ["Authorization"]
}
```

### Agent Implementation

```python
from bedrock_agentcore.runtime import BedrockAgentCoreContext

def extract_user_identity(jwt_claims):
    """Extract user identity from JWT claims"""
    return {
        'authenticated': True,
        'tenant_id': jwt_claims.get('custom:tenant_id'),
        'user_role': jwt_claims.get('custom:user_role'),
        'username': jwt_claims.get('cognito:username'),
        'sub': jwt_claims.get('sub')
    }

# Get Authorization header
headers = BedrockAgentCoreContext.get_request_headers() or {}
auth_header = headers.get('authorization')

# Decode ID Token
token = auth_header.replace('Bearer ', '')
jwt_claims = decode_jwt(token)
user_identity = extract_user_identity(jwt_claims)

# Use tenant_id for data filtering
tenant_id = user_identity['tenant_id']
```

## What You'll Learn

1. ID Token vs Access Token differences
2. Custom attributes in Cognito User Pools
3. Identity propagation through AgentCore
4. Multi-tenant data isolation patterns
5. Role-based access control (RBAC)
6. Authorization header forwarding

## Advanced Example: RBAC

The notebook includes an advanced example showing role-based tool filtering:

```python
def create_tenant_tools(tenant_id, user_role):
    """Create tools scoped to tenant and filtered by role"""
    
    @tool
    def get_orders() -> str:
        """Get orders for tenant (all roles)"""
        return f"Orders for {tenant_id}: ..."
    
    @tool
    def get_revenue() -> str:
        """Get revenue for tenant (admin only)"""
        if user_role != 'admin':
            return "Permission denied: Admin role required"
        return f"Revenue for {tenant_id}: ..."
    
    # Return tools based on role
    if user_role == 'admin':
        return [get_orders, get_revenue]
    else:
        return [get_orders]  # Read-only for non-admin
```

## Testing

The notebook includes comprehensive tests:

1. **Unauthenticated Request** - Verifies authentication is enforced
2. **Token Comparison** - Shows Access Token vs ID Token differences
3. **Identity Propagation** - Verifies tenant_id and user_role extraction
4. **Multi-Tenant Isolation** - Tests that each user sees only their tenant data
5. **Role-Based Access** - Demonstrates admin vs user permissions

## Files

- `agentcore-identity-propagation-multitenant-idtoken.ipynb` - Complete tutorial
- `identity_aware_agent.py` - Agent implementation
- `rbac_agent_example.py` - Advanced RBAC example
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration

## Token Comparison

| Aspect | Access Token | ID Token (This Example) |
|--------|--------------|------------------------|
| Token Type | access | id |
| Validation | allowedClients | allowedAudience |
| Custom Attributes | ❌ No | ✅ Yes |
| Use Case | Simple auth | Multi-tenant |
| OAuth 2.0 Standard | ✅ Yes | ❌ Non-standard for API |

## Important Notes

- **ID Token for API**: While ID Tokens are typically used for client authentication, AgentCore allows them as Bearer tokens for efficiency
- **No Token Introspection**: Eliminates need for additional API calls to get user attributes
- **Custom Attributes**: Only available in ID Token (Cognito limitation)
- **Header Forwarding**: Must configure `requestHeaderAllowlist: ['Authorization']`

## Best Practices

1. ✅ Use ID Token for multi-tenant applications
2. ✅ Configure `allowedAudience` to match ID Token's `aud` claim
3. ✅ Add `requestHeaderAllowlist: ['Authorization']`
4. ✅ Extract identity using `BedrockAgentCoreContext`
5. ✅ Implement tenant-based data isolation
6. ✅ Filter tools based on user roles
7. ✅ Log user context for audit trails

## Next Steps

- For RAG with metadata filtering, see `../identity3/`
- For simple authentication, see `../identity1/`

## References

- [ID Token vs Access Token](https://auth0.com/blog/id-token-access-token-what-is-the-difference/)
- [Cognito Custom Attributes](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html)
- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Strands Agents](https://github.com/awslabs/strands)
