"""
Multi-Tenant Insurance Claims Platform API
Demonstrates secure tenant isolation with AWS Bedrock AgentCore and Strands Agents
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import boto3
from functools import wraps
from config import Config
from cognito_service import CognitoService

app = Flask(__name__)
CORS(app)

# Initialize AWS services
cognito = CognitoService()
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=Config.AWS_REGION)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=Config.AWS_REGION)

# Database configuration
DB_CONFIG = {
    'host': Config.DB_HOST,
    'database': Config.DB_NAME,
    'user': Config.DB_USER,
    'password': Config.DB_PASSWORD
}


def get_db_connection(tenant_id=None):
    """Get database connection with tenant context for RLS"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    if tenant_id:
        with conn.cursor() as cur:
            cur.execute("SET app.current_tenant_id = %s", (str(tenant_id),))
        conn.commit()
    
    return conn


def token_required(f):
    """JWT Authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            decoded = cognito.decode_token(token)
            request.tenant_id = decoded.get('custom:tenant_id')
            request.user_sub = decoded.get('sub')
            request.user_email = decoded.get('email')
            
            if not request.tenant_id:
                return jsonify({'error': 'No tenant_id in token'}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': f'Invalid token: {str(e)}'}), 401
    
    return decorated_function


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/login', methods=['POST'])
def login():
    """
    Login endpoint - authenticates broker and returns JWT tokens
    
    Demo accounts:
    - broker-a@example.com / Pass123! (Broker A - 5 claims)
    - broker-b@example.com / Pass123! (Broker B - 2 claims)
    """
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Authenticate with Cognito
    auth_result = cognito.sign_in(email, password)
    
    if auth_result['success']:
        user_info = auth_result['user_info']
        tenant_id = user_info.get('custom:tenant_id')
        
        if not tenant_id:
            return jsonify({'error': 'No tenant associated with this user'}), 403
        
        # Verify tenant exists and is active
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT tenant_id, name, status FROM tenants WHERE tenant_id = %s",
                    (tenant_id,)
                )
                tenant = cur.fetchone()
                
                if not tenant or tenant['status'] != 'active':
                    conn.close()
                    return jsonify({'error': 'Tenant not found or inactive'}), 403
                
                tenant_name = tenant['name']
            
            conn.close()
            
            return jsonify({
                'success': True,
                'email': email,
                'tenant_id': tenant_id,
                'tenant_name': tenant_name,
                'access_token': auth_result['access_token'],
                'id_token': auth_result['id_token'],
                'user_info': {
                    'given_name': user_info.get('given_name'),
                    'family_name': user_info.get('family_name'),
                    'email': user_info.get('email')
                }
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
    else:
        return jsonify({
            'success': False,
            'error': auth_result.get('message', 'Authentication failed')
        }), 401


@app.route('/api/claims', methods=['GET'])
@token_required
def get_claims():
    """
    Get claims for authenticated tenant (RLS enforced)
    Demonstrates structured data isolation with Row-Level Security
    """
    tenant_id = request.tenant_id
    
    try:
        conn = get_db_connection(tenant_id)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # RLS automatically filters by tenant_id
            cur.execute("""
                SELECT 
                    claim_id,
                    claim_number,
                    customer_name,
                    claim_amount,
                    claim_date,
                    status,
                    description
                FROM claims
                ORDER BY claim_date DESC
                LIMIT 50
            """)
            claims = cur.fetchall()
            
            # Get summary statistics
            cur.execute("""
                SELECT 
                    COUNT(*) as total_claims,
                    SUM(claim_amount) as total_amount,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                    COUNT(CASE WHEN claim_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_claims
                FROM claims
            """)
            stats = cur.fetchone()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'tenant_id': tenant_id,
            'claims': claims,
            'statistics': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/query', methods=['POST'])
@token_required
def query():
    """
    Natural language query endpoint
    Supports both structured (SQL) and unstructured (RAG) queries
    """
    data = request.json
    user_query = data.get('query')
    
    if not user_query:
        return jsonify({'error': 'Query is required'}), 400
    
    tenant_id = request.tenant_id
    
    try:
        # Detect query type
        query_type = detect_query_type(user_query)
        
        if query_type == 'structured':
            response = query_structured_data(user_query, tenant_id)
        else:
            response = query_unstructured_data(user_query, tenant_id)
        
        return jsonify({
            'success': True,
            'response': response['answer'],
            'query_type': query_type,
            'tenant_id': tenant_id,
            'metadata': response.get('metadata', {})
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def detect_query_type(query):
    """Detect if query is for structured or unstructured data"""
    structured_keywords = ['how many', 'count', 'total', 'sum', 'average', 'claims filed', 'last week']
    unstructured_keywords = ['what is', 'explain', 'policy', 'deductible', 'coverage', 'maximum']
    
    query_lower = query.lower()
    
    for keyword in structured_keywords:
        if keyword in query_lower:
            return 'structured'
    
    for keyword in unstructured_keywords:
        if keyword in query_lower:
            return 'unstructured'
    
    return 'structured'


def query_structured_data(query, tenant_id):
    """Query structured data with RLS (Text-to-SQL simulation)"""
    conn = get_db_connection(tenant_id)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query_lower = query.lower()
            
            # Simple pattern matching for demo (in production, use proper text-to-SQL)
            if 'how many' in query_lower or 'count' in query_lower:
                if 'last week' in query_lower or 'week' in query_lower:
                    cur.execute("""
                        SELECT COUNT(*) as count
                        FROM claims
                        WHERE claim_date >= CURRENT_DATE - INTERVAL '7 days'
                    """)
                    result = cur.fetchone()
                    count = result['count']
                    
                    cur.execute("""
                        SELECT claim_number, customer_name, claim_amount, status, claim_date
                        FROM claims
                        WHERE claim_date >= CURRENT_DATE - INTERVAL '7 days'
                        ORDER BY claim_date DESC
                    """)
                    claims = cur.fetchall()
                    
                    answer = f"You have {count} claims filed in the last week:\n\n"
                    for claim in claims:
                        answer += f"• {claim['claim_number']}: {claim['customer_name']} - ${claim['claim_amount']:.2f} ({claim['status']}) - {claim['claim_date']}\n"
                    
                    return {
                        'answer': answer,
                        'metadata': {'claims_count': count, 'query_type': 'count'}
                    }
                else:
                    cur.execute("SELECT COUNT(*) as count FROM claims")
                    result = cur.fetchone()
                    return {
                        'answer': f"You have {result['count']} total claims.",
                        'metadata': {'claims_count': result['count']}
                    }
            
            elif 'total' in query_lower or 'sum' in query_lower:
                cur.execute("""
                    SELECT SUM(claim_amount) as total, COUNT(*) as count
                    FROM claims
                    WHERE claim_date >= CURRENT_DATE - INTERVAL '7 days'
                """)
                result = cur.fetchone()
                
                return {
                    'answer': f"Total claim amount for the last week: ${result['total']:.2f} across {result['count']} claims.",
                    'metadata': {'total_amount': float(result['total']), 'claims_count': result['count']}
                }
            
            else:
                return {
                    'answer': "I can help you with queries about claim counts and totals. Try asking 'How many claims were filed last week?'",
                    'metadata': {}
                }
    
    finally:
        conn.close()


def query_unstructured_data(query, tenant_id):
    """Query unstructured data with RAG + metadata filtering"""
    if not Config.KNOWLEDGE_BASE_ID:
        return {
            'answer': 'Knowledge base not configured. This would query policy documents with metadata filtering to ensure tenant isolation.',
            'metadata': {'sources': []}
        }
    
    # Build metadata filter for tenant isolation
    tenant_filter = {
        "equals": {
            "key": "tenant_id",
            "value": tenant_id
        }
    }
    
    try:
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={'text': query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': Config.KNOWLEDGE_BASE_ID,
                    'modelArn': f'arn:aws:bedrock:{Config.AWS_REGION}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 5,
                            'filter': tenant_filter
                        }
                    }
                }
            }
        )
        
        answer = response['output']['text']
        sources = []
        
        if 'citations' in response:
            for citation in response['citations']:
                for reference in citation.get('retrievedReferences', []):
                    sources.append({
                        'uri': reference.get('location', {}).get('s3Location', {}).get('uri'),
                        'text': reference.get('content', {}).get('text', '')[:200]
                    })
        
        return {
            'answer': answer,
            'metadata': {'sources': sources}
        }
    
    except Exception as e:
        return {
            'answer': f'Error querying knowledge base: {str(e)}',
            'metadata': {'sources': []}
        }


@app.route('/api/chat', methods=['POST'])
@token_required
def chat():
    """
    General chat endpoint using Bedrock
    For complex queries requiring agent orchestration
    """
    data = request.json
    messages = data.get('messages', [])
    
    if not messages:
        return jsonify({'error': 'Messages required'}), 400
    
    tenant_id = request.tenant_id
    
    try:
        conversation = []
        for msg in messages:
            conversation.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        system_prompt = f"""You are an AI assistant for an insurance claims platform.
You are currently helping tenant: {tenant_id}
You can only access and discuss information related to this tenant.

Your capabilities:
- Answer questions about insurance claims and policies
- Provide information about claim status and amounts
- Explain insurance terms and coverage details

Always maintain tenant isolation and never discuss data from other tenants."""
        
        bedrock_request = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1000,
            'system': system_prompt,
            'messages': conversation
        }
        
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps(bedrock_request)
        )
        
        response_body = json.loads(response['body'].read())
        assistant_message = response_body['content'][0]['text']
        
        return jsonify({
            'success': True,
            'response': assistant_message,
            'tenant_id': tenant_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
