# Multi-Tenant Insurance Claims Frontend

Cloudscape Design System UI for secure multi-tenant insurance claims platform.

## Features

- **Cloudscape Design System** - AWS's design system for enterprise applications
- **JWT Authentication** - Secure login via AWS Cognito
- **Multi-tenant Dashboard** - Claims data with Row-Level Security
- **AI Chat Assistant** - Natural language queries with tenant isolation
- **Real-time Statistics** - Claims analytics and summaries

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create `.env` file:

```bash
REACT_APP_API_URL=http://localhost:5000
```

### 3. Run Development Server

```bash
npm start
```

Open [http://localhost:3000](http://localhost:3000)

## Demo Accounts

### Broker A
- **Email**: broker-a@example.com
- **Password**: Pass123!
- **Claims**: 5 claims (CLM-A-001 to CLM-A-005)

### Broker B
- **Email**: broker-b@example.com
- **Password**: Pass123!
- **Claims**: 2 claims (CLM-B-001 to CLM-B-002)

## Features Demonstrated

### 1. Structured Data (Claims Table)
- **Row-Level Security (RLS)** enforced at PostgreSQL level
- Each broker sees only their tenant's claims
- Real-time statistics dashboard

### 2. AI Assistant (Chat)
- **Natural language queries** powered by Amazon Bedrock
- **Structured queries**: "How many claims were filed last week?"
- **Unstructured queries**: "What is the maximum deductible?" (requires Knowledge Base)
- **Tenant isolation** maintained throughout query processing

## Architecture

```
┌─────────────────────────────────────┐
│   Cloudscape UI (React)             │
│   - Login with Cognito              │
│   - Claims Dashboard                │
│   - AI Chat Interface               │
└──────────────┬──────────────────────┘
               │ JWT Token
               ↓
┌─────────────────────────────────────┐
│   Backend API (Flask)               │
│   - Token validation                │
│   - Tenant context extraction       │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ↓                ↓
┌─────────────┐  ┌─────────────────┐
│ PostgreSQL  │  │ Bedrock KB      │
│ + RLS       │  │ + Metadata      │
│ (Structured)│  │ (Unstructured)  │
└─────────────┘  └─────────────────┘
```

## Security

- **JWT tokens** from AWS Cognito with custom tenant_id claim
- **Row-Level Security** at database layer
- **Metadata filtering** for RAG queries
- **Defense in depth** with multiple isolation layers

## Build for Production

```bash
npm run build
```

Builds the app for production to the `build` folder.

## Components Used

- **@cloudscape-design/components** - Core UI components
- **@cloudscape-design/chat-components** - Chat interface
- **@cloudscape-design/global-styles** - Global styles
- **axios** - HTTP client for API calls
