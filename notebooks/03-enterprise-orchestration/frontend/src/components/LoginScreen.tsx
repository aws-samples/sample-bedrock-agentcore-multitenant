import React from 'react';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import Input from '@cloudscape-design/components/input';
import Box from '@cloudscape-design/components/box';
import Alert from '@cloudscape-design/components/alert';

interface LoginScreenProps {
  email: string;
  password: string;
  loading: boolean;
  error: string | null;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onLogin: () => void;
  onDismissError: () => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({
  email,
  password,
  loading,
  error,
  onEmailChange,
  onPasswordChange,
  onLogin,
  onDismissError
}) => {
  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      background: '#f9f9f9' 
    }}>
      <Container
        header={
          <Header 
            variant="h1" 
            description="Secure multi-tenant insurance claims platform"
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
            Login with your broker credentials to access your insurance claims data.
            Each broker can only see their own tenant's data, enforced by Row-Level Security and metadata filtering.
          </Box>

          <Input
            value={email}
            onChange={({ detail }) => onEmailChange(detail.value)}
            placeholder="Email (e.g., broker-a@example.com)"
            type="email"
            disabled={loading}
          />

          <Input
            value={password}
            onChange={({ detail }) => onPasswordChange(detail.value)}
            placeholder="Password"
            type="password"
            disabled={loading}
            onKeyDown={(e) => {
              if (e.detail.key === 'Enter') {
                onLogin();
              }
            }}
          />

          <Button
            variant="primary"
            onClick={onLogin}
            loading={loading}
            fullWidth
          >
            Login
          </Button>

          <Box variant="small" color="text-body-secondary">
            <strong>Demo Accounts:</strong><br />
            • broker-a@example.com / Pass123! (Broker A - 5 claims)<br />
            • broker-b@example.com / Pass123! (Broker B - 2 claims)<br /><br />
            <strong>Security Features:</strong><br />
            ✓ JWT authentication via AWS Cognito<br />
            ✓ Row-Level Security for structured data<br />
            ✓ Metadata filtering for unstructured data<br />
            ✓ Defense-in-depth tenant isolation
          </Box>
        </SpaceBetween>
      </Container>
    </div>
  );
};
