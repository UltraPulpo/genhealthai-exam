import { describe, it, expect, vi, beforeEach } from 'vitest';
import { register, login, refreshToken, getMe, logout } from '../auth';
import { apiClient } from '../client';

vi.mock('../client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
  setAccessToken: vi.fn(),
}));

/* eslint-disable @typescript-eslint/unbound-method */
const mockPost = vi.mocked(apiClient.post);
const mockGet = vi.mocked(apiClient.get);
/* eslint-enable @typescript-eslint/unbound-method */

describe('auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('register', () => {
    it('calls POST /api/v1/auth/register with the provided data', async () => {
      const userData = {
        email: 'test@example.com',
        password: 'Password1!',
        first_name: 'John',
        last_name: 'Doe',
      };
      const mockResponse = { data: { id: '1', ...userData } };
      mockPost.mockResolvedValue(mockResponse);

      const result = await register(userData);

      expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/register', userData);
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('login', () => {
    it('calls POST /api/v1/auth/login with credentials', async () => {
      const credentials = { email: 'test@example.com', password: 'Password1!' };
      const mockResponse = {
        data: { access_token: 'abc', refresh_token: 'def' },
      };
      mockPost.mockResolvedValue(mockResponse);

      const result = await login(credentials);

      expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/login', credentials);
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('refreshToken', () => {
    it('calls POST /api/v1/auth/refresh with the refresh token', async () => {
      const mockResponse = {
        data: { access_token: 'new-abc', refresh_token: 'new-def' },
      };
      mockPost.mockResolvedValue(mockResponse);

      const result = await refreshToken('my-refresh-token');

      expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/refresh', {
        refresh_token: 'my-refresh-token',
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getMe', () => {
    it('calls GET /api/v1/auth/me', async () => {
      const mockUser = { id: '1', email: 'test@example.com' };
      mockGet.mockResolvedValue({ data: mockUser });

      const result = await getMe();

      expect(mockGet).toHaveBeenCalledWith('/api/v1/auth/me');
      expect(result).toEqual(mockUser);
    });
  });

  describe('logout', () => {
    it('calls POST /api/v1/auth/logout', async () => {
      mockPost.mockResolvedValue({ data: {} });

      await logout();

      expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/logout');
    });
  });
});
