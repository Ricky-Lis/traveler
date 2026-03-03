import axios from 'axios';

// Create an axios instance with a base URL
// In development, this will be proxied by Vite to http://localhost:8000
// In production, this should point to the real API
const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 不需要、也不应携带 Authorization 的路径（与后端接口文档一致）
const NO_AUTH_PATHS = [
  '/auth/login',
  '/auth/register',
  '/auth/send-code',
  '/auth/reset-password',
];

function isNoAuthPath(url: string): boolean {
  return NO_AUTH_PATHS.some((p) => url.includes(p));
}

// Add a request interceptor to include the auth token if available
api.interceptors.request.use(
  (config) => {
    if (isNoAuthPath(config.url || '')) {
      return config;
    }
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
