import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import type { ReactNode } from 'react';
import { useDocumentUpload } from '../useDocumentUpload';
import * as ordersApi from '../../api/orders';
import type { Order } from '../../types';

vi.mock('../../api/orders', () => ({
  listOrders: vi.fn(),
  getOrder: vi.fn(),
  createOrder: vi.fn(),
  updateOrder: vi.fn(),
  deleteOrder: vi.fn(),
  uploadDocument: vi.fn(),
}));

const mockUploadDocument = vi.mocked(ordersApi.uploadDocument);

const testOrder: Order = {
  id: 'order-1',
  created_by: 'user-1',
  status: 'pending',
  error_message: null,
  patient_first_name: 'John',
  patient_last_name: 'Doe',
  patient_dob: '1990-01-01',
  insurance_provider: null,
  insurance_id: null,
  group_number: null,
  ordering_provider_name: null,
  provider_npi: null,
  provider_phone: null,
  equipment_type: null,
  equipment_description: null,
  hcpcs_code: null,
  authorization_number: null,
  authorization_status: null,
  delivery_address: null,
  delivery_date: null,
  delivery_notes: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  document: null,
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('useDocumentUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls uploadDocument mutation', async () => {
    mockUploadDocument.mockResolvedValue(testOrder);
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    const { result } = renderHook(() => useDocumentUpload(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ orderId: 'order-1', file });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockUploadDocument).toHaveBeenCalledWith('order-1', file);
  });
});
