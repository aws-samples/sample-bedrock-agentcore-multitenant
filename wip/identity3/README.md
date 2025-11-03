# Multi-Tenant RAG with Metadata Filtering

This example demonstrates end-to-end multi-tenant RAG implementation using:
- Amazon Cognito for authentication with custom tenant attributes
- Amazon Bedrock AgentCore for identity propagation
- Amazon Bedrock Knowledge Bases with metadata filtering
- Strands Agents for intelligent query processing

## Architecture

```
Tenant A → JWT (tenant_id=A) → AgentCore → Strands Agent
                                                  ↓
                                    RetrieveAndGenerate API
                                    + filter: {tenant_id: A}
                                                  ↓
                                    Knowledge Base (pooled)
                                    ├─ Doc1 {tenant_id: A} ✓
                                    ├─ Doc2 {tenant_id: B} ✗
                                    └─ Doc3 {tenant_id: A} ✓
```

## Key Features

- **Pool-based multi-tenancy**: Single Knowledge Base with metadata filtering
- **Cost-efficient**: Shared infrastructure with strict isolation
- **Secure**: Metadata filter enforced at vector database layer
- **Identity propagation**: JWT → AgentCore → Strands → RAG

## Quick Start

### Prerequisites

- AWS Account with Bedrock access
- Python 3.10+
- Docker (for local testing)

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the notebook:
```bash
jupyter notebook agentcore-rag-metadata-filtering.ipynb
```

The notebook will:
- Create Cognito User Pool with tenant_id attribute
- Upload sample documents with metadata to S3
- Create Knowledge Base and ingest documents
- Deploy AgentCore Runtime with JWT authentication
- Test multi-tenant isolation

## Document Metadata Format

Each document requires a corresponding `.metadata.json` file:

```json
{
  "metadataAttributes": {
    "tenant_id": "broker-a",
    "document_type": "policy",
    "region": "us-east-1"
  }
}
```

File naming: `document.txt` → `document.txt.metadata.json`

## Agent Implementation

The agent extracts tenant_id from JWT and applies metadata filtering:

```python
# Extract tenant from JWT
tenant_id = jwt_claims.get('custom:tenant_id')

# Apply metadata filter
tenant_filter = {
    "equals": {
        "key": "tenant_id",
        "value": tenant_id
    }
}

# Query with filtering
response = bedrock_agent_runtime.retrieve_and_generate(
    input={'text': user_query},
    retrieveAndGenerateConfiguration={
        'type': 'KNOWLEDGE_BASE',
        'knowledgeBaseConfiguration': {
            'knowledgeBaseId': kb_id,
            'modelArn': model_arn,
            'retrievalConfiguration': {
                'vectorSearchConfiguration': {
                    'filter': tenant_filter
                }
            }
        }
    }
)
```

## Testing

The notebook includes tests for:
- Tenant A querying auto insurance deductible → Returns $1000
- Tenant B querying auto insurance deductible → Returns $500
- Same query, different results based on tenant_id filter

## Cost Optimization

- Single Knowledge Base for all tenants
- Single OpenSearch Serverless collection
- Metadata filtering at vector DB layer (efficient)
- No per-tenant infrastructure overhead

## Security

- JWT validation at AgentCore Runtime
- Metadata filter enforced at vector database
- No cross-tenant data leakage possible
- Defense-in-depth approach

## Files

- `agentcore-rag-metadata-filtering.ipynb` - End-to-end tutorial
- `rag_metadata_agent.py` - Agent implementation
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration

## Related Examples

- `../identity1/` - Simple authentication with Access Token
- `../identity2/` - Identity propagation with ID Token

## Troubleshooting

### Model ARN Issues

If you see `ValidationException` with `GetInferenceProfile`:
- The agent uses `anthropic.claude-3-sonnet-20240229-v1:0` for RAG
- Make sure this model is enabled in your Bedrock console
- The agent will fallback to direct LLM if RAG fails

### Knowledge Base Not Found

If RAG is not working:
1. Verify `knowledge_base_id` is correct
2. Check KB ingestion job completed successfully
3. Ensure documents have `.metadata.json` files
4. Verify metadata contains `tenant_id` field

### No Results Returned

If queries return no results:
- Check metadata filter matches document metadata exactly
- Verify `tenant_id` in JWT matches document `tenant_id`
- Try querying without filter first to verify documents are indexed

## References

- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Metadata Filtering](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-config.html)
- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Strands Agents](https://github.com/awslabs/strands)
