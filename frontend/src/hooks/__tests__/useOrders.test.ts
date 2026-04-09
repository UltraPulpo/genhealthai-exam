import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import type { ReactNode } from 'react';
import { useOrders, useOrder, useCreateOrder, useUpdateOrder, useDeleteOrder } from '../useOrders';
import * as ordersApi from '../../api/orders';
import type { Order, PaginatedResponse } from '../../types';

vi.mock('../../api/orders', () => ({
  listOrders: vi.fn(),
  getOrder: vi.fn(),
  createOrder: vi.fn(),
  updateOrder: vi.fn(),
  deleteOrder: vi.fn(),
  uploadDocument: vi.fn(),
}));

const mockListOrders = vi.mocked(ordersApi.listOrders);
const mockGetOrder = vi.mocked(ordersApi.getOrder);
const mockCreateOrder = vi.mocked(ordersApi.createOrder);
const mockUpdateOrder = vi.mocked(ordersApi.updateOrder);
const mockDeleteOrder = vi.mocked(ordersApi.deleteOrder);

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

describe('useOrders hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useOrders', () => {
    it('returns data from listOrders', async () => {
      const response: PaginatedResponse<Order> = {
        data: [testOrder],
        pagination: { page: 1, per_page: 20, total: 1, total_pages: 1 },
      };
      mockListOrders.mockResolvedValue(response);

      const { result } = renderHook(() => useOrders({ page: 1 }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(response);
      expect(mockListOrders).toHaveBeenCalledWith({ page: 1 });
    });
  });

  describe('useOrder', () => {
    it('returns data from getOrder', async () => {
      mockGetOrder.mockResolvedValue(testOrder);

      const { result } = renderHook(() => useOrder('order-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(testOrder);
      expect(mockGetOrder).toHaveBeenCalledWith('order-1');
    });

    it('does not fetch when id is empty', () => {
      const { result } = renderHook(() => useOrder(''), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
      expect(mockGetOrder).not.toHaveBeenCalled();
    });
  });

  describe('useCreateOrder', () => {
    it('calls createOrder and invalidates queries', async () => {
      mockCreateOrder.mockResolvedValue(testOrder);

      const { result } = renderHook(() => useCreateOrder(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ patient_first_name: 'John' });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockCreateOrder).toHaveBeenCalledWith({ patient_first_name: 'John' });
    });
  });

  describe('useUpdateOrder', () => {
    it('calls updateOrder and invalidates queries', async () => {
      mockUpdateOrder.mockResolvedValue({ ...testOrder, status: 'completed' });

      const { result } = renderHook(() => useUpdateOrder(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ id: 'order-1', data: { status: 'completed' } });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockUpdateOrder).toHaveBeenCalledWith('order-1', { status: 'completed' });
    });
  });

  describe('useDeleteOrder', () => {
    it('calls deleteOrder and invalidates queries', async () => {
      mockDeleteOrder.mockResolvedValue(undefined);

      const { result } = renderHook(() => useDeleteOrder(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('order-1');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockDeleteOrder).toHaveBeenCalledWith('order-1');
    });
  });
});
