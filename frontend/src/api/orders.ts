import type { Order, PaginatedResponse, OrderFilters } from '../types';
import { apiClient } from './client';

export async function createOrder(data: Partial<Order>): Promise<Order> {
  const response = await apiClient.post<Order>('/api/v1/orders/', data);
  return response.data;
}

export async function listOrders(
  params: { page?: number; per_page?: number } & OrderFilters,
): Promise<PaginatedResponse<Order>> {
  const response = await apiClient.get<PaginatedResponse<Order>>('/api/v1/orders/', { params });
  return response.data;
}

export async function getOrder(id: string): Promise<Order> {
  const response = await apiClient.get<Order>(`/api/v1/orders/${id}`);
  return response.data;
}

export async function updateOrder(id: string, data: Partial<Order>): Promise<Order> {
  const response = await apiClient.put<Order>(`/api/v1/orders/${id}`, data);
  return response.data;
}

export async function deleteOrder(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/orders/${id}`);
}

export async function uploadDocument(orderId: string, file: File): Promise<Order> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<Order>(`/api/v1/orders/${orderId}/upload/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}
