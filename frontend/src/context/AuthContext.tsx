import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import type { ReactNode } from 'react';
import type { User } from '../types';
import * as auth from '../api/auth';
import { setAccessToken } from '../api/client';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('refresh_token');
    if (!storedToken) {
      setIsLoading(false);
      return;
    }

    auth
      .refreshToken(storedToken)
      .then((data) => {
        setAccessToken(data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        return auth.getMe();
      })
      .then((profile) => {
        setUser(profile);
      })
      .catch(() => {
        localStorage.removeItem('refresh_token');
        setAccessToken(null);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const loginFn = useCallback(async (email: string, password: string) => {
    const data = await auth.login({ email, password });
    setAccessToken(data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    const profile = await auth.getMe();
    setUser(profile);
  }, []);

  const registerFn = useCallback(
    async (data: {
      email: string;
      password: string;
      first_name: string;
      last_name: string;
    }) => {
      await auth.register(data);
    },
    [],
  );

  const logoutFn = useCallback(async () => {
    try {
      await auth.logout();
    } catch {
      // Ignore logout API errors
    }
    setAccessToken(null);
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  const refreshTokenFn = useCallback(async () => {
    const storedToken = localStorage.getItem('refresh_token');
    if (!storedToken) throw new Error('No refresh token available');
    const data = await auth.refreshToken(storedToken);
    setAccessToken(data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login: loginFn,
      register: registerFn,
      logout: logoutFn,
      refreshToken: refreshTokenFn,
    }),
    [user, isLoading, loginFn, registerFn, logoutFn, refreshTokenFn],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuthContext(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}
