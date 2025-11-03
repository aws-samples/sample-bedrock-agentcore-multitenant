
--  
Organizations are integrating agentic AI capabilities into their applications to improve business processes to perform sophisticated workflows with accuracy. As these applications serve multiple tenants it is important to ensure that capabilities of the agent and its ability to acquire knowledge would be limited to the scope of a given customer's environment. 

For example, an insurance claims platform might want to allow multiple brokers to ask questions like “how many claims were filed yesterday?” or “what is the maximum allowed deductible for auto insurance?”. The system needs to understand the queries and execute agents to generate response and ensure that each tenant (in this case an insurance broker) sees only their customer’s data.  
  

In this blog post, we'll demonstrate how to implement robust tenant isolation in agentic AI applications that query different types of data sources (structured and unstructured). You'll learn a defense-in-depth approach with combining row-level security at the database and metadata filtering for unstructured data sources with secure tenant context management throughout the application stack using Amazon Bedrock AgentCore runtime and Strands' built-in state management and security features.

# Multi-Agents Architecture Overview

An insurance claims platform is used by multiple insurance brokers to access claims information, policy documents for their customers. The system has access to claims database that holds claims information for all the claims processed by insurance provider. It also has access to policy documents for all the customers. It is important to make sure that each insurance broker has access to claims, policy documents, claims history of their own customers only.

This is a multi-tenant agentic AI that is built to answer a variety of questions from brokers, that require execution of sophisticated workflows without human intervention. This comprises of a supervisor agent and executor agents to extract information from different knowledge sources. These are tenant context aware agents that receive the context information of tenant (in this case insurance brokers) at the time of the call. The context is passed between the agents and is carried all the way to knowledge layers.

_<Add an intro para to talk about two queries and a complex query that uses both the execuotor agents>_  Talk about what supervisor and executor agents do. Agent A is a text to SQL implementation that takes the user query from supervisor agent and also gets the tenant context from supervisor to draft a tenant aware query to the DB. Agent B Is a agent that can access Divide the two workflow.


Identity aware authorization is enabled through JWT tokens propagation between the agents. <add another line as to how agents translate this to a particular tenant> A pool-based data partitioning model is enforced at the DB layer to save on the most on operational costs and reduces your infrastructure code and maintenance overhead. Row level security is implemented to enforce data access to a particular tenant. Metadata filtering is used for unstructured data sources to control access for a specific tenant.  

## How identity is propagated from the application stack

In a multi-tenant environment such as the insurance claims platform, maintaining a consistent identity across every component of the system is essential for both security and data isolation.  
This model applies to all types of workloads—whether an agent is querying structured data or retrieving unstructured documents.


  
The flow starts when a broker signs in through Amazon Cognito User Pools, which can federate with enterprise identity providers like Microsoft Entra ID (Azure AD) or Google. After authentication, Cognito issues a tenant-aware JSON Web Token (JWT) that contains standard identity attributes along with custom claims such as tenant_id and role.  
  
When the broker initiates a request, it is processed by the AWS Bedrock AgentCore runtime. AgentCore validates the JWT to confirm that it was issued by the trusted Cognito User Pool and extracts the relevant identity claims.

 It then binds the tenant context to the agent’s runtime session, establishing a trusted AgentCore identity. This identity context is automatically included in every subsequent interaction between agents, tools, and services, ensuring that all actions within the session occur under the same verified tenant context. AgentCore runtime also forwards the customer header downstream, allowing other agents or connected services to operate securely within this trusted identity boundary.  
  
The Strands Agent receives the request along with the propagated identity context. It interprets the JWT claims and applies role-based access controls (RBAC) to determine what operations the authenticated tenant is permitted to perform. For structured data, these controls are enforced through Row-Level Security (RLS), ensuring that each query runs only against records associated with the authenticated tenant. For unstructured data—such as policy documents, knowledge embeddings, or retrieved content—the same tenant identity is applied through metadata-based filtering, which limits visibility to only those resources tagged for that tenant.  
  
This approach creates a continuous chain of trust from authentication to data access. Cognito establishes the root of trust by verifying the user’s identity. Bedrock AgentCore runtime extends that trust through runtime validation and session-level propagation. Strands Agents complete the loop by enforcing authorization policies and tenant isolation during data retrieval and processing.

Together, these layers ensure that every agentic interaction whether generating a response, executing a query, or retrieving information is securely bound to the user’s verified identity and tenant context. By standardizing how identity is validated and propagated across agents, the architecture ensures strong data isolation without increasing operational complexity.

  
Brokers across different organizations can interact with the same system and ask similar business questions, such as “How many claims were filed last week?” or “What’s the deductible limit for my auto insurance policies?”, yet each broker only sees information belonging to their own tenant.  
  
