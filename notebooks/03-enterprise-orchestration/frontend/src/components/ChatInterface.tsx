import React, { useRef, useEffect } from 'react';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import ChatBubble from '@cloudscape-design/chat-components/chat-bubble';
import Avatar from '@cloudscape-design/chat-components/avatar';
import PromptInput from '@cloudscape-design/components/prompt-input';

interface Message {
  type: 'incoming' | 'outgoing';
  content: string;
  timestamp: string;
  queryType?: string;
  metadata?: any;
  isError?: boolean;
}

interface ChatInterfaceProps {
  messages: Message[];
  prompt: string;
  loading: boolean;
  userInitials: string;
  userEmail: string;
  tenantId: string;
  onPromptChange: (value: string) => void;
  onSendMessage: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  prompt,
  loading,
  userInitials,
  userEmail,
  tenantId,
  onPromptChange,
  onSendMessage
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
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
                      initials={userInitials}
                      ariaLabel={userEmail}
                    />
                  )
                }
                ariaLabel={`${msg.type === 'incoming' ? 'AI' : userEmail} at ${msg.timestamp}`}
              >
                <Box color={msg.isError ? 'text-status-error' : undefined}>
                  {msg.content}
                </Box>
                {msg.queryType && (
                  <Box variant="small" color="text-body-secondary" margin={{ top: 'xs' }}>
                    Query type: {msg.queryType} | Tenant: {tenantId}
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
          onChange={({ detail }) => onPromptChange(detail.value)}
          onAction={onSendMessage}
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
  );
};
