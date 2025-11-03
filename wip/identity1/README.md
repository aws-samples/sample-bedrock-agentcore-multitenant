# Simple Authentication with Access Token

This example demonstrates the standard OAuth 2.0 approach using Access Tokens for basic authentication with Amazon Bedrock AgentCore.

## When to Use Access Token

✅ **Use Access Token when:**
- Single-tenant application
- Only need basic user identity (sub, username)
- Don't need custom user attributes
- Following standard OAuth 2.0 patterns

❌ **Don't use Access Token when:**
- Multi-tenant application
- Need custom attributes (tenant_id, user_role)
- Need detailed user profile information

## What Access Token Contains (Cognito)

```json
{
  "sub": "user-uuid",              // ✓ User ID
  "username": "john",              // ✓ Username  
  "client_id": "3jea6...",         // ✓ Client ID
  "token_use": "access",
  "scope": "aws.cognito.signin.user.admin"
  // ❌ No aud field
  // ❌ No custom attributes
}
```

## Architecture

```
Client → Access Token → AgentCore → Strands Agent
                         (validates)  (extracts sub, username)
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the notebook:
```bash
jupyter notebook agentcore-simple-authentication-accesstoken.ipynb
```

The notebook will:
- Create Cognito User Pool (no custom attributes)
- Create test users (alice, bob)
- Deploy AgentCore Runtime with Access Token validation
- Test authentication and user identification

## Key Configuration

### AgentCore Configuration

```python
authorizer_configuration={
    "customJWTAuthorizer": {
        "discoveryUrl": cognito_discovery_url,
        "allowedClients": [client_id]  # For Access Token
        # No allowedAudience - Access Token doesn't have aud field
    }
}
```

### Agent Implementation

```python
from bedrock_agentcore.runtime import BedrockAgentCoreContext

# Get Authorization header
headers = BedrockAgentCoreContext.get_request_headers() or {}
auth = headers.get('authorization')

# Decode Access Token
claims = decode_jwt(auth.replace('Bearer ', ''))

# Extract basic info
user_info = {
    "sub": claims.get('sub'),
    "username": claims.get('username'),
    "client_id": claims.get('client_id')
}
```

## What You'll Learn

1. Standard OAuth 2.0 Access Token flow
2. AgentCore JWT validation with `allowedClients`
3. Extracting user identity from Access Token
4. Authorization header forwarding
5. Difference between Access Token and ID Token

## Files

- `agentcore-simple-authentication-accesstoken.ipynb` - Complete tutorial
- `simple_auth_agent.py` - Agent implementation
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration

## Comparison: Access Token vs ID Token

| Claim | Access Token | ID Token |
|-------|--------------|----------|
| `sub` | ✅ | ✅ |
| `username` | ✅ | ✅ |
| `client_id` | ✅ | ❌ |
| `aud` | ❌ | ✅ |
| `custom:tenant_id` | ❌ | ✅ |
| `custom:user_role` | ❌ | ✅ |

### AgentCore Configuration

```python
# Access Token
authorizer_configuration={
    "customJWTAuthorizer": {
        "discoveryUrl": "...",
        "allowedClients": [client_id]  # Validates client_id
    }
}

# ID Token
authorizer_configuration={
    "customJWTAuthorizer": {
        "discoveryUrl": "...",
        "allowedAudience": [client_id]  # Validates aud
    }
}
```

## Next Steps

- For multi-tenant applications, see `../identity2/` (ID Token with custom attributes)
- For RAG with metadata filtering, see `../identity3/`

## References

- [OAuth 2.0 Access Tokens](https://oauth.net/2/access-tokens/)
- [Amazon Cognito Tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html)
- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
