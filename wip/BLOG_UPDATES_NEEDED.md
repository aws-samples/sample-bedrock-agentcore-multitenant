# Blog Updates Needed

## Section to Update: "Structured data sources" (Line ~70-78)

### Current Text (to replace):
```
Consider a query "How many claims were filed last week?".

_<Modify above diagram to show our architecture elements_ _+ DB schema and isolation_

Broker authenticate and authorize from the built-in user directory, from insurance providers;s enterprise directory, or from consumer identity providers like Google and Facebook using Amazon Cognito User pools.  Executor agent A is built using Strands agent that has access to Claims database. …Talk about agentcore runtime and benefits. Talk about DB RLS and more.<

<Add description of different security features od this architecture. Highlifht it in the diagram.
```

### New Text (to insert):
```markdown
Consider a query "How many claims were filed last week?" where brokers need to access claims data from a shared database.

Brokers authenticate through Amazon Cognito User Pools, which can federate with enterprise identity providers. The executor agent, built using Strands, has access to the Claims database with Row-Level Security (RLS) policies that automatically filter data based on the authenticated tenant.

**Example: Database Query with Tenant Isolation**

| User | Tenant ID | Query | Database Filter | Result |
|------|-----------|-------|----------------|--------|
| broker-a | tenant-a | "How many claims were filed last week?" | `WHERE tenant_id = 'tenant-a'` | 5 claims |
| broker-b | tenant-b | "How many claims were filed last week?" | `WHERE tenant_id = 'tenant-b'` | 2 claims |

The database RLS policy automatically applies tenant filtering:

```sql
-- PostgreSQL Row-Level Security Policy
CREATE POLICY tenant_isolation ON claims
    USING (tenant_id = current_setting('app.current_tenant'));

-- When broker-a queries, RLS automatically adds:
-- WHERE tenant_id = 'tenant-a'
```

The agent extracts tenant context from JWT and sets the database session variable, ensuring all queries are automatically scoped to the correct tenant without requiring application-level filtering logic.
```

### Also Update: "Flow Description" section (Line ~80-95)

Replace the existing flow description with:

```markdown
**Flow Description:**

1. **User Authentication**: User authenticates and receives a JWT with tenant context
2. **Natural Language Query**: User submits a natural language query to the application
3. **JWT Validation**: AgentCore validates JWT and extracts tenant information
4. **Agent Session Creation**: Strands Agent receives tenant context from AgentCore
5. **Intelligent Processing**: Agent processes the query using built-in conversation management
6. **Secure Tool Execution**: Agent invokes database tools with tenant context
7. **Database Query**: Tools execute tenant-aware queries with Row-Level Security
8. **Secure Response**: Results flow back to user with tenant context preserved throughout

Throughout this flow, tenant isolation is maintained at multiple layers:

- **Authentication layer** with JWT claims containing tenant context
- **AgentCore Runtime** validates JWT and forwards identity
- **Agent state management** with Strands' built-in state persistence
- **Database layer** with Row-Level Security policies

Even if a malicious user attempted to prompt the agent to access another tenant's data, the security controls at multiple layers would prevent any unauthorized access.
```

## Summary of Changes

### Added:
1. ✅ **Workflow 2 (Unstructured)**: User permissions table (broker-a vs broker-b)
2. ✅ **Workflow 2 (Unstructured)**: Code execution example with results
3. ⏳ **Workflow 1 (Structured)**: User permissions table (needs manual update)
4. ⏳ **Workflow 1 (Structured)**: SQL RLS example (needs manual update)
5. ⏳ **Flow Description**: Cleaned up and simplified (needs manual update)

### Benefits:
- Clear comparison between tenants
- Concrete examples with actual values ($1000 vs $500, 5 claims vs 2 claims)
- Shows same query → different results based on tenant
- Demonstrates automatic filtering at infrastructure level
- AWS blog style: concise, visual (tables), code snippets

## Manual Steps Required:

1. Open `Securing multi-tenant architectures for agentic AI on AWS.md`
2. Find line ~70 starting with "Consider a query..."
3. Replace the placeholder text with the new content from above
4. Find line ~80 "Flow Description"
5. Replace with the cleaned up version above
6. Save and verify formatting

## Alternative: Use the prepared file

The complete updated section is available in `workflow1_update.txt` - you can copy/paste from there.
