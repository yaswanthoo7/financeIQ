/**
 * FinanceIQ API Client
 * Handles all communication with the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ──── Types ────

export interface LineItem {
  id?: string;
  description: string | null;
  quantity: number | null;
  unit_price: number | null;
  tax: number | null;
  discount: number | null;
  line_total: number | null;
  sort_order: number;
}

export interface Category {
  id: string;
  name: string;
  group: string; // "business" | "personal" | "custom"
  icon: string | null;
  color: string | null;
  is_system: boolean;
}

export interface InvoiceDetail {
  invoice_number: string | null;
  invoice_date: string | null;
  due_date: string | null;
  customer_name: string | null;
  payment_terms: string | null;
  subtotal: number | null;
  tax_rate: number | null;
  tax_amount: number | null;
  discount_amount: number | null;
  amount_due: number | null;
}

export interface ReceiptDetail {
  receipt_number: string | null;
  receipt_date: string | null;
  merchant_name: string | null;
  payment_method: string | null;
  subtotal: number | null;
  tax_amount: number | null;
  tip_amount: number | null;
}

export interface PurchaseOrderDetail {
  po_number: string | null;
  po_date: string | null;
  delivery_date: string | null;
  requester_name: string | null;
  approver_name: string | null;
  po_status: string | null;
  shipping_address: string | null;
  subtotal: number | null;
  tax_amount: number | null;
  shipping_cost: number | null;
}

export interface ExpenseReportDetail {
  report_number: string | null;
  report_date: string | null;
  employee_name: string | null;
  department: string | null;
  purpose: string | null;
  period_start: string | null;
  period_end: string | null;
  reimbursement_amount: number | null;
}

export interface FinancialRecord {
  id: string;
  session_id: string;
  record_type: string;
  vendor_name: string | null;
  vendor_address: string | null;
  currency: string | null;
  total_amount: number | null;
  record_date: string | null;
  category_id: string | null;
  extraction_method: string | null;
  confidence_score: number | null;
  original_filename: string;
  file_type: string | null;
  file_size_bytes: number | null;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  line_items: LineItem[];
  category: Category | null;
  invoice_detail: InvoiceDetail | null;
  receipt_detail: ReceiptDetail | null;
  purchase_order_detail: PurchaseOrderDetail | null;
  expense_report_detail: ExpenseReportDetail | null;
}

export interface RecordListItem {
  id: string;
  record_type: string;
  vendor_name: string | null;
  total_amount: number | null;
  currency: string | null;
  record_date: string | null;
  status: string;
  original_filename: string;
  confidence_score: number | null;
  created_at: string;
  line_item_count: number;
  category: Category | null;
}

export interface PaginatedResponse {
  items: RecordListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface UploadResult {
  id: string;
  filename: string;
  status: string;
  message: string;
}

export interface BulkUploadResponse {
  uploads: UploadResult[];
  total: number;
  successful: number;
  failed: number;
}

export interface QueryFilter {
  vendor_name: string | null;
  date_from: string | null;
  date_to: string | null;
  amount_min: number | null;
  amount_max: number | null;
  currency: string | null;
  status: string | null;
  record_type: string | null;
  category_name: string | null;
}

export interface QueryResponse {
  query: string;
  interpreted_filters: QueryFilter;
  results: RecordListItem[];
  total_count: number;
  explanation: string;
}

export interface VendorSpend {
  vendor_name: string;
  total_spend: number;
  record_count: number;
}

export interface CategorySpend {
  category_name: string;
  category_color: string | null;
  category_icon: string | null;
  total_spend: number;
  record_count: number;
}

export interface MonthlySpend {
  month: string;
  total_spend: number;
  record_count: number;
}

export interface RecordTypeBreakdown {
  record_type: string;
  count: number;
  total_spend: number;
}

export interface Analytics {
  total_records: number;
  total_spend: number;
  average_record_amount: number;
  top_vendors: VendorSpend[];
  spend_by_category: CategorySpend[];
  record_type_breakdown: RecordTypeBreakdown[];
  monthly_trend: MonthlySpend[];
  currencies_used: string[];
  status_breakdown: Record<string, number>;
}

// ──── Session Management ────

function getSessionId(): string {
  if (typeof window === "undefined") return "";
  let sessionId = document.cookie
    .split("; ")
    .find((row) => row.startsWith("session_id="))
    ?.split("=")[1];
  
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    document.cookie = `session_id=${sessionId}; path=/; max-age=${60 * 60 * 24 * 30}; SameSite=Lax`;
  }
  return sessionId;
}

// ──── Fetch Helper ────

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const sessionId = getSessionId();
  
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// ──── API Methods ────

export const api = {
  /** Upload financial document files */
  async uploadFiles(files: File[]): Promise<BulkUploadResponse> {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    const res = await fetch(`${API_BASE}/api/upload`, {
      method: "POST",
      body: formData,
      headers: {},
      credentials: "include",
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errorData.detail || "Upload failed");
    }

    return res.json();
  },

  /** List financial records with filters and pagination */
  async listRecords(params?: {
    page?: number;
    page_size?: number;
    vendor_name?: string;
    date_from?: string;
    date_to?: string;
    amount_min?: number;
    amount_max?: number;
    status?: string;
    record_type?: string;
    category_id?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<PaginatedResponse> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return apiFetch<PaginatedResponse>(`/api/records${query ? `?${query}` : ""}`);
  },

  /** Get financial record detail with type-specific data and line items */
  async getRecord(id: string): Promise<FinancialRecord> {
    return apiFetch<FinancialRecord>(`/api/records/${id}`);
  },

  /** Update financial record data */
  async updateRecord(id: string, data: Partial<FinancialRecord>): Promise<FinancialRecord> {
    return apiFetch<FinancialRecord>(`/api/records/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  /** Delete a financial record */
  async deleteRecord(id: string): Promise<void> {
    await apiFetch(`/api/records/${id}`, { method: "DELETE" });
  },

  /** Get the URL for the original document file */
  getFileUrl(id: string): string {
    return `${API_BASE}/api/records/${id}/file`;
  },

  /** List categories */
  async listCategories(): Promise<Category[]> {
    return apiFetch<Category[]>("/api/categories");
  },

  /** Create a custom category */
  async createCategory(data: { name: string; group: string; icon?: string; color?: string }): Promise<Category> {
    return apiFetch<Category>("/api/categories", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /** Delete a custom category */
  async deleteCategory(id: string): Promise<void> {
    await apiFetch(`/api/categories/${id}`, { method: "DELETE" });
  },

  /** Natural language query */
  async query(queryText: string): Promise<QueryResponse> {
    return apiFetch<QueryResponse>("/api/query", {
      method: "POST",
      body: JSON.stringify({ query: queryText }),
    });
  },

  /** Get analytics data */
  async getAnalytics(): Promise<Analytics> {
    return apiFetch<Analytics>("/api/analytics");
  },

  /** Health check */
  async healthCheck(): Promise<{ status: string }> {
    return apiFetch<{ status: string }>("/api/health");
  },
};
