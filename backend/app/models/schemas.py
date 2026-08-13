"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


# ──── Line Item Schemas ────

class LineItemBase(BaseModel):
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    tax: Optional[Decimal] = Field(default=Decimal("0"))
    discount: Optional[Decimal] = Field(default=Decimal("0"))
    line_total: Optional[Decimal] = None
    sort_order: int = 0


class LineItemCreate(LineItemBase):
    pass


class LineItemUpdate(LineItemBase):
    pass


class LineItemResponse(LineItemBase):
    id: UUID

    class Config:
        from_attributes = True


# ──── Category Schemas ────

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    group: str = Field(..., pattern="^(business|personal|custom)$")
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: UUID
    is_system: bool

    class Config:
        from_attributes = True


# ──── Type-Specific Detail Schemas ────

class InvoiceDetailSchema(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    customer_name: Optional[str] = None
    payment_terms: Optional[str] = None
    subtotal: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    amount_due: Optional[Decimal] = None

    class Config:
        from_attributes = True


class ReceiptDetailSchema(BaseModel):
    receipt_number: Optional[str] = None
    receipt_date: Optional[date] = None
    merchant_name: Optional[str] = None
    payment_method: Optional[str] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    tip_amount: Optional[Decimal] = None

    class Config:
        from_attributes = True


class PurchaseOrderDetailSchema(BaseModel):
    po_number: Optional[str] = None
    po_date: Optional[date] = None
    delivery_date: Optional[date] = None
    requester_name: Optional[str] = None
    approver_name: Optional[str] = None
    po_status: Optional[str] = None
    shipping_address: Optional[str] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    shipping_cost: Optional[Decimal] = None

    class Config:
        from_attributes = True


class ExpenseReportDetailSchema(BaseModel):
    report_number: Optional[str] = None
    report_date: Optional[date] = None
    employee_name: Optional[str] = None
    department: Optional[str] = None
    purpose: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    reimbursement_amount: Optional[Decimal] = None

    class Config:
        from_attributes = True


# ──── Financial Record Schemas ────

class FinancialRecordBase(BaseModel):
    record_type: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    currency: Optional[str] = "USD"
    total_amount: Optional[Decimal] = None
    record_date: Optional[date] = None
    category_id: Optional[UUID] = None


class FinancialRecordUpdate(FinancialRecordBase):
    line_items: Optional[List[LineItemUpdate]] = None
    invoice_detail: Optional[InvoiceDetailSchema] = None
    receipt_detail: Optional[ReceiptDetailSchema] = None
    purchase_order_detail: Optional[PurchaseOrderDetailSchema] = None
    expense_report_detail: Optional[ExpenseReportDetailSchema] = None


class FinancialRecordResponse(FinancialRecordBase):
    id: UUID
    session_id: str
    extraction_method: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    original_filename: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    line_items: List[LineItemResponse] = []
    category: Optional[CategoryResponse] = None
    invoice_detail: Optional[InvoiceDetailSchema] = None
    receipt_detail: Optional[ReceiptDetailSchema] = None
    purchase_order_detail: Optional[PurchaseOrderDetailSchema] = None
    expense_report_detail: Optional[ExpenseReportDetailSchema] = None

    class Config:
        from_attributes = True


class FinancialRecordListResponse(BaseModel):
    id: UUID
    record_type: str
    vendor_name: Optional[str] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    record_date: Optional[date] = None
    status: str
    original_filename: str
    confidence_score: Optional[Decimal] = None
    created_at: datetime
    line_item_count: int = 0
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True


# ──── Upload Schemas ────

class UploadResponse(BaseModel):
    id: UUID
    filename: str
    status: str
    message: str


class BulkUploadResponse(BaseModel):
    uploads: List[UploadResponse]
    total: int
    successful: int
    failed: int


# ──── Query Schemas ────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Natural language query")


class QueryFilter(BaseModel):
    vendor_name: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    record_type: Optional[str] = None
    category_name: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    interpreted_filters: QueryFilter
    results: List[FinancialRecordListResponse]
    total_count: int
    explanation: str


# ──── Analytics Schemas ────

class VendorSpend(BaseModel):
    vendor_name: str
    total_spend: Decimal
    record_count: int


class CategorySpend(BaseModel):
    category_name: str
    category_color: Optional[str] = None
    category_icon: Optional[str] = None
    total_spend: Decimal
    record_count: int


class MonthlySpend(BaseModel):
    month: str  # YYYY-MM
    total_spend: Decimal
    record_count: int


class RecordTypeBreakdown(BaseModel):
    record_type: str
    count: int
    total_spend: Decimal


class AnalyticsResponse(BaseModel):
    total_records: int
    total_spend: Decimal
    average_record_amount: Decimal
    top_vendors: List[VendorSpend]
    spend_by_category: List[CategorySpend]
    record_type_breakdown: List[RecordTypeBreakdown]
    monthly_trend: List[MonthlySpend]
    currencies_used: List[str]
    status_breakdown: dict


# ──── Pagination ────

class PaginatedResponse(BaseModel):
    items: List[FinancialRecordListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
