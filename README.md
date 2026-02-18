# Securing multi-tenant architectures for agentic AI on AWS

When you build a multi-tenant agentic AI application, you need secure data isolation at every layer of the stack to make sure each customer sees only their own data. An insurance claims application, for example, might let brokers ask "How many claims were filed last week?" or "What is the maximum deductible for auto insurance?". The answer must reflect only that broker's customers—not every customer in the database.

This post shows you how to implement **tenant isolation** in agentic AI applications. You'll build a defense-in-depth architecture using **Row-Level Security (RLS)** for structured data, **metadata filtering** for unstructured data with [Amazon Bedrock Knowledge Bases](https://aws.amazon.com/bedrock/knowledge-bases/), and secure tenant context management with [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/). 

You'll work through three hands-on tutorials: a Retrieval Augmented Generation (RAG) pipeline with metadata filtering, a database layer with Row-Level Security, and a web demo that ties both patterns together.

## The challenge: one application, many tenants

Consider an insurance claims application that serves multiple brokers. Each broker asks questions about their customers' claims and policy documents, but they shouldn't see another broker's data. When Broker A asks "How many claims were filed last week?", they should only see their own customers' claims.

<p align="center">
  <img src="./images/portal-policy-agent.png" alt="Policy Agent - RAG with metadata filtering" width="45%"/>
  <img src="./images/portal-claims-agent.png" alt="Claims Agent - RLS with Row-Level Security" width="45%"/>
  <br/>
  <em>Same question, different answers: each broker sees only their own data</em>
</p>

This scenario requires two types of data isolation.

- For **unstructured data** like policy documents, the answer to "What is the maximum deductible?" varies by customer tier.

- For **structured data** like the claims database, query results must be filtered by the broker's tenant.

