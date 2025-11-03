# 03 - Enterprise Multi-Agent Orchestration

Complete multi-tenant insurance platform with supervisor agent orchestration, production-ready UI, and enterprise-grade architecture.

## Overview

This tutorial brings together the specialized agents from Tutorials 01 and 02 under a supervisor agent, providing a production-ready web application for multi-tenant insurance operations. You'll learn how to build enterprise-grade orchestration with proper authentication, routing, and UI integration.

## What This Demonstrates

- **Supervisor Agent Pattern**: Intelligent routing to specialized agents
- **Multi-Agent Orchestration**: Coordinating RAG and RLS agents
- **Production UI**: AWS Cloudscape Design System
- **Enterprise Authentication**: OAuth 2.0 with custom scopes
- **Full-Stack Integration**: React frontend + Flask backend + Strands agents
- **Tenant Context Propagation**: Maintaining tier context across the stack

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Cloudscape UI)                  │
│  - Login with Cognito                                        │
│  - Claims Dashboard                                          │
│  - AI Chat Assistant                                         │
│  - Tier-specific views                                       │
└────────────────────────┬────────────────────────────────────┘
                         │ Access Token (scope: insurance/regular)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (Flask)                       │
│  - JWT validation                                            │
│  - Tier extraction from scope                                │
│  - Request routing                                           │
└────────────────────────┬────────────────────────────────────┘
                         │ Tier context
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Supervisor Agent (AgentCore Runtime)            │
│  - Query understanding                                       │
│  - Agent selection                                           │
│  - Response orchestration                                    │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             ↓                           ↓
┌────────────────────────┐  ┌──────────────────────────┐
│  RAG Agent (Tutorial 01)│  │ RLS Agent (Tutorial 02)  │
│  - Policy documents     │  │ - Claims database        │
│  - Benefits info        │  │ - Customer records       │
│  - Metadata filtering   │  │ - Row-level security     │
└────────────────────────┘  └──────────────────────────┘
```

## Key Components

### Frontend (React + Cloudscape)
- AWS Cloudscape Design System for enterprise UI
- Cognito authentication flow
- Claims dashboard with real-time data
- AI chat interface with streaming responses
- Tier-specific data visualization

### Backend (Flask API)
- JWT token validation
- Tier extraction from Access Token scopes
- RESTful API endpoints
- Supervisor agent integration
- Error handling and logging

### Supervisor Agent (Strands)
- Intelligent query routing
- Tool orchestration
- Tier context maintenance
- Streaming response handling
- Multi-agent coordination

## Files

```
03-enterprise-orchestration/
├── 03-enterprise-orchestration.ipynb   # Main tutorial notebook
├── backend/
│   ├── app.py                          # Flask API server
│   ├── config.py                       # Configuration management
│   ├── cognito_service.py              # Authentication service
│   └── requirements.txt                # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx                     # Main application
│   │   ├── components/                 # UI components
│   │   │   ├── LoginPage.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── ChatInterface.tsx
│   │   ├── services/                   # API services
│   │   └── utils/                      # Utilities
│   ├── package.json
│   └── README.md
├── supervisor_agent.py                 # Supervisor agent implementation
├── start.sh                            # Quick start script
└── README.md                           # This file
```

## Prerequisites

Before starting this tutorial, you should have completed:
- **Tutorial 01**: Unstructured Multi-Tenant RAG
- **Tutorial 02**: Structured Multi-Tenant RLS

You'll also need:
- Node.js 16+ and npm
- Python 3.9+
- AWS credentials configured
- Agents from Tutorials 01 & 02 deployed

## Quick Start

### Option 1: Run from Notebook (Recommended)

```bash
cd notebooks/03-enterprise-orchestration
jupyter notebook 03-enterprise-orchestration.ipynb
```

Then run all cells in order.

### Option 2: Run from Script

```bash
cd notebooks/03-enterprise-orchestration
./start.sh
```

Then open http://localhost:3000

## Demo Accounts

The tutorial creates test users for each tier:

- **Regular Tier**: john-regular@example.com / Pass123!
  - Access to standard policies and claims
  - $1000 deductible information
  - 5-7 day claim processing

- **Platinum Tier**: sarah-platinum@example.com / Pass123!
  - Access to premium policies and claims
  - $500 deductible information
  - 24-48 hour priority processing

## Features

### 1. Authentication & Authorization
- OAuth 2.0 login with Cognito
- Custom scope-based tier identification
- JWT token management
- Automatic token refresh

### 2. Claims Dashboard
- Tier-specific claim listings
- Real-time statistics
- PostgreSQL RLS enforcement
- Responsive data tables

### 3. AI Chat Assistant
- Natural language queries
- Automatic agent routing
- Streaming responses
- Citation tracking
- Tier-aware responses

### 4. Supervisor Orchestration
- Query classification
- Agent selection logic
- Context propagation
- Error handling
- Response aggregation

## Environment Configuration

### Backend (.env)
```bash
# Database
DB_HOST=localhost
DB_NAME=insurance_claims
DB_USER=postgres
DB_PASSWORD=your_password

# AWS
AWS_REGION=us-east-1

# Cognito
COGNITO_USER_POOL_ID=your_pool_id
COGNITO_CLIENT_ID=your_client_id
COGNITO_DISCOVERY_URL=https://cognito-idp.region.amazonaws.com/pool_id

# Knowledge Base (from Tutorial 01)
KNOWLEDGE_BASE_ID=your_kb_id

# Agent ARNs (from Parameter Store)
RAG_AGENT_ARN=/agents/rag_metadata_arn
RLS_AGENT_ARN=/agents/rls_agent_arn
```

### Frontend (.env)
```bash
REACT_APP_API_URL=http://localhost:5000
REACT_APP_COGNITO_DOMAIN=your-domain.auth.region.amazoncognito.com
REACT_APP_COGNITO_CLIENT_ID=your_client_id
REACT_APP_REDIRECT_URI=http://localhost:3000/callback
```

## What You'll Learn

1. **Supervisor Agent Pattern**: How to build intelligent routing logic
2. **Multi-Agent Orchestration**: Coordinating specialized agents
3. **Full-Stack Integration**: Connecting React, Flask, and Strands
4. **Enterprise UI**: Building production-ready interfaces
5. **Token Propagation**: Maintaining authentication context
6. **Tier Context**: Propagating tier information across layers
7. **Error Handling**: Graceful degradation and user feedback
8. **Streaming Responses**: Real-time AI interactions

## Security Features

- **JWT Validation**: Automatic token verification by AgentCore
- **Scope-Based Authorization**: Tier extraction from Access Token
- **Row-Level Security**: PostgreSQL RLS for structured data
- **Metadata Filtering**: Vector DB filtering for unstructured data
- **Defense in Depth**: Multiple isolation layers
- **Secure Communication**: HTTPS in production
- **Session Management**: Secure token storage

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `POST /api/auth/logout` - User logout

### Claims
- `GET /api/claims` - List claims (tier-filtered)
- `GET /api/claims/:id` - Get claim details
- `GET /api/claims/stats` - Claim statistics

### Chat
- `POST /api/chat` - Send message to supervisor agent
- `GET /api/chat/stream` - Streaming chat responses

## Troubleshooting

### Backend Issues

**Backend won't start**
```bash
# Check PostgreSQL
psql -h localhost -U postgres -d insurance_claims

# Verify environment variables
cat backend/.env

# Check Python dependencies
pip install -r backend/requirements.txt
```

**Agent invocation fails**
```bash
# Verify agent ARNs in Parameter Store
aws ssm get-parameter --name /agents/rag_metadata_arn
aws ssm get-parameter --name /agents/rls_agent_arn

# Check IAM permissions
aws sts get-caller-identity
```

### Frontend Issues

**Frontend won't start**
```bash
# Install dependencies
cd frontend
npm install

# Check Node version (should be 16+)
node --version

# Verify backend is running
curl http://localhost:5000/health
```

**Authentication fails**
```bash
# Verify Cognito configuration
aws cognito-idp describe-user-pool --user-pool-id your_pool_id

# Check redirect URIs
# Must include http://localhost:3000/callback
```

### Database Issues

**RLS not working**
```sql
-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Verify policies
SELECT * FROM pg_policies WHERE tablename = 'claims';

-- Test RLS
SET app.current_tier = 'regular';
SELECT * FROM claims;
```

## Cleanup

### From Notebook
```python
# Stop processes
backend_process.terminate()
frontend_process.terminate()

# Delete supervisor agent
supervisor_runtime.delete()
```

### From Command Line
```bash
# Kill processes
pkill -f "python backend/app.py"
pkill -f "npm start"

# Or use the stop script
./stop.sh
```

## Production Deployment

For production deployment, consider:

1. **Infrastructure**
   - Use AWS ECS/EKS for containerized deployment
   - CloudFront for frontend distribution
   - ALB for backend load balancing
   - RDS for PostgreSQL with Multi-AZ

2. **Security**
   - Enable HTTPS with ACM certificates
   - Use AWS Secrets Manager for credentials
   - Enable CloudTrail for audit logging
   - Implement rate limiting

3. **Monitoring**
   - CloudWatch for logs and metrics
   - X-Ray for distributed tracing
   - Custom dashboards for business metrics

4. **Scaling**
   - Auto-scaling for backend services
   - Read replicas for database
   - CloudFront caching for static assets
   - AgentCore auto-scaling

## Next Steps

After completing this tutorial:
- Customize the UI for your use case
- Add more specialized agents
- Implement advanced routing logic
- Add monitoring and observability
- Deploy to production environment
- Integrate with existing systems

## Support

For issues or questions:
- Check the troubleshooting section
- Review Tutorial 01 and 02 documentation
- Consult AWS Bedrock AgentCore documentation
- Review Strands Agents documentation
