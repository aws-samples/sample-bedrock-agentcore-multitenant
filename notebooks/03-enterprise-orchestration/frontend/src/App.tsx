import React, { useState } from 'react';
import TopNavigation from '@cloudscape-design/components/top-navigation';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Alert from '@cloudscape-design/components/alert';

import { LoginScreen } from './components/LoginScreen';
import { ChatInterface } from './components/ChatInterface';

import { api, LoginResponse } from './services/api';
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendMessage = async (directQuery?: string) => {
    const queryText = directQuery || prompt;
    if (!queryText.trim() || loading || !user) return;

    const userMessage: Message = {
      type: 'outgoing',
      content: queryText,
      timestamp: getCurrentTimestamp()
    };

    setMessages(prev => [...prev, userMessage]);
    setPrompt('');
    setLoading(true);
    setError(null);

    try {
      const response = await api.query(user.access_token, queryText, user.tenant_id, user.agent_type, user.session_id);

      const aiMessage: Message = {
        type: 'incoming',
        content: response.response,
        timestamp: getCurrentTimestamp(),
        queryType: response.query_type,
        metadata: response.metadata
      };

      setMessages(prev => [...prev, aiMessage]);
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
  };

  const handleDemoLogin = async (demoUser: any) => {
    setError(null);
    setLoading(true);
    
    try {
      // Call backend to get real Cognito tokens
      const response = await api.demoLogin(demoUser.username, demoUser.agent_type);
      
      if (response.success) {
        setUser(response);
        const agentDesc = response.agent_type === 'rag' 
          ? 'policy documents (RAG with metadata filtering)'
          : 'insurance claims (RLS with Row-Level Security)';
        setMessages([{
          type: 'incoming',
          content: `Welcome ${response.user_info.given_name}! You are logged in as **${response.tenant_name}**. I can help you query your ${agentDesc}.`,
          timestamp: getCurrentTimestamp()
        }]);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  // Login Screen
  if (!user) {
    return (
      <LoginScreen
        loading={loading}
        error={error}
        onDismissError={() => setError(null)}
        onDemoLogin={handleDemoLogin}
      />
    );
  }

  const userInitials = getInitials(
    user.user_info.given_name,
    user.user_info.family_name
  );

  // Main Application
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopNavigation
        identity={{
          href: '#',
          title: `Insurance Claims Portal - ${user.agent_type === 'rag' ? 'Policy Agent' : 'Claims Agent'}`
        }}
        utilities={[
          {
            type: 'button',
            text: `${user.user_info.given_name} (${user.tenant_name})`,
            iconName: 'user-profile'
          },
          {
            type: 'button',
            text: 'Switch User',
            onClick: handleLogout,
            iconName: 'redo'
          }
        ]}
      />

      <div style={{ flex: 1, padding: '20px', background: '#f1f3f5' }}>
        <SpaceBetween size="m">
          {error && (
            <Alert type="error" dismissible onDismiss={() => setError(null)}>
              {error}
            </Alert>
          )}

          <ChatInterface
            messages={messages}
            prompt={prompt}
            loading={loading}
            userInitials={userInitials}
            userEmail={user.email}
            tenantId={user.tenant_id}
            agentType={user.agent_type}
            onPromptChange={setPrompt}
            onSendMessage={handleSendMessage}
          />
        </SpaceBetween>
      </div>
    </div>
  );
}

export default App;