The solution combines [Amazon Cognito](https://aws.amazon.com/cognito/) for authentication, Amazon Bedrock AgentCore for agent execution, and tenant-aware data access patterns at both the document and database layers.

## How identity propagates through the stack

Maintaining a consistent identity across every component is essential for security and data isolation. This applies whether an agent queries structured data or retrieves unstructured documents.

<p align="center">
  <img src="./images/identity-propagation.png" alt="Identity Propagation Architecture" width="90%"/>
  <br/>
  <em>Identity propagation from Cognito through AgentCore to data layer</em>
</p>

The flow starts when your broker signs in through Amazon Cognito User Pools, which can federate with enterprise identity providers like Microsoft Entra ID or Google. After authentication, Cognito issues a JSON Web Token (JWT) containing standard identity attributes and custom claims such as `tenant_id` and `cognito:groups`. For machine-to-machine authorization, you can use [custom OAuth 2.0 scopes](https://docs.aws.amazon.com/cognito/latest/developerguide/scope-based-multi-tenancy.html) to define tenant-specific access controls.

When your application forwards the request, Amazon Bedrock AgentCore Runtime validates the JWT, confirms it was issued by the trusted Cognito User Pool, and extracts the identity claims. AgentCore binds the tenant context to the agent's runtime session. Every subsequent interaction between agents, tools, and services includes this identity context.

Your [Strands Agent](https://strandsagents.com/latest/) (an open-source SDK for building AI agents) receives the request with the validated identity context. It reads the tenant claims and applies role-based access controls to determine what operations the tenant can perform. For unstructured data, your agent applies metadata-based filtering to limit visibility to resources tagged for that tenant. For structured data, your agent uses Row-Level Security (RLS) so each query runs only against records associated with the authenticated tenant.

This creates a chain of trust from authentication to data access:

1. **Amazon Cognito** verifies the user's identity
2. **AgentCore Runtime** validates the JWT and propagates identity context
3. **Strands Agents** enforce tenant isolation during data retrieval

Now that you understand how identity flows through the stack, let's look at how each data layer enforces isolation.

## Tenant and user data isolation at the data layer

### Unstructured data: metadata filtering

For unstructured data such as policy documents and knowledge base articles, Amazon Bedrock Knowledge Bases provides a managed RAG solution with metadata filtering. This approach uses a single knowledge base with metadata tags to identify document ownership. Each document uploaded to [Amazon S3](https://aws.amazon.com/s3/) includes a corresponding `.metadata.json` file:

```json
{
  "metadataAttributes": {
    "tier": "regular",
    "document_type": "policy"
  }
}
```

During ingestion, Amazon Bedrock Knowledge Bases indexes these metadata fields alongside the document vectors, which allows filtered retrieval at query time.

### Structured data: Row-Level Security

Tenant isolation at the database layer starts with [data partitioning design](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/) decisions. There are three common approaches:

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **Silo** | Separate database instance per tenant | Complete isolation | High operational costs |
| **Bridge** | Shared instance, different schema per tenant | Better resource sharing | Complex management |
| **Pool** | Shared tables with tenant IDs | Cost-efficient | Requires strong security controls |

For more information, see the [AWS SaaS Factory whitepaper](https://d1.awsstatic.com/whitepapers/Multi_Tenant_SaaS_Storage_Strategies.pdf).

Centralizing isolation policies at the data layer reduces the burden on developers. You get the cost benefits of the pool model while reducing the risk of cross-tenant data access. With Row-Level Security (RLS), you define which users or roles can access specific records based on security policies at the database level. The following three tutorials walk you through implementing these patterns step by step.

## Tutorial 1: multi-tenant RAG with metadata filtering

In this tutorial, you implement tenant isolation for unstructured data using Amazon Bedrock Knowledge Bases with metadata filtering based on Cognito groups.

### Architecture

<p align="center">
  <img src="./images/tutorial-01-rag-architecture.png" alt="Tutorial 01 - RAG with Metadata Filtering Architecture" width="90%"/>
</p>

### How it works

1. **User authentication**: User authenticates with Cognito and receives a JWT with group membership (`regular` or `platinum`)
2. **JWT validation**: AgentCore Runtime validates the token signature and expiration
3. **Tier extraction**: The Strands Agent extracts the user's tier from the `cognito:groups` claim
4. **Metadata filtering**: The agent calls `strands_tools.retrieve` with a tier-based filter
5. **Isolated results**: Only documents matching the user's tier are retrieved

### Query-time filtering

The agent extracts the tier from the JWT and applies it as a metadata filter:

```python
# Extract tier from cognito:groups claim
groups = token_claims.get('cognito:groups', [])
tier = groups[0] if groups else 'regular'

# Build metadata filter
retrieval_filter = {
    "equals": {
        "key": "tier",
        "value": tier
    }
}

# Call retrieve with filtering
response = retrieve(
    knowledge_base_id=knowledge_base_id,
    query=user_query,
    retrieval_filter=retrieval_filter
)
```

### Example: same query, different results

| User | Tier | Query | Result |
|------|------|-------|--------|
| john-regular | regular | "What is the deductible for auto insurance?" | $1,000 |
| sarah-platinum | platinum | "What is the deductible for auto insurance?" | $500 |

The vector database layer enforces the metadata filter. Users cannot access documents from other tiers, even with prompt injection attempts.

**[View Tutorial 1 →](https://github.com/aws-samples/sample-bedrock-agentcore-multitenant/tree/main/notebooks/01-unstructured-multitenant-rag)**

## Tutorial 2: multi-tenant database with Row-Level Security

In this tutorial, you implement tenant isolation for structured data using [Aurora Serverless v2](https://aws.amazon.com/rds/aurora/serverless/) PostgreSQL with Row-Level Security.

### Architecture

<p align="center">
  <img src="./images/tutorial-02-rls-architecture.png" alt="Tutorial 02 - Aurora RLS Architecture" width="90%"/>
</p>

### How it works

1. **User authentication**: User authenticates with Cognito and receives a JWT with their `sub` claim
2. **JWT validation**: AgentCore Runtime validates the token
3. **User-tenant lookup**: The agent extracts `sub` from the JWT and looks up the tenant_id from the `user_tenants` table
4. **Session variable**: The agent sets `app.current_tenant_id` PostgreSQL session variable
5. **RLS enforcement**: All queries are automatically filtered by the RLS policy

### Database schema with RLS

```sql
-- User-tenant mapping table
CREATE TABLE user_tenants (
    user_sub VARCHAR(100) PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(tenant_id)
);

-- Claims table with tenant isolation
CREATE TABLE claims (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    claim_number VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    claim_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL
);

-- Enable Row-Level Security
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;

-- RLS Policy: users see only rows matching their tenant
CREATE POLICY tenant_isolation ON claims
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true));
```

### Use non-superuser database accounts

PostgreSQL superusers (like `postgres`) bypass RLS policies. Create a dedicated application user with limited permissions:

```sql
-- Create application user (non-superuser)
CREATE USER app_user WITH PASSWORD 'secure_password';

-- Grant limited permissions
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT ON claims, tenants, user_tenants TO app_user;
```

### Example: tenant-isolated claims

| User | Tenant | Query | Visible Claims |
|------|--------|-------|----------------|
| mike-broker-a | broker-a | "Show me all claims" | CLM-A-001, CLM-A-002, CLM-A-003 |
| emma-broker-b | broker-b | "Show me all claims" | CLM-B-001, CLM-B-002 |

The RLS policy enforces isolation at the database engine level, blocking SQL injection and prompt manipulation attempts before they can reach other tenants' data.

**[View Tutorial 2 →](https://github.com/aws-samples/sample-bedrock-agentcore-multitenant/tree/main/notebooks/02-structured-multitenant-rls)**

## Tutorial 3: enterprise demo application

In this tutorial, you build a web interface demonstrating both agents with Cognito authentication.

### Architecture

<p align="center">
  <img src="./images/tutorial-03-demo-architecture.png" alt="Tutorial 03 - Enterprise Demo Architecture" width="90%"/>
</p>

### Invoking AgentCore with OAuth tokens

When integrating agents with OAuth authentication, use direct HTTPS requests to the `InvokeAgentRuntime` API. The AWS SDK does not support passing bearer tokens for user authentication.

The `InvokeAgentRuntime` API accepts a bearer token in the `Authorization` header. The agent uses this token to authenticate the end user and extract tenant context from the JWT claims. For details, see [Invoke an AgentCore Runtime agent](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-invoke-agent.html).

```python
# Direct HTTPS call with OAuth token
endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations"
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {access_token}'
}
response = requests.post(endpoint, json={'prompt': prompt}, headers=headers)
```

**[View Tutorial 3 →](https://github.com/aws-samples/sample-bedrock-agentcore-multitenant/tree/main/notebooks/03-enterprise-orchestration)**

## Security best practices

### Defense in depth

The architecture implements multiple security layers. If one layer allows unintended access, additional controls prevent unauthorized data exposure:

| Layer | Component | Security Control |
|-------|-----------|------------------|
| Authentication | Amazon Cognito | JWT issuance with tenant claims |
| Runtime | AgentCore | JWT signature validation, expiration check |
| Agent | Strands Agent | Tenant context extraction and validation |
| Data (Structured) | PostgreSQL RLS | Row-level filtering by tenant |
| Data (Unstructured) | Knowledge Base | Metadata filtering by tenant |

### Key considerations

1. **Use non-superuser database accounts**: PostgreSQL superusers bypass RLS. Create dedicated application users with limited permissions.

2. **Validate tenant context at every layer**: Don't trust upstream validation alone. Each component should verify the tenant context independently.

3. **Log access attempts**: Enable CloudTrail and database audit logging for compliance and forensic analysis.

4. **Test isolation**: Verify that prompt injection and SQL injection attempts are blocked by your security controls.

5. **Use VPC endpoints for private connectivity**: For production deployments, VPC endpoints keep traffic within the AWS network.

## Conclusion

Building secure multi-tenant agentic AI applications requires defense in depth: identity propagation, data isolation, and runtime security controls working together.

The architecture in this post provides security through multiple layers. Amazon Cognito handles authentication with tenant context in JWT claims. AgentCore Runtime validates JWT integrity and forwards identity context. Strands Agents manage tenant context propagation. Row-level security policies filter structured data at the database layer. Metadata filtering isolates unstructured data at the vector database layer.

The pool-based data partitioning model balances cost-efficiency and security for most multi-tenant scenarios. If one security layer allows unintended access, additional controls prevent unauthorized data exposure.

## Get started

Explore the working examples in our [GitHub repository](https://github.com/aws-samples/sample-bedrock-agentcore-multitenant).

The repository includes three tutorials:

- **01-unstructured-multitenant-rag**: RAG with Cognito groups and metadata filtering
- **02-structured-multitenant-rls**: Aurora Serverless v2 with Row-Level Security
- **03-enterprise-orchestration**: Web demo with Cloudscape UI

## Additional resources

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Metadata Filtering in Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-config.html)
- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [Multi-tenant Data Isolation with PostgreSQL RLS](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)
- [AWS Prescriptive Guidance: Multi-Tenant Agentic AI](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-multitenant/)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

## Security

See [SECURITY.md](SECURITY.md) for security considerations and [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for security issue notifications.

**Important**: This repository contains demonstration code for educational purposes. Review [SECURITY.md](SECURITY.md) before using any code in production environments.
