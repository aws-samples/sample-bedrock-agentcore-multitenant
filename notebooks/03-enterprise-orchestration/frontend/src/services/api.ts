import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export interface LoginResponse {
  success: boolean;
  email: string;
  tenant_id: string;
  tenant_name: string;
  access_token: string;
  id_token: string;
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

export const api = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const response = await axios.post(`${API_BASE_URL}/api/login`, {
      email,
      password
    });
    return response.data;
  },

  getClaims: async (accessToken: string): Promise<ClaimsResponse> => {
    const response = await axios.get(`${API_BASE_URL}/api/claims`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    return response.data;
  },

  query: async (accessToken: string, query: string): Promise<QueryResponse> => {
    const response = await axios.post(
      `${API_BASE_URL}/api/query`,
      { query },
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    return response.data;
  },

  chat: async (accessToken: string, messages: any[]): Promise<any> => {
    const response = await axios.post(
      `${API_BASE_URL}/api/chat`,
      { messages },
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    return response.data;
  }
};
