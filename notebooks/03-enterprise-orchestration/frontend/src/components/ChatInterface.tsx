import React, { useRef, useEffect } from 'react';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import ChatBubble from '@cloudscape-design/chat-components/chat-bubble';
import Avatar from '@cloudscape-design/chat-components/avatar';
import PromptInput from '@cloudscape-design/components/prompt-input';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
  agentType?: string;
  onPromptChange: (value: string) => void;
  onSendMessage: (query?: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  prompt,
  loading,
  userInitials,
  userEmail,
  tenantId,
  agentType,
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
                  <div className="markdown-content" style={{ 
                    lineHeight: '1.4',
                  }}>
                    <style>{`
                      .markdown-content p { margin: 0 0 0.5em 0; }
                      .markdown-content p:last-child { margin-bottom: 0; }
                      .markdown-content ul, .markdown-content ol { margin: 0.3em 0; padding-left: 1.5em; }
                      .markdown-content li { margin: 0.2em 0; }
                      .markdown-content table { border-collapse: collapse; margin: 0.5em 0; font-size: 0.9em; }
                      .markdown-content th, .markdown-content td { border: 1px solid #ddd; padding: 4px 8px; }
                      .markdown-content th { background: #f5f5f5; }
                      .markdown-content h1, .markdown-content h2, .markdown-content h3 { margin: 0.5em 0 0.3em 0; }
                    `}</style>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>
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
                ariaLabel="AI is processing"
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
          onAction={() => onSendMessage()}
          placeholder="Ask about your claims or policies..."
          actionButtonAriaLabel="Send message"
          actionButtonIconName="send"
          disabled={loading}
        />

        <Box variant="small" color="text-body-secondary">
          <strong>Try asking:</strong>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
            {(agentType === 'rag' ? [
              "What is the deductible for auto insurance?",
              "What is the claims processing time?",
              "Is roadside assistance included?"
            ] : [
              "Show me all my claims",
              "What is the total claim amount?",
              "How many claims are approved?"
            ]).map((suggestion, idx) => (
              <span
                key={idx}
                onClick={() => !loading && onSendMessage(suggestion)}
                style={{
                  padding: '4px 12px',
                  background: '#f0f3f5',
                  borderRadius: '16px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '13px',
                  border: '1px solid #d5dbdb',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (!loading) {
                    e.currentTarget.style.background = '#e9ebed';
                    e.currentTarget.style.borderColor = '#879596';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = '#f0f3f5';
                  e.currentTarget.style.borderColor = '#d5dbdb';
                }}
              >
                {suggestion}
              </span>
            ))}
          </div>
        </Box>
      </SpaceBetween>
    </Container>
  );
};
