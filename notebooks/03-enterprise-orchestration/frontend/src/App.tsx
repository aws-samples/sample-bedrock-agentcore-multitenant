import React, { useState, useEffect } from 'react';
import AppLayout from '@cloudscape-design/components/app-layout';
import TopNavigation from '@cloudscape-design/components/top-navigation';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Alert from '@cloudscape-design/components/alert';
import Tabs from '@cloudscape-design/components/tabs';

import { LoginScreen } from './components/LoginScreen';
import { StatisticsDashboard } from './components/StatisticsDashboard';
import { ClaimsTable } from './components/ClaimsTable';
import { ChatInterface } from './components/ChatInterface';

import { api, LoginResponse, ClaimsResponse } from './services/api';
import { getInitials, getCurrentTimestamp } from './utils/formatters';

interface Message {
  type: 'incoming' | 'outgoing';
  content: string;
  timestamp: string;
  queryType?: string;
  metadata?: any;
  isError?: boolean;
}

function App() {
  const [user, setUser] = useState<LoginResponse | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [claims, setClaims] = useState<any[]>([]);
  const [statistics, setStatistics] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('claims');

  useEffect(() => {
    if (user) {
      loadClaims();
    }
  }, [user]);

  const handleLogin = async () => {
    setError(null);
    setLoading(true);
    
    try {
      const response = await api.login(email, password);
      
      if (response.success) {
        setUser(response);
        setMessages([{
          type: 'incoming',
          content: `Welcome ${response.user_info.given_name}! You are logged in as ${response.tenant_name}. I can help you with your insurance claims and policies.`,
          timestamp: getCurrentTimestamp()
        }]);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const loadClaims = async () => {
    if (!user) return;
    
    try {
      const response = await api.getClaims(user.access_token);
      
      if (response.success) {
        setClaims(response.claims);
        setStatistics(response.statistics);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load claims');
    }
  };

  const handleSendMessage = async () => {
    if (!prompt.trim() || loading || !user) return;

    const userMessage: Message = {
      type: 'outgoing',
      content: prompt,
      timestamp: getCurrentTimestamp()
    };

    setMessages(prev => [...prev, userMessage]);
    setPrompt('');
    setLoading(true);
    setError(null);

    try {
      const response = await api.query(user.access_token, prompt);

      const aiMessage: Message = {
        type: 'incoming',
        content: response.response,
        timestamp: getCurrentTimestamp(),
        queryType: response.query_type,
        metadata: response.metadata
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // Refresh claims if it was a structured query
      if (response.query_type === 'structured') {
        loadClaims();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Query failed');
      
      const errorMessage: Message = {
        type: 'incoming',
        content: `Error: ${err.response?.data?.error || 'Failed to process query'}`,
        timestamp: getCurrentTimestamp(),
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
      <LoginScreen
        email={email}
        password={password}
        loading={loading}
        error={error}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onLogin={handleLogin}
        onDismissError={() => setError(null)}
      />
    );
  }

  const userInitials = getInitials(
    user.user_info.given_name,
    user.user_info.family_name
  );

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

            {statistics && <StatisticsDashboard statistics={statistics} />}

            <Tabs
              activeTabId={activeTab}
              onChange={({ detail }) => setActiveTab(detail.activeTabId)}
              tabs={[
                {
                  id: 'claims',
                  label: 'Claims Data',
                  content: <ClaimsTable claims={claims} />
                },
                {
                  id: 'chat',
                  label: 'AI Assistant',
                  content: (
                    <ChatInterface
                      messages={messages}
                      prompt={prompt}
                      loading={loading}
                      userInitials={userInitials}
                      userEmail={user.email}
                      tenantId={user.tenant_id}
                      onPromptChange={setPrompt}
                      onSendMessage={handleSendMessage}
                    />
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
