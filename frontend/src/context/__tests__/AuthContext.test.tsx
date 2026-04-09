import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuthContext } from '../AuthContext';
import * as auth from '../../api/auth';
import { setAccessToken } from '../../api/client';
import type { User, TokenResponse } from '../../types';

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  refreshToken: vi.fn(),
  getMe: vi.fn(),
  logout: vi.fn(),
}));

vi.mock('../../api/client', () => ({
  apiClient: {
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
  },
  setAccessToken: vi.fn(),
}));

const mockLogin = vi.mocked(auth.login);
const mockRegister = vi.mocked(auth.register);
const mockRefreshToken = vi.mocked(auth.refreshToken);
const mockGetMe = vi.mocked(auth.getMe);
const mockLogout = vi.mocked(auth.logout);
const mockSetAccessToken = vi.mocked(setAccessToken);

const testUser: User = {
  id: '1',
  email: 'test@example.com',
  first_name: 'John',
  last_name: 'Doe',
  created_at: '2026-01-01T00:00:00Z',
};

const tokenResponse: TokenResponse = {
  access_token: 'access-123',
  refresh_token: 'refresh-456',
};

function TestConsumer() {
  const { user, isAuthenticated, isLoading, login, logout } = useAuthContext();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="user">{user ? user.email : 'none'}</span>
      <button onClick={() => void login('test@example.com', 'password')}>Login</button>
      <button onClick={() => void logout()}>Logout</button>
    </div>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders children when not authenticated', async () => {
    render(
      <AuthProvider>
        <span>child content</span>
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText('child content')).toBeInTheDocument();
    });
  });

  it('does not attempt refresh when no refresh_token in localStorage', async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    expect(mockRefreshToken).not.toHaveBeenCalled();
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('user')).toHaveTextContent('none');
  });

  it('isLoading is true initially during refresh attempt', () => {
    localStorage.setItem('refresh_token', 'stored-token');
    // Never-resolving promise to keep loading state
    mockRefreshToken.mockReturnValue(new Promise(() => {}));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    expect(screen.getByTestId('loading')).toHaveTextContent('true');
  });

  it('attempts silent refresh on mount when refresh_token exists', async () => {
    localStorage.setItem('refresh_token', 'stored-token');
    mockRefreshToken.mockResolvedValue(tokenResponse);
    mockGetMe.mockResolvedValue(testUser);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    expect(mockRefreshToken).toHaveBeenCalledWith('stored-token');
    expect(mockSetAccessToken).toHaveBeenCalledWith('access-123');
    expect(localStorage.getItem('refresh_token')).toBe('refresh-456');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
  });

  it('clears tokens on failed silent refresh', async () => {
    localStorage.setItem('refresh_token', 'bad-token');
    mockRefreshToken.mockRejectedValue(new Error('invalid'));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(mockSetAccessToken).toHaveBeenCalledWith(null);
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
  });

  it('login calls API and updates user state', async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValue(tokenResponse);
    mockGetMe.mockResolvedValue(testUser);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    await user.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });

    expect(mockLogin).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password',
    });
    expect(mockSetAccessToken).toHaveBeenCalledWith('access-123');
    expect(localStorage.getItem('refresh_token')).toBe('refresh-456');
    expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
  });

  it('logout clears user state and tokens', async () => {
    const user = userEvent.setup();
    localStorage.setItem('refresh_token', 'stored-token');
    mockRefreshToken.mockResolvedValue(tokenResponse);
    mockGetMe.mockResolvedValue(testUser);
    mockLogout.mockResolvedValue(undefined);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });

    await user.click(screen.getByRole('button', { name: 'Logout' }));

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    });

    expect(mockLogout).toHaveBeenCalled();
    expect(mockSetAccessToken).toHaveBeenCalledWith(null);
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(screen.getByTestId('user')).toHaveTextContent('none');
  });

  it('logout clears state even when API call fails', async () => {
    const user = userEvent.setup();
    localStorage.setItem('refresh_token', 'stored-token');
    mockRefreshToken.mockResolvedValue(tokenResponse);
    mockGetMe.mockResolvedValue(testUser);
    mockLogout.mockRejectedValue(new Error('network error'));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });

    await user.click(screen.getByRole('button', { name: 'Logout' }));

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    });

    expect(localStorage.getItem('refresh_token')).toBeNull();
  });

  it('throws when useAuthContext is used outside AuthProvider', () => {
    // Suppress console.error for the expected error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => render(<TestConsumer />)).toThrow(
      'useAuthContext must be used within an AuthProvider',
    );

    spy.mockRestore();
  });

  it('register calls the register API without auto-login', async () => {
    const regData = {
      email: 'new@example.com',
      password: 'Password1!',
      first_name: 'Jane',
      last_name: 'Doe',
    };
    mockRegister.mockResolvedValue(testUser);

    function RegisterConsumer() {
      const { register, isAuthenticated } = useAuthContext();
      return (
        <div>
          <span data-testid="auth">{String(isAuthenticated)}</span>
          <button onClick={() => void register(regData)}>Register</button>
        </div>
      );
    }

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <RegisterConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth')).toHaveTextContent('false');
    });

    await user.click(screen.getByRole('button', { name: 'Register' }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith(regData);
    });

    // Should not auto-login
    expect(mockLogin).not.toHaveBeenCalled();
    expect(screen.getByTestId('auth')).toHaveTextContent('false');
  });
});
