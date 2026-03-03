import api from './api';

export interface User {
  id: number;
  nickname: string;
  avatar: string;
  email: string;
  bio: string;
  is_active: boolean;
  email_verified: boolean;
  last_login_at: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authService = {
  sendCode: (email: string) => {
    return api.post<{ message: string }>('/auth/send-code', { email });
  },

  register: (data: { email: string; code: string; password: string; nickname?: string }) => {
    return api.post<AuthResponse>('/auth/register', data);
  },

  login: (data: { email: string; password: string }) => {
    return api.post<AuthResponse>('/auth/login', data);
  },

  resetPassword: (data: { email: string; code: string; new_password: string }) => {
    return api.post<{ message: string }>('/auth/reset-password', data);
  },
};
