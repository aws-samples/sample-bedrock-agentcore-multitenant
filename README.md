# Securing Multi-Tenant Architectures for Agentic AI on AWS

Production-ready implementations demonstrating multi-tenant isolation patterns for agentic AI applications using Amazon Bedrock AgentCore, Strands Agents, and AWS security services with OAuth 2.0 custom scopes.

## Overview

This repository provides a progressive tutorial series for building secure, enterprise-grade multi-tenant agentic AI systems:

1. **01-unstructured-multitenant-rag** - Multi-tenant RAG with custom scopes and metadata filtering
2. **02-structured-multitenant-rls** - Multi-tenant database access with PostgreSQL RLS
3. **03-enterprise-orchestration** - Complete platform with supervisor agent and production UI

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Amazon Cognito User Pools                 │
│  - OAuth 2.0 Authentication                                  │
│  - Custom Resource Server (insurance)                        │
│  - Custom Scopes (insurance/regular, insurance/platinum)     │
└────────────────────────┬────────────────────────────────────┘
                         │ Access Token with scope claim
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Bedrock AgentCore Runtime                       │
│  - Automatic JWT validation                                  │
│  - Identity propagation to agents                            │
│  - Scope forwarding                                          │
└────────────────────────┬────────────────────────────────────┘
                         │ user_identity with scope
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Strands Agents                            │
│  - Extract tier from scope (insurance/regular)               │
│  - Apply tier-based filtering                                │
│  - Maintain tier context                                     │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             ↓                           ↓
┌────────────────────────┐  ┌──────────────────────────┐
│  Knowledge Base        │  │  PostgreSQL Database     │
│  - Metadata filtering  │  │  - Row-Level Security    │
│  - tier: regular       │  │  - SET app.current_tier  │
│  - Vector search       │  │  - Tier-based policies   │
└────────────────────────┘  └──────────────────────────┘
```

## Key Features

- **Production-Ready OAuth 2.0**: Custom scopes for tier-based access control
- **Multi-Tenant Isolation**: Defense-in-depth with multiple isolation layers
- **Unstructured Data**: RAG with metadata filtering by tier
- **Structured Data**: PostgreSQL RLS for row-level tier isolation
- **Enterprise UI**: AWS Cloudscape Design System
- **Supervisor Pattern**: Intelligent multi-agent orchestration
- **Streaming Responses**: Real-time AI interactions
- **Complete Examples**: End-to-end tutorials with working code

## Quick Start

### Prerequisites

- AWS Account with Bedrock access
- Python 3.9+
- Node.js 16+ (for Tutorial 03)
- PostgreSQL (for Tutorial 02)
- Jupyter Notebook

### Installation

```bash
# Clone repository
git clone <repo-url>
cd agentcore-identity-runtime-propagation

# Install dependencies
pip install -r requirements.txt

# Start Jupyter
cd notebooks
jupyter notebook
```

### Run Tutorials

Start with Tutorial 01 and progress sequentially:

```bash
# Tutorial 01: Unstructured Multi-Tenant RAG
cd notebooks/01-unstructured-multitenant-rag
jupyter notebook 01-unstructured-multitenant-rag.ipynb

# Tutorial 02: Structured Multi-Tenant RLS
cd notebooks/02-structured-multitenant-rls
jupyter notebook 02-structured-multitenant-rls.ipynb

# Tutorial 03: Enterprise Orchestration
cd notebooks/03-enterprise-orchestration
jupyter notebook 03-enterprise-orchestration.ipynb
# Or use quick start script:
./start.sh
```

## Tutorials

### 01 - Unstructured Multi-Tenant RAG

Build a multi-tenant RAG system with OAuth 2.0 custom scopes and metadata filtering.

**What You'll Learn**:
- Creating Cognito custom scopes (`insurance/regular`, `insurance/platinum`)
- Building Knowledge Base with OpenSearch Serverless
- Implementing metadata filtering by tier
- Extracting tier from Access Token scopes
- Deploying production-ready RAG agents

**Use Case**: Insurance document access with tier-based isolation

**Pattern**: Access Token (scope) → Metadata Filter → Tier-specific documents

**Time**: 30-45 minutes

[View Tutorial →](notebooks/01-unstructured-multitenant-rag/)

### 02 - Structured Multi-Tenant RLS

Implement PostgreSQL Row-Level Security with custom scopes for structured data.

**What You'll Learn**:
- Setting up PostgreSQL with RLS policies
- Creating tier-based RLS policies
- Extracting tier from Access Token scopes
- Setting PostgreSQL session variables
- Building secure database agents

**Use Case**: Insurance claims database with tier-based access

**Pattern**: Access Token (scope) → RLS Context → Tier-specific rows

**Time**: 30-45 minutes

[View Tutorial →](notebooks/02-structured-multitenant-rls/)

### 03 - Enterprise Orchestration

Build a complete multi-tenant platform with supervisor agent and production UI.

**What You'll Learn**:
- Supervisor agent pattern for intelligent routing
- Multi-agent orchestration
- Full-stack OAuth 2.0 integration
- React + Cloudscape UI development
- Production deployment patterns
- Streaming AI responses

**Use Case**: Complete insurance platform with claims dashboard and AI assistant

**Pattern**: Supervisor Agent → Specialized Agents → Production UI

**Time**: 60-90 minutes

[View Tutorial →](notebooks/03-enterprise-orchestration/)

## Security Patterns

### Authentication (OAuth 2.0)

**Access Tokens with Custom Scopes** (Recommended for Production)
- Standard OAuth 2.0 pattern
- Custom resource server: `insurance`
- Custom scopes: `insurance/regular`, `insurance/platinum`
- Scope included in Access Token
- AgentCore validates JWT automatically

```json
{
  "sub": "user-123",
  "scope": "openid email insurance/regular",
  "token_use": "access"
}
```

### Authorization

**Multi-Layer Defense**:
1. **JWT Validation**: AgentCore Runtime validates token signature and expiration
2. **Scope Extraction**: Agent extracts tier from scope claim
3. **Data Layer Filtering**: 
   - Unstructured: Metadata filtering in Knowledge Base
   - Structured: Row-Level Security in PostgreSQL

### Tier Isolation

**Unstructured Data (Tutorial 01)**:
```python
# Metadata filter applied at vector DB
retrieval_filter = {
    "equals": {
        "key": "tier",
        "value": "regular"  # Extracted from scope
    }
}
```

**Structured Data (Tutorial 02)**:
```sql
-- RLS policy enforces tier isolation
CREATE POLICY tier_isolation ON claims
    USING (tier = current_setting('app.current_tier'));

