# 01 - Unstructured Multi-Tenant RAG with Custom Scopes

Multi-tenant RAG system using OAuth 2.0 Access Tokens with custom scopes for insurance tier isolation.

## What This Demonstrates

- Access Token with custom scopes (`insurance/regular`, `insurance/platinum`)
- Metadata-based tier isolation at vector DB layer
- Pooled Knowledge Base architecture (cost-efficient)
- Document-level access control by insurance tier
- Production-ready OAuth 2.0 pattern

## When to Use

- Multi-tenant SaaS applications
- Unstructured document repositories (policies, claims, benefits)
- Tier-based access control (regular vs premium customers)
- Shared infrastructure with strict data isolation
- Production deployments requiring OAuth 2.0 compliance

## Architecture

```
Regular User → Access Token (scope: insurance/regular) → AgentCore → Strands Agent
                                                                           ↓
                                                             RetrieveAndGenerate API
                                                             + filter: {tier: regular}
                                                                           ↓
                                                             Knowledge Base (pooled)
                                                             ├─ Regular Policy {tier: regular} ✓
                                                             ├─ Platinum Policy {tier: platinum} ✗
                                                             └─ Regular Claims {tier: regular} ✓
```

## Key Components

- **Cognito User Pool** with custom resource server and scopes
- **OpenSearch Serverless** for vector storage
- **Bedrock Knowledge Base** with metadata filtering
- **Strands Agent** that extracts tier from Access Token scopes
- **AgentCore Runtime** with JWT validation

## Files

- `01-unstructured-multitenant-rag.ipynb` - Main tutorial notebook
- `rag_metadata_agent.py` - Agent implementation with scope-based filtering
- `requirements.txt` - Python dependencies

## Run

```bash
cd notebooks/01-unstructured-multitenant-rag
jupyter notebook 01-unstructured-multitenant-rag.ipynb
```

## What You'll Learn

1. How to create Cognito custom scopes for multi-tenant applications
2. How to build a complete Knowledge Base infrastructure
3. How to implement metadata filtering for tier isolation
4. How to extract and use scopes from Access Tokens in agents
5. How to deploy production-ready multi-tenant RAG systems

## Next Steps

After completing this tutorial:
- **Tutorial 02**: Learn structured data access with PostgreSQL RLS
- **Tutorial 03**: Build enterprise orchestration with supervisor agents
