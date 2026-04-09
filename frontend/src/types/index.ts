export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
}

export type OrderStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Order {
  id: string;
  created_by: string;
  status: OrderStatus;
  error_message: string | null;
  patient_first_name: string | null;
  patient_last_name: string | null;
  patient_dob: string | null;
  insurance_provider: string | null;
  insurance_id: string | null;
  group_number: string | null;
  ordering_provider_name: string | null;
  provider_npi: string | null;
  provider_phone: string | null;
  equipment_type: string | null;
  equipment_description: string | null;
  hcpcs_code: string | null;
  authorization_number: string | null;
  authorization_status: string | null;
  delivery_address: string | null;
  delivery_date: string | null;
  delivery_notes: string | null;
  created_at: string;
  updated_at: string;
  document: Document | null;
}

export interface Document {
  id: string;
  original_filename: string;
  content_type: string;
  file_size_bytes: number;
  extracted_data: Record<string, string | null> | null;
  uploaded_at: string;
}

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: Pagination;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details: { field: string; message: string }[];
  };
}

export interface OrderFilters {
  status?: OrderStatus;
  patient_last_name?: string;
  created_after?: string;
  created_before?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}
