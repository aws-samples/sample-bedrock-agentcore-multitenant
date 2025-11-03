# Securing Multi-Tenant Architectures for Agentic AI on AWS

This repository contains complete working examples demonstrating how to implement robust tenant isolation in agentic AI applications using Amazon Bedrock AgentCore, Strands Agents, and AWS security services.

## Overview

Organizations integrating agentic AI capabilities into multi-tenant applications need to ensure that each tenant's data remains strictly isolated. This repository demonstrates three progressive patterns for implementing secure multi-tenant agentic AI:

1. **Simple Authentication** - Basic JWT authentication with Access Tokens
2. **Identity Propagation** - Multi-tenant identity with ID Tokens and custom attributes
3. **RAG with Metadata Filtering** - Multi-tenant RAG using Amazon Bedrock Knowledge Bases

## Architecture

```
┌─────────────────┐
│  Amazon Cognito │  ← Authentication with tenant_id
│   User Pools    │
└────────┬────────┘
         │ JWT (ID Token)
         ▼
┌─────────────────┐
│  Bedrock        │  ← Validates JWT, forwards identity
│  AgentCore      │
│  Runtime        │
└────────┬────────┘
         │ Authorization header
         ▼
┌─────────────────┐
│  Strands Agent  │  ← Extracts tenant_id, applies filters
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌──────────────┐
│Database│  │Knowledge Base│  ← Row-Level Security & Metadata Filtering
│  RLS   │  │   Metadata   │
└────────┘  └──────────────┘
```

## Examples

### identity1: Simple Authentication with Access Token

Basic OAuth 2.0 authentication using Access Tokens.

**Use Case**: Single-tenant applications or basic user identification

**Key Features**:
- Standard OAuth 2.0 Access Token flow
- Basic user identity (sub, username)
- AgentCore JWT validation with `allowedClients`

**Run**: `jupyter notebook identity1/agentcore-simple-authentication-accesstoken.ipynb`

### identity2: Identity Propagation with ID Token

Multi-tenant authentication using ID Tokens with custom attributes.

**Use Case**: Multi-tenant applications requiring custom user attributes

**Key Features**:
- ID Token with custom attributes (tenant_id, user_role)
- Identity propagation through AgentCore
- Role-based access control (RBAC)
- AgentCore JWT validation with `allowedAudience`

**Run**: `jupyter notebook identity2/agentcore-identity-propagation-multitenant-idtoken.ipynb`

### identity3: Multi-Tenant RAG with Metadata Filtering

End-to-end multi-tenant RAG using Amazon Bedrock Knowledge Bases.

**Use Case**: Multi-tenant applications with unstructured data (documents, policies)

**Key Features**:
- Single Knowledge Base with metadata filtering
- Pool-based multi-tenancy (cost-efficient)
- Tenant isolation at vector database layer
- S3 document metadata (`.metadata.json` files)
- Query-time filtering with RetrieveAndGenerate API

**Run**: `jupyter notebook identity3/agentcore-rag-metadata-filtering.ipynb`

## Quick Start

### Prerequisites

- AWS Account with Amazon Bedrock access
- Python 3.10+
- Docker (for local testing)
- AWS CLI configured

### Installation

```bash
# Clone the repository
git clone https://github.com/aws-samples/bedrock-agentcore-multitenant
cd bedrock-agentcore-multitenant

# Install dependencies for any example
cd identity1  # or identity2, identity3
pip install -r requirements.txt

# Run the notebook
jupyter notebook
```

### Running Examples

Each example is self-contained and includes:
- Jupyter notebook with step-by-step instructions
- Python agent implementation
- Dockerfile for containerization
- README with detailed documentation

All notebooks are **idempotent** and can be run multiple times safely.

## Key Concepts

### Token Types

| Token Type | Contains | Use Case | AgentCore Config |
|------------|----------|----------|------------------|
| **Access Token** | `sub`, `username`, `client_id` | Basic auth | `allowedClients` |
| **ID Token** | `sub`, `username`, `aud`, **custom attributes** | Multi-tenant | `allowedAudience` |

