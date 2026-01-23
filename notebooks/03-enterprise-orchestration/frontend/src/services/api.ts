import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Generate unique session ID for conversation history
const generateSessionId = () => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

export interface LoginResponse {
  success: boolean;
  email: string;
  tenant_id: string;
  tenant_name: string;
  agent_type?: string;
  access_token: string;
  id_token: string;
  session_id: string;
  user_info: {
    given_name: string;
    family_name: string;
    email: string;
  };
}

export interface ClaimsResponse {
  success: boolean;
  tenant_id: string;
  claims: any[];
  response?: string;
  statistics: {
    total_claims: number;
    total_amount: number;
    approved_count: number;
    recent_claims: number;
  };
}

export interface QueryResponse {
  success: boolean;
  response: string;
  query_type: string;
  tenant_id: string;
  metadata: any;
}

// Helper to get headers with tenant support
const getHeaders = (accessToken: string, tenantId?: string, agentType?: string, sessionId?: string) => {
  const headers: Record<string, string> = {
    'Authorization': `Bearer ${accessToken}`
  };
  
  if (tenantId) {
    headers['X-Tenant-Id'] = tenantId;
  }
  if (agentType) {
    headers['X-Agent-Type'] = agentType;
  }
  if (sessionId) {
    headers['X-Session-Id'] = sessionId;
  }
  
  return headers;
};

export const api = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await axios.post(`${API_BASE_URL}/api/login`, {
      username,
      password
    });
    return response.data;
  },

  demoLogin: async (username: string, agentType: string): Promise<LoginResponse> => {
    const response = await axios.post(`${API_BASE_URL}/api/demo-login`, {
      username,
      agent_type: agentType
    });
    // Add session_id for conversation history
    return {
      ...response.data,
      session_id: generateSessionId()
    };
  },

  getClaims: async (accessToken: string, tenantId?: string, agentType?: string): Promise<ClaimsResponse> => {
    const response = await axios.get(`${API_BASE_URL}/api/claims`, {
      headers: getHeaders(accessToken, tenantId, agentType)
    });
    return response.data;
  },

  query: async (accessToken: string, query: string, tenantId?: string, agentType?: string, sessionId?: string): Promise<QueryResponse> => {
    const response = await axios.post(
      `${API_BASE_URL}/api/query`,
      { query },
      {
        headers: getHeaders(accessToken, tenantId, agentType, sessionId)
      }
    );
    return response.data;
  },

  chat: async (accessToken: string, messages: any[], tenantId?: string, agentType?: string): Promise<any> => {
    const response = await axios.post(
      `${API_BASE_URL}/api/chat`,
      { messages },
      {
        headers: getHeaders(accessToken, tenantId, agentType)
      }
    );
    return response.data;
  }
};
