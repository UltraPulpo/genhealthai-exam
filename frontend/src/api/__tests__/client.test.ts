import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AxiosHeaders, type InternalAxiosRequestConfig } from 'axios';
import { apiClient, setAccessToken } from '../client';

function getRequestInterceptor() {
  const interceptor = apiClient.interceptors.request as unknown as {
    handlers: { fulfilled: (c: InternalAxiosRequestConfig) => InternalAxiosRequestConfig }[];
  };
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  return interceptor.handlers[0]!.fulfilled;
}

function makeConfig(): InternalAxiosRequestConfig {
  return { headers: new AxiosHeaders() };
}

describe('setAccessToken', () => {
  beforeEach(() => {
    setAccessToken(null);
  });

  it('stores a token that is used by the request interceptor', () => {
    setAccessToken('test-token-123');
    const fulfilled = getRequestInterceptor();
    const result = fulfilled(makeConfig());
    expect(result.headers.Authorization).toBe('Bearer test-token-123');
  });

  it('clears the token when set to null', () => {
    setAccessToken('some-token');
    setAccessToken(null);
    const fulfilled = getRequestInterceptor();
    const result = fulfilled(makeConfig());
    expect(result.headers.Authorization).toBeUndefined();
  });
});

describe('request interceptor', () => {
  beforeEach(() => {
    setAccessToken(null);
  });

  it('adds Authorization header when token is set', () => {
    setAccessToken('my-jwt');
    const fulfilled = getRequestInterceptor();
    const result = fulfilled(makeConfig());
    expect(result.headers.Authorization).toBe('Bearer my-jwt');
  });

  it('omits Authorization header when no token is set', () => {
    const fulfilled = getRequestInterceptor();
    const result = fulfilled(makeConfig());
    expect(result.headers.Authorization).toBeUndefined();
  });
});

describe('response interceptor', () => {
  beforeEach(() => {
    setAccessToken(null);
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('passes through successful responses', () => {
    const interceptor = apiClient.interceptors.response as unknown as {
      handlers: {
        fulfilled: (r: unknown) => unknown;
      }[];
    };
    const response = { status: 200, data: { ok: true } };
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const result = interceptor.handlers[0]!.fulfilled(response);
    expect(result).toBe(response);
  });
});
