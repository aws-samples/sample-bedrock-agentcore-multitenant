import React, { useState, useEffect, useRef } from 'react';
import AppLayout from '@cloudscape-design/components/app-layout';
import TopNavigation from '@cloudscape-design/components/top-navigation';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import Input from '@cloudscape-design/components/input';
import Box from '@cloudscape-design/components/box';
import Alert from '@cloudscape-design/components/alert';
import Table from '@cloudscape-design/components/table';
import Badge from '@cloudscape-design/components/badge';
import ChatBubble from '@cloudscape-design/chat-components/chat-bubble';
import Avatar from '@cloudscape-design/chat-components/avatar';
import PromptInput from '@cloudscape-design/components/prompt-input';
import Tabs from '@cloudscape-design/components/tabs';
import ColumnLayout from '@cloudscape-design/components/column-layout';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [user, setUser] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [claims, setClaims] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('claims');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (user) {
      loadClaims();
    }
  }, [user]);

  const handleLogin = async () => {
    setError(null);
    setLoading(true);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/login`, {
        email,
        password
      });
      
      if (response.data.success) {
        setUser(response.data);
        setMessages([{
          type: 'incoming',
          content: `Welcome ${response.data.user_info.given_name}! You are logged in as ${response.data.tenant_name}. I can help you with your insurance claims and policies.`,
          timestamp: new Date().toLocaleTimeString()
        }]);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const loadClaims = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/claims`, {
        headers: {
          'Authorization': `Bearer ${user.access_token}`
        }
      });
      
      if (response.data.success) {
        setClaims(response.data.claims);
        setStatistics(response.data.statistics);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load claims');
    }
  };

  const handleSendMessage = async () => {
    if (!prompt.trim() || loading) return;

    const userMessage = {
      type: 'outgoing',
      content: prompt,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setPrompt('');
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/query`,
        { query: prompt },
        {
          headers: {
            'Authorization': `Bearer ${user.access_token}`
          }
        }
      );

      const aiMessage = {
        type: 'incoming',
        content: response.data.response,
        timestamp: new Date().toLocaleTimeString(),
        queryType: response.data.query_type,
        metadata: response.data.metadata
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // Refresh claims if it was a structured query
      if (response.data.query_type === 'structured') {
        loadClaims();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Query failed');
      
      const errorMessage = {
        type: 'incoming',
        content: `Error: ${err.response?.data?.error || 'Failed to process query'}`,
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setUser(null);
    setMessages([]);
    setClaims([]);
    setStatistics(null);
    setEmail('');
    setPassword('');
    setActiveTab('claims');
  };

  // Login Screen
  if (!user) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f9f9f9' }}>
        <Container
          header={
            <Header variant="h1" description="Secure multi-tenant insurance claims platform">
              Insurance Claims Portal
            </Header>
          }
        >
          <SpaceBetween size="l">
            {error && (
              <Alert type="error" dismissible onDismiss={() => setError(null)}>
                {error}
              </Alert>
            )}
            
            <Box variant="p">
              Login with your broker credentials to access your insurance claims data.
              Each broker can only see their own tenant's data, enforced by Row-Level Security and metadata filtering.
            </Box>

            <Input
              value={email}
              onChange={({ detail }) => setEmail(detail.value)}
              placeholder="Email (e.g., broker-a@example.com)"
              type="email"
              disabled={loading}
            />

            <Input
              value={password}
              onChange={({ detail }) => setPassword(detail.value)}
              placeholder="Password"
              type="password"
              disabled={loading}
              onKeyDown={(e) => {
                if (e.detail.key === 'Enter') {
                  handleLogin();
                }
              }}
            />

            <Button
              variant="primary"
              onClick={handleLogin}
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
  }

  // Main Application
  return (
    <>
      <TopNavigation
        identity={{
          href: '#',
          title: 'Insurance Claims Portal',
          logo: {
            src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHJ4PSI0IiBmaWxsPSIjMjMyRjNFIi8+PHBhdGggZD0iTTE2IDhMMjQgMTZMMTYgMjRMOCAxNkwxNiA4WiIgZmlsbD0iIzAwN0RCQyIvPjwvc3ZnPg==',
            alt: 'Logo'
          }
        }}
        utilities={[
          {
            type: 'button',
            text: user.tenant_name,
            description: user.email,
            iconName: 'user-profile'
          },
          {
            type: 'button',
            text: 'Logout',
            onClick: handleLogout,
            iconName: 'close'
          }
        ]}
      />

      <AppLayout
        navigationHide
        toolsHide
        content={
          <SpaceBetween size="l">
            {error && (
              <Alert type="error" dismissible onDismiss={() => setError(null)}>
                {error}
              </Alert>
            )}

            {/* Statistics Dashboard */}
            {statistics && (
              <Container>
                <ColumnLayout columns={4} variant="text-grid">
                  <div>
                    <Box variant="awsui-key-label">Total Claims</Box>
                    <Box variant="awsui-value-large">{statistics.total_claims}</Box>
                  </div>
                  <div>
                    <Box variant="awsui-key-label">Total Amount</Box>
                    <Box variant="awsui-value-large">${statistics.total_amount?.toFixed(2) || '0.00'}</Box>
                  </div>
                  <div>
                    <Box variant="awsui-key-label">Approved</Box>
                    <Box variant="awsui-value-large">{statistics.approved_count}</Box>
                  </div>
                  <div>
                    <Box variant="awsui-key-label">Last 7 Days</Box>
                    <Box variant="awsui-value-large">{statistics.recent_claims}</Box>
                  </div>
                </ColumnLayout>
              </Container>
            )}

            {/* Tabs */}
            <Tabs
              activeTabId={activeTab}
              onChange={({ detail }) => setActiveTab(detail.activeTabId)}
              tabs={[
                {
                  id: 'claims',
                  label: 'Claims Data',
                  content: (
                    <Container
                      header={
                        <Header
                          variant="h2"
                          description="Structured data with Row-Level Security (RLS)"
                        >
                          Your Insurance Claims
                        </Header>
                      }
                    >
                      <Table
                        columnDefinitions={[
                          {
                            id: 'claim_number',
                            header: 'Claim Number',
                            cell: item => item.claim_number
                          },
                          {
                            id: 'customer_name',
                            header: 'Customer',
                            cell: item => item.customer_name
                          },
                          {
                            id: 'claim_amount',
                            header: 'Amount',
                            cell: item => `$${item.claim_amount}`
                          },
                          {
                            id: 'claim_date',
                            header: 'Date',
                            cell: item => new Date(item.claim_date).toLocaleDateString()
                          },
                          {
                            id: 'status',
                            header: 'Status',
                            cell: item => (
                              <Badge
                                color={
                                  item.status === 'approved' ? 'green' :
                                  item.status === 'pending' ? 'blue' : 'red'
                                }
                              >
                                {item.status}
                              </Badge>
                            )
                          }
                        ]}
                        items={claims}
                        loadingText="Loading claims"
                        empty={
                          <Box textAlign="center" color="inherit">
                            <b>No claims</b>
                            <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                              No claims to display.
                            </Box>
                          </Box>
                        }
                      />
                    </Container>
                  )
                },
                {
                  id: 'chat',
                  label: 'AI Assistant',
                  content: (
                    <Container
                      header={
                        <Header
                          variant="h2"
                          description="Ask questions about your claims and policies"
                        >
                          AI-Powered Query Assistant
                        </Header>
                      }
                    >
                      <SpaceBetween size="l">
                        <div style={{ 
                          minHeight: '400px', 
                          maxHeight: '600px', 
                          overflowY: 'auto',
                          padding: '16px',
                          background: '#fafafa',
                          borderRadius: '8px'
                        }}>
                          <SpaceBetween size="m">
                            {messages.map((msg, idx) => (
                              <ChatBubble
                                key={idx}
                                type={msg.type}
                                avatar={
                                  msg.type === 'incoming' ? (
                                    <Avatar
                                      color="gen-ai"
                                      iconName="gen-ai"
                                      ariaLabel="AI Assistant"
                                    />
                                  ) : (
                                    <Avatar
                                      initials={user.user_info.given_name.substring(0, 1) + user.user_info.family_name.substring(0, 1)}
                                      ariaLabel={user.email}
                                    />
                                  )
                                }
                                ariaLabel={`${msg.type === 'incoming' ? 'AI' : user.email} at ${msg.timestamp}`}
                              >
                                <Box color={msg.isError ? 'text-status-error' : undefined}>
                                  {msg.content}
                                </Box>
                                {msg.queryType && (
                                  <Box variant="small" color="text-body-secondary" margin={{ top: 'xs' }}>
                                    Query type: {msg.queryType} | Tenant: {user.tenant_id}
                                  </Box>
                                )}
                              </ChatBubble>
                            ))}
                            {loading && (
                              <ChatBubble
                                type="incoming"
                                avatar={
                                  <Avatar
                                    color="gen-ai"
                                    iconName="gen-ai"
                                    ariaLabel="AI Assistant"
                                    loading
                                  />
                                }
                              >
                                <Box color="text-status-inactive">Processing your query...</Box>
                              </ChatBubble>
                            )}
                            <div ref={messagesEndRef} />
                          </SpaceBetween>
                        </div>

                        <PromptInput
                          value={prompt}
                          onChange={({ detail }) => setPrompt(detail.value)}
                          onAction={handleSendMessage}
                          placeholder="Ask about your claims or policies..."
                          actionButtonAriaLabel="Send message"
                          actionButtonIconName="send"
                          disabled={loading}
                        />

                        <Box variant="small" color="text-body-secondary">
                          <strong>Try asking:</strong><br />
                          • "How many claims were filed last week?"<br />
                          • "What is the total claim amount?"<br />
                          • "What is the maximum deductible for auto insurance?" (requires Knowledge Base)
                        </Box>
                      </SpaceBetween>
                    </Container>
                  )
                }
              ]}
            />
          </SpaceBetween>
        }
      />
    </>
  );
}

export default App;
