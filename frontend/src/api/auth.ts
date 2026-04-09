import type { User, TokenResponse } from '../types';
import { apiClient } from './client';

export async function register(data: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}): Promise<User> {
  const response = await apiClient.post<User>('/api/v1/auth/register', data);
  return response.data;
}

export async function login(data: { email: string; password: string }): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', data);
  return response.data;
}

export async function refreshToken(refreshToken: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/api/v1/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data;
}

export async function getMe(): Promise<User> {
  const response = await apiClient.get<User>('/api/v1/auth/me');
  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/api/v1/auth/logout');
}
