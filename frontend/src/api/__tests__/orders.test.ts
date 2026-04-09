import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  createOrder,
  listOrders,
  getOrder,
  updateOrder,
  deleteOrder,
  uploadDocument,
} from '../orders';
import { apiClient } from '../client';

vi.mock('../client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
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
const mockPut = vi.mocked(apiClient.put);
const mockDelete = vi.mocked(apiClient.delete);
/* eslint-enable @typescript-eslint/unbound-method */

describe('orders API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createOrder', () => {
    it('calls POST /api/v1/orders with order data', async () => {
      const orderData = { patient_first_name: 'Jane', patient_last_name: 'Doe' };
      const mockResponse = { data: { id: '1', ...orderData } };
      mockPost.mockResolvedValue(mockResponse);

      const result = await createOrder(orderData);

      expect(mockPost).toHaveBeenCalledWith('/api/v1/orders', orderData);
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('listOrders', () => {
    it('calls GET /api/v1/orders with query parameters', async () => {
      const params = { page: 1, per_page: 10, status: 'pending' as const };
      const mockResponse = {
        data: { data: [], pagination: { page: 1, per_page: 10, total: 0, total_pages: 0 } },
      };
      mockGet.mockResolvedValue(mockResponse);

      const result = await listOrders(params);

      expect(mockGet).toHaveBeenCalledWith('/api/v1/orders', { params });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getOrder', () => {
    it('calls GET /api/v1/orders/:id', async () => {
      const mockResponse = { data: { id: 'abc-123', status: 'pending' } };
      mockGet.mockResolvedValue(mockResponse);

      const result = await getOrder('abc-123');

      expect(mockGet).toHaveBeenCalledWith('/api/v1/orders/abc-123');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('updateOrder', () => {
    it('calls PUT /api/v1/orders/:id with update data', async () => {
      const updateData = { patient_first_name: 'Updated' };
      const mockResponse = { data: { id: 'abc-123', ...updateData } };
      mockPut.mockResolvedValue(mockResponse);

      const result = await updateOrder('abc-123', updateData);

      expect(mockPut).toHaveBeenCalledWith('/api/v1/orders/abc-123', updateData);
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('deleteOrder', () => {
    it('calls DELETE /api/v1/orders/:id', async () => {
      mockDelete.mockResolvedValue({ data: {} });

      await deleteOrder('abc-123');

      expect(mockDelete).toHaveBeenCalledWith('/api/v1/orders/abc-123');
    });
  });

  describe('uploadDocument', () => {
    it('calls POST /api/v1/orders/:id/documents with FormData', async () => {
      const file = new File(['pdf-content'], 'test.pdf', { type: 'application/pdf' });
      const mockResponse = { data: { id: 'abc-123', document: { id: 'doc-1' } } };
      mockPost.mockResolvedValue(mockResponse);

      const result = await uploadDocument('abc-123', file);

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v1/orders/abc-123/documents',
        expect.any(FormData),
        { headers: { 'Content-Type': 'multipart/form-data' } },
      );

      // eslint-disable-next-line @typescript-eslint/unbound-method
      const callArgs = vi.mocked(apiClient.post).mock.calls[0];
      const formData = callArgs?.[1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(result).toEqual(mockResponse.data);
    });
  });
});