### Multi-Tenancy Patterns

| Pattern | Isolation Level | Cost | Complexity | Use Case |
|---------|----------------|------|------------|----------|
| **Silo** | Complete | High | High | Largest tenants, strict compliance |
| **Pool** | Logical | Low | Low | Many small tenants |
| **Bridge** | Moderate | Medium | Medium | Mixed tenant sizes |

This repository demonstrates the **Pool** pattern with:
- Row-Level Security (RLS) for structured data
- Metadata filtering for unstructured data

### Metadata Filtering

Documents in S3 require corresponding `.metadata.json` files:

```json
{
  "metadataAttributes": {
    "tenant_id": "tenant-a",
    "document_type": "policy"
  }
}
```

File naming: `document.txt` → `document.txt.metadata.json`

Query-time filtering:

```python
tenant_filter = {
    "equals": {
        "key": "tenant_id",
        "value": extracted_tenant_id
    }
}
```

## Security Features

### Defense-in-Depth

1. **Authentication Layer**: Amazon Cognito with JWT tokens
2. **Runtime Layer**: AgentCore validates JWT and forwards identity
3. **Application Layer**: Strands Agent extracts and validates tenant context
4. **Data Layer**: 
   - Row-Level Security for databases
   - Metadata filtering for Knowledge Bases

### Identity Propagation Flow

```
User → Cognito (JWT) → AgentCore (validates) → Strands Agent (extracts) → Data Layer (filters)
```

## Cost Optimization

The pool-based approach demonstrated here provides significant cost savings:

- **Single Knowledge Base** for all tenants (vs. N knowledge bases)
- **Single OpenSearch Serverless collection** (vs. N collections)
- **Shared compute resources** with logical isolation
- **Metadata filtering** at vector DB layer (efficient)

## Blog Post

Read the accompanying blog post: [Securing multi-tenant architectures for agentic AI on AWS](./Securing%20multi-tenant%20architectures%20for%20agentic%20AI%20on%20AWS.md)

## Repository Structure

```
.
├── README.md                          # This file
├── Securing multi-tenant architectures for agentic AI on AWS.md  # Blog post
├── identity1/                         # Simple authentication
│   ├── agentcore-simple-authentication-accesstoken.ipynb
│   ├── simple_auth_agent.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── identity2/                         # Identity propagation
│   ├── agentcore-identity-propagation-multitenant-idtoken.ipynb
│   ├── identity_aware_agent.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
└── identity3/                         # RAG with metadata filtering
    ├── agentcore-rag-metadata-filtering.ipynb
    ├── rag_metadata_agent.py
    ├── requirements.txt
    ├── Dockerfile
    └── README.md
```

## Testing

Each example includes comprehensive tests:

- Authentication validation
- Token type verification (Access vs ID)
- Multi-tenant isolation
- Metadata filtering effectiveness
- Cross-tenant access prevention

## Troubleshooting

### Common Issues

1. **JWT validation fails**: Ensure `allowedAudience` (ID Token) or `allowedClients` (Access Token) matches your Cognito client ID

2. **Authorization header not forwarded**: Add `requestHeaderAllowlist: ['Authorization']` to `.bedrock_agentcore.yaml`

3. **Metadata filtering not working**: Verify `.metadata.json` files are uploaded with correct naming convention

4. **Knowledge Base ingestion fails**: Check IAM role permissions for S3 and Bedrock access

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

## References

- [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Strands Agents](https://github.com/awslabs/strands)
- [Amazon Cognito](https://docs.aws.amazon.com/cognito/)
- [Multi-tenant SaaS on AWS](https://aws.amazon.com/saas/)

## Support

For issues and questions:
- Open an issue in this repository
- Contact AWS Support
- Visit AWS re:Post

---

**Note**: These examples are for educational purposes. For production deployments, implement additional security controls, monitoring, and compliance measures appropriate for your use case.
