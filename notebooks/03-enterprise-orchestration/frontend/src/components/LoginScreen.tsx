import React from 'react';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import Box from '@cloudscape-design/components/box';
import Alert from '@cloudscape-design/components/alert';
import Cards from '@cloudscape-design/components/cards';
import Badge from '@cloudscape-design/components/badge';

interface DemoUser {
  username: string;
  email: string;
  tenant_id: string;
  tenant_name: string;
  given_name: string;
  agent_type: 'rls' | 'rag';
  cognito_pool: string;
}

interface LoginScreenProps {
  loading: boolean;
  error: string | null;
  onDismissError: () => void;
  onDemoLogin?: (user: DemoUser) => void;
}

const RLS_USERS: DemoUser[] = [
  {
    username: 'mike-broker-a',
    email: 'mike.broker@example.com',
    tenant_id: 'broker-a',
    tenant_name: 'Broker A',
    given_name: 'Mike',
    agent_type: 'rls',
    cognito_pool: 'structured-rls-pool'
  },
  {
    username: 'emma-broker-b',
    email: 'emma.broker@example.com',
    tenant_id: 'broker-b',
    tenant_name: 'Broker B',
    given_name: 'Emma',
    agent_type: 'rls',
    cognito_pool: 'structured-rls-pool'
  }
];

const RAG_USERS: DemoUser[] = [
  {
    username: 'john-regular',
    email: 'john.regular@example.com',
    tenant_id: 'regular',
    tenant_name: 'Regular Tier',
    given_name: 'John',
    agent_type: 'rag',
    cognito_pool: 'unstructured-rag-pool'
  },
  {
    username: 'sarah-platinum',
    email: 'sarah.platinum@example.com',
    tenant_id: 'platinum',
    tenant_name: 'Platinum Tier',
    given_name: 'Sarah',
    agent_type: 'rag',
    cognito_pool: 'unstructured-rag-pool'
  }
];

interface AgentCard {
  id: string;
  title: string;
  description: string;
  badge: string;
  users: DemoUser[];
}

const AGENT_CARDS: AgentCard[] = [
  {
    id: 'rag',
    title: 'Policy Agent',
    description: 'Search and query your insurance policy documents. Uses Knowledge Base with metadata filtering for tenant isolation.',
    badge: 'RAG',
    users: RAG_USERS
  },
  {
    id: 'rls',
    title: 'Claims Agent',
    description: 'View and analyze your insurance claims data. Uses PostgreSQL with Row-Level Security for tenant isolation.',
    badge: 'RLS',
    users: RLS_USERS
  }
];

export const LoginScreen: React.FC<LoginScreenProps> = ({
  loading,
  error,
  onDismissError,
  onDemoLogin
}) => {
  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      background: '#f1f3f5',
      padding: '40px 20px'
    }}>
      <div style={{ maxWidth: '900px', width: '100%' }}>
        <SpaceBetween size="l">
          <Container
            header={
              <Header
                variant="h1"
                description="Multi-tenant demo showcasing AgentCore identity propagation"
              >
                Insurance Claims Portal
              </Header>
            }
          >
            <SpaceBetween size="l">
              {error && (
                <Alert type="error" dismissible onDismiss={onDismissError}>
                  {error}
                </Alert>
              )}

              <Box variant="p">
                Select an agent and user to explore multi-tenant data isolation. 
                Each user can only access data belonging to their tenant.
              </Box>

              <Cards
                cardDefinition={{
                  header: item => (
                    <SpaceBetween direction="horizontal" size="xs">
                      <span>{item.title}</span>
                      <Badge color="blue">{item.badge}</Badge>
                    </SpaceBetween>
                  ),
                  sections: [
                    {
                      id: 'description',
                      content: item => (
                        <Box variant="small" color="text-body-secondary">
                          {item.description}
                        </Box>
                      )
                    },
                    {
                      id: 'users',
                      header: 'Demo Users',
                      content: item => (
                        <SpaceBetween size="xs">
                          {item.users.map(user => (
                            <Button
                              key={user.username}
                              onClick={() => onDemoLogin?.(user)}
                              loading={loading}
                              fullWidth
                            >
                              {user.given_name} ({user.tenant_name})
                            </Button>
                          ))}
                        </SpaceBetween>
                      )
                    }
                  ]
                }}
                cardsPerRow={[{ cards: 2 }]}
                items={AGENT_CARDS}
                trackBy="id"
              />

              <Box variant="small" color="text-body-secondary" textAlign="center">
                JWT tokens from AWS Cognito are passed to AgentCore agents for identity-aware data access
              </Box>
            </SpaceBetween>
          </Container>
        </SpaceBetween>
      </div>
    </div>
  );
};
