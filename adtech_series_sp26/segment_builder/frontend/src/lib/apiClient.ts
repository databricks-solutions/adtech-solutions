/**
 * API client for backend communication.
 */

import axios from 'axios';
import toast from 'react-hot-toast';

export const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor: log errors and show user-facing toast
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      (Array.isArray(error.response?.data?.detail)
        ? error.response.data.detail.map((e: { msg?: string }) => e?.msg).join(' ')
        : error.response?.data?.detail) ??
      error.message ??
      'An error occurred';
    console.error('API Error:', message);
    toast.error(message, { duration: 5000 });
    return Promise.reject(error);
  }
);

export default apiClient;