-- Set from Access Token scope
SET app.current_tier = 'regular';
```

## Project Structure

```
agentcore-identity-runtime-propagation/
├── notebooks/
│   ├── 01-unstructured-multitenant-rag/
│   │   ├── 01-unstructured-multitenant-rag.ipynb
│   │   ├── rag_metadata_agent.py
│   │   ├── README.md
│   │   └── requirements.txt
│   ├── 02-structured-multitenant-rls/
│   │   ├── 02-structured-multitenant-rls.ipynb
│   │   ├── rls_agent.py
│   │   ├── README.md
│   │   └── requirements.txt
│   ├── 03-enterprise-orchestration/
│   │   ├── 03-enterprise-orchestration.ipynb
│   │   ├── backend/              # Flask API
│   │   ├── frontend/             # React + Cloudscape UI
│   │   ├── supervisor_agent.py
│   │   ├── start.sh
│   │   └── README.md
│   └── utils/
│       ├── aws_resources.py      # Reusable AWS utilities
│       └── __init__.py
├── blog/
│   └── securing-multi-tenant-architectures-for-agentic-ai.md
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

## Technologies

### AWS Services
- **Amazon Bedrock AgentCore Runtime** - Agent hosting with JWT validation
- **Amazon Bedrock Knowledge Bases** - RAG with metadata filtering
- **AWS Cognito** - OAuth 2.0 authentication with custom scopes
- **Amazon OpenSearch Serverless** - Vector database
- **Amazon RDS PostgreSQL** - Structured data with RLS

### Frameworks & Libraries
- **Strands Agents** - Agentic AI framework
- **Flask** - Backend API
- **React** - Frontend framework
- **AWS Cloudscape** - Enterprise UI components
- **psycopg2** - PostgreSQL adapter

## Demo Accounts

Each tutorial creates test users for different tiers:

- **Regular Tier**: john-regular@example.com / Pass123!
  - Standard insurance coverage
  - $1000 deductible
  - 5-7 day claim processing

- **Platinum Tier**: sarah-platinum@example.com / Pass123!
  - Premium insurance coverage
  - $500 deductible
  - 24-48 hour priority processing

## Best Practices

### Production Deployment

1. **Security**
   - Use HTTPS with ACM certificates
   - Store secrets in AWS Secrets Manager
   - Enable CloudTrail for audit logging
   - Implement rate limiting
   - Use VPC endpoints for private connectivity

2. **Scalability**
   - Use Auto Scaling for backend services
   - Enable RDS read replicas
   - Implement CloudFront caching
   - Use ElastiCache for session management

3. **Monitoring**
   - CloudWatch for logs and metrics
   - X-Ray for distributed tracing
   - Custom dashboards for business metrics
   - Alerts for error rates and latency

4. **Cost Optimization**
   - Use Bedrock on-demand pricing
   - Implement caching strategies
   - Right-size RDS instances
   - Use S3 lifecycle policies

### Development

1. **Testing**
   - Unit tests for agent tools
   - Integration tests for API endpoints
   - End-to-end tests for UI flows
   - Load testing for scalability

2. **Code Quality**
   - Type hints for Python code
   - ESLint for TypeScript/React
   - Pre-commit hooks
   - Code reviews

## Troubleshooting

### Common Issues

**Authentication Fails**
```bash
# Verify Cognito configuration
aws cognito-idp describe-user-pool --user-pool-id <pool-id>

# Check resource server
aws cognito-idp describe-resource-server \
  --user-pool-id <pool-id> \
  --identifier insurance
```

**Agent Invocation Fails**
```bash
# Check agent status
aws bedrock-agent-runtime get-agent --agent-id <agent-id>

# Verify IAM permissions
aws sts get-caller-identity
```

**Database Connection Issues**
```bash
# Test PostgreSQL connection
psql -h <host> -U <user> -d <database>

# Verify RLS policies
SELECT * FROM pg_policies WHERE tablename = 'claims';
```

## Support & Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Strands Agents Documentation](https://docs.strands.ai/)
- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for security issue notifications.