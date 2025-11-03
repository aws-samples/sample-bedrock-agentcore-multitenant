# Multi-Tenant RAG Backend API

REST API for multi-tenant insurance claims platform with Cloudscape UI.

## Features

- **JWT Authentication** via AWS Cognito
- **Row-Level Security (RLS)** for structured data
- **Metadata Filtering** for unstructured data (RAG)
- **Multi-tenant isolation** at database and knowledge base layers

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

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
COGNITO_CLIENT_SECRET=your_client_secret

# Bedrock Knowledge Base (optional)
KNOWLEDGE_BASE_ID=your_kb_id
```

### 3. Run Server

```bash
# Development
python app.py

# Production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### Authentication

**POST /api/login**
```json
{
  "username": "broker-a",
  "password": "Pass123!"
}
```

Response:
```json
{
  "success": true,
  "username": "broker-a",
  "tenant_id": "broker-a",
  "access_token": "...",
  "id_token": "..."
}
```

### Query

**POST /api/query**

Headers:
```
Authorization: Bearer <access_token>
```

Body:
```json
{
  "query": "How many claims were filed last week?",
  "type": "auto"  // auto, structured, or unstructured
}
```

Response:
```json
{
  "success": true,
  "response": "You have 5 claims filed in the last week...",
  "query_type": "structured",
  "metadata": {
    "tenant_id": "broker-a",
    "claims_count": 5
  }
}
```

### Chat

**POST /api/chat**

Headers:
```
Authorization: Bearer <access_token>
```

Body:
```json
{
  "messages": [
    {"role": "user", "content": "What is the deductible for auto insurance?"}
  ]
}
```

## Architecture

```
Frontend (Cloudscape UI)
    ↓
Backend API (Flask)
    ↓
┌─────────────────┬──────────────────┐
│   Structured    │   Unstructured   │
│   PostgreSQL    │   Bedrock KB     │
│   + RLS         │   + Metadata     │
└─────────────────┴──────────────────┘
```

## Security

- **JWT tokens** validated via AWS Cognito
- **Row-Level Security** enforces tenant isolation at database layer
- **Metadata filtering** ensures tenant isolation for RAG queries
- **Defense in depth** with multiple isolation layers

## Development

```bash
# Run with debug mode
FLASK_DEBUG=1 python app.py

# Test endpoints
curl http://localhost:5000/health
```