~~With identity and tenant isolation firmly established, we will look at how these mechanisms apply in real-world broker scenarios using both structured and unstructured data workflows.~~

### How tenant and user data is isolated at data layer

### Structured data sources

Tenant and user data isolation at database layer starts with [Data partitioning design](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/) decisions in multi-tenant systems. These are silo, bridge and pool. Consider below pros and cons of how each design enforces isolation. 

1.     **Silo:** A separate database instance per tenant. This approach achieves complete isolation but high operational costs

2. **Bridge:** partition tenant data is to share the same database instance but use a _different schema_ for each tenant. This offers better resource sharing but complex management
3. **Pool:** This approach uses Shared tables with tenant IDs. This approach Efficient but requires robust security controls

For more information about multi-tenant data partitioning, see [AWS SaaS Factory whitepaper](https://d1.awsstatic.com/whitepapers/Multi_Tenant_SaaS_Storage_Strategies.pdf).<need to get new link>

By centralizing the enforcement of RDBMS isolation policies at the data layer you ease the burden on your software developers. This allows you to take advantage of the benefits of the pool model _and_ reduce the risk of cross-tenant data access. Using Row-Level Security (RLS), you can have granular access control over your sensitive data. You can decide which users or roles can access specific records of data within schemas or tables, based on security policies that are defined at the database objects level.  For more information on RLS implementation, see blogs [Multi-tenant data isolation with PostgreSQL Row Level](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/) Security and [achieve fine-grained data security with row-level access control in Amazon Redshift.](https://aws.amazon.com/blogs/big-data/achieve-fine-grained-data-security-with-row-level-access-control-in-amazon-redshift/)

### Unstructured data sources

For unstructured data such as policy documents, compliance guides, and knowledge base articles, Amazon Bedrock Knowledge Bases provides a fully managed RAG solution with built-in metadata filtering capabilities. This enables tenant isolation at the document level without requiring separate knowledge bases per tenant.

The pool-based approach uses a single knowledge base with metadata tags to identify document ownership. Each document uploaded to Amazon S3 includes a corresponding `.metadata.json` file that specifies the tenant ID and other attributes. During ingestion, Amazon Bedrock Knowledge Bases automatically indexes these metadata fields alongside the document vectors, enabling efficient filtered retrieval at query time.

When a broker queries the system, the application enforces tenant isolation by including metadata filters in the `RetrieveAndGenerate` API call. This ensures that only documents tagged with the authenticated user's tenant ID are retrieved and used for response generation. The metadata filtering happens at the vector database layer, providing both security and performance benefits by reducing the search space to tenant-specific documents only.

### Structured data sources

Consider a query “How many claims were filed last week?”.

_<Modify above diagram to show our architecture elements_ _+ DB schema and isolation_

Broker authenticate and authorize from the built-in user directory, from insurance providers;s enterprise directory, or from consumer identity providers like Google and Facebook using Amazon Cognito User pools.  Executor agent A is built using Strands agent that has access to Claims database. …Talk about agentcore runtime and benefits. Talk about DB RLS and more.<

<Add description of different security features od this architecture. Highlifht it in the diagram.

**Flow Description <modify to include agentcore>:**

1. **User Authentication**: User authenticates and receives a JWT with tenant context
2. **Natural Language Query**: User submits a natural language query to the application
3. **JWT Validation**: Application validates JWT and extracts tenant information
4. **Agent Session Creation**: Application creates a Strands Agent session with tenant context in agent state
5. **Intelligent Processing**: Strands Agent processes the query using its built-in conversation management and tool orchestration
6. **Secure Tool Execution**: Agent invokes MCP tools with tenant context securely propagated through agent state
7. **Database Query**: MCP tools execute tenant-aware queries against database with Row-Level Security
8. **Secure Response**: Results flow back to user with appropriate tenant context preserved throughout

Need someone to evaluate the need of MCP for this?

[https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-multitenant/enforcing-tenant-isolation.html](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-multitenant/enforcing-tenant-isolation.html) MCP for multi tenancy and how that will work in this settins?

Throughout this flow, tenant isolation is maintained at multiple layers:

- **Authentication layer** with JWT claims containing tenant context
- **Application layer** with explicit tenant context validation
- **Agent state management** with Strands' built-in state persistence
- **MCP tool layer** with automatic tenant context injection
- **Database layer** with Row-Level Security policies

Even if a malicious user attempted to prompt the agent to access another tenant's data, the security controls at multiple layers would prevent any unauthorized access

### Workflow 2: Identity propagation and tenant isolation for unstructured data sources

Consider a query "What is the maximum deductible for auto insurance?" where information is stored in policy documents that vary by broker. The system uses Amazon Bedrock Knowledge Bases with metadata filtering to ensure each broker only accesses their own documents.

**Document Upload with Metadata**

Each policy document uploaded to S3 includes a corresponding `.metadata.json` file that specifies tenant ownership:

```json
{
  "metadataAttributes": {
    "tenant_id": "broker-a",
    "document_type": "policy",
    "region": "us-east-1"
  }
}
```

The metadata file must follow the naming convention `<filename>.metadata.json` and be stored in the same S3 location as the source document. During ingestion, Amazon Bedrock Knowledge Bases automatically indexes these metadata fields alongside the document vectors.

**Query-Time Filtering**

The Strands agent extracts `tenant_id` from the JWT token and applies it as a metadata filter when calling the RetrieveAndGenerate API:

```python
# Extract tenant_id from JWT claims
tenant_id = jwt_claims.get('custom:tenant_id')

# Build metadata filter
tenant_filter = {
    "equals": {
        "key": "tenant_id",
        "value": tenant_id
    }
}

# Call RetrieveAndGenerate with filtering
response = bedrock_agent_runtime.retrieve_and_generate(
    input={'text': user_query},
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
```

**Example: Multi-Tenant Isolation in Action**

Consider two insurance brokers querying the same question with different results based on their tenant context:

| User     | Tenant ID | User Role | Query                                                | Result                           |
| -------- | --------- | --------- | ---------------------------------------------------- | -------------------------------- |
| broker-a | tenant-a  | admin     | "What is the maximum deductible for auto insurance?" | $1,000 (from tenant-a documents) |
| broker-b | tenant-b  | user      | "What is the maximum deductible for auto insurance?" | $500 (from tenant-b documents)   |

The agent code automatically extracts the tenant context and applies filtering:

```python
# Agent extracts identity from JWT
user_identity = {
    'tenant_id': 'tenant-a',  # Extracted from JWT
    'user_role': 'admin',
    'username': 'broker-a'
}

# Query with tenant filter
response = retrieve_and_generate(
    query="What is the maximum deductible?",
    filter={"equals": {"key": "tenant_id", "value": "tenant-a"}}
)
# Returns: "The maximum deductible for auto insurance is $1,000..."
```

When broker-b queries with the same question, the system automatically applies `tenant_id: tenant-b` filter, returning their specific policy information ($500 deductible). This ensures complete data isolation without requiring application-level logic.

This pool-based approach with metadata filtering provides cost-efficient multi-tenancy while maintaining strict security boundaries. The metadata filter is enforced at the vector database layer, making it impossible for one tenant to access another tenant's documents even if they craft malicious queries. For complete implementation details, see the [sample code repository](https://github.com/aws-samples/bedrock-agentcore-multitenant).

## Conclusion

Building secure multi-tenant agentic AI applications requires a comprehensive defense-in-depth approach that combines identity propagation, data isolation, and runtime security controls. The architecture demonstrated in this post provides strong security guarantees through multiple layers of protection:

1. **Authentication and authorization** with tenant context in JWT claims propagated through Amazon Cognito
2. **AgentCore Runtime validation** ensuring JWT integrity and forwarding identity context
3. **Strands Agent state management** for secure tenant context propagation between agents
4. **Row-level security policies** enforced at the database layer for structured data
5. **Metadata filtering** at the vector database layer for unstructured data
6. **Comprehensive audit logging** for monitoring and compliance

This approach enables organizations to build secure, compliant agentic AI applications that serve multiple tenants while maintaining strict data isolation. By leveraging Amazon Bedrock AgentCore's built-in security features alongside proven database security patterns and Knowledge Bases metadata filtering, you can create applications that scale securely across multiple tenants without sacrificing performance or increasing operational complexity.

The pool-based data partitioning model demonstrated here provides the optimal balance of cost-efficiency and security for most multi-tenant scenarios, while the defense-in-depth approach ensures that even if one security layer is compromised, additional controls prevent unauthorized data access.

## Next Steps

Ready to implement these patterns in your own multi-tenant agentic AI application? Explore the complete working examples in our [GitHub repository](https://github.com/aws-samples/bedrock-agentcore-multitenant), which includes:

- **identity1/**: Simple authentication with Access Token
- **identity2/**: Identity propagation with ID Token and custom attributes
- **identity3/**: Multi-tenant RAG with metadata filtering

Additional resources:

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Metadata Filtering in Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-config.html)
- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [Multi-tenant Data Isolation with PostgreSQL RLS](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)
- [AWS SaaS Factory Multi-Tenancy Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-multitenant/)