# 02 - Structured Multi-Tenant RLS with Custom Scopes

Multi-tenant database access using PostgreSQL Row-Level Security (RLS) with OAuth 2.0 Access Tokens and custom scopes.

## What This Demonstrates

- PostgreSQL with Row-Level Security (RLS) for tier isolation
- Access Token with custom scopes (`insurance/regular`, `insurance/platinum`)
- Automatic tier extraction from token scopes
- Database-level tier isolation for structured data
- Production-ready pattern for multi-tenant databases

## When to Use

- Multi-tenant structured data (claims, policies, customer records)
- Relational database with complex queries
- Row-level access control by insurance tier
- Compliance requirements for data isolation
- Production deployments with PostgreSQL

## Architecture

```
Regular User → Access Token (scope: insurance/regular) → AgentCore → Strands Agent
                                                                           ↓
                                                          Extract tier from scope
                                                                           ↓
                                                          SET app.current_tier = 'regular'
                                                                           ↓
                                                          PostgreSQL Query + RLS Policy
                                                                           ↓
                                                          Returns only Regular tier data
```

## Key Components

- **Cognito User Pool** with custom resource server and scopes
- **PostgreSQL RDS** with Row-Level Security policies
- **Strands Agent** with database query tools
- **RLS Policies** that filter by `app.current_tier` session variable
- **AgentCore Runtime** with JWT validation

## Files

- `02-structured-multitenant-rls.ipynb` - Main tutorial notebook
- `rls_agent.py` - Agent implementation with RLS context
- `requirements.txt` - Python dependencies

## Run

```bash
cd notebooks/02-structured-multitenant-rls
jupyter notebook 02-structured-multitenant-rls.ipynb
```

## What You'll Learn

1. How to set up PostgreSQL with Row-Level Security
2. How to create RLS policies for tier-based isolation
3. How to extract tier from Access Token scopes
4. How to set PostgreSQL session variables for RLS context
5. How to build secure multi-tenant database agents

## Database Schema

```sql
CREATE TABLE claims (
    id SERIAL PRIMARY KEY,
    tier VARCHAR(50) NOT NULL,
    claim_number VARCHAR(100),
    amount DECIMAL(10,2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- RLS Policy
CREATE POLICY tier_isolation ON claims
    USING (tier = current_setting('app.current_tier'));
```

## Next Steps

After completing this tutorial:
- **Tutorial 01**: Learn unstructured data access with RAG
- **Tutorial 03**: Build enterprise orchestration with supervisor agents
