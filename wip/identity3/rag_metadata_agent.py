from strands import Agent
import json
import base64
import boto3
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

# Initialize Bedrock clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Initialize model and agent
model = BedrockModel(model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0")
agent = Agent(
    model=model,
    system_prompt="You're a helpful assistant with access to tenant-specific knowledge base."
)

@app.entrypoint
def rag_metadata_agent(payload):
    """Process requests with RAG and metadata filtering for tenant isolation"""
    
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
    
    if not user_identity['authenticated'] or not user_identity['tenant_id']:
        return {
            "response": "Authentication required with valid tenant_id",
            "user_identity": user_identity
        }
    
    # Get knowledge base ID from payload or environment
    knowledge_base_id = payload.get("knowledge_base_id")
    user_input = payload.get("prompt", "")
    
    if not knowledge_base_id:
        # Fallback to agent without RAG
        response = agent(user_input)
        return {
            "response": response.message['content'][0]['text'],
            "user_identity": user_identity,
            "rag_used": False
        }
    
    # Build metadata filter for tenant isolation
    tenant_filter = {
        "equals": {
            "key": "tenant_id",
            "value": user_identity['tenant_id']
        }
    }
    
    # Call RetrieveAndGenerate with metadata filtering
    try:
        # Use inference profile instead of foundation model ARN
        model_arn = "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        
        rag_response = bedrock_agent_runtime.retrieve_and_generate(
            input={'text': user_input},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': model_arn,
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 5,
                            'filter': tenant_filter
                        }
                    }
                }
            }
        )
        
        agent_response = rag_response['output']['text']
        citations = rag_response.get('citations', [])
        
        print(f"RAG Response generated with {len(citations)} citations")
        
        return {
            "response": agent_response,
            "user_identity": user_identity,
            "rag_used": True,
            "citations_count": len(citations),
            "metadata_filter": tenant_filter
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"RAG error: {error_msg}")
        
        # Check if it's a model ARN issue
        if "GetInferenceProfile" in error_msg or "ValidationException" in error_msg:
            print("Model ARN validation failed. Using fallback model.")
        
        # Fallback to agent without RAG
        response = agent(user_input)
        return {
            "response": response.message['content'][0]['text'],
            "user_identity": user_identity,
            "rag_used": False,
            "error": error_msg,
            "note": "RAG failed, used fallback agent. Check knowledge_base_id and model ARN."
        }

if __name__ == "__main__":
    app.run()
