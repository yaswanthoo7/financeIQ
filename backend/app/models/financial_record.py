"""
SQLAlchemy models for FinanceIQ.

Parent-child architecture:
- FinancialRecord: shared parent table with common fields
- InvoiceDetail, ReceiptDetail, PurchaseOrderDetail, ExpenseReportDetail: type-specific child tables
- LineItem: shared across all record types
- Category: spending categories (predefined + custom)
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, String, Text, Date, DateTime, Numeric,
    Integer, ForeignKey, Index, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
    """Spending category for financial records."""
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), nullable=True, index=True)  # null = system default
    name = Column(String(100), nullable=False)
    group = Column(String(20), nullable=False)  # business, personal, custom
    icon = Column(String(10), nullable=True)
    color = Column(String(7), nullable=True)  # hex color
    is_system = Column(Boolean, nullable=False, default=False)

    # Relationships
    financial_records = relationship("FinancialRecord", back_populates="category")

    __table_args__ = (
        Index("ix_categories_session_group", "session_id", "group"),
    )


class FinancialRecord(Base):
    """Parent table for all financial document types."""
    __tablename__ = "financial_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), nullable=False, index=True)

    # Classification
    record_type = Column(String(20), nullable=False, index=True)  # invoice, receipt, purchase_order, expense_report
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    # Common fields
    vendor_name = Column(String(255), nullable=True, index=True)
    vendor_address = Column(Text, nullable=True)
    currency = Column(String(3), nullable=True, default="USD")
    total_amount = Column(Numeric(12, 2), nullable=True)
    record_date = Column(Date, nullable=True)

    # Processing metadata
    extraction_method = Column(String(20), nullable=True)  # 'llm_only' or 'hybrid'
    confidence_score = Column(Numeric(3, 2), nullable=True)
    raw_text = Column(Text, nullable=True)
    anomalies = Column(Text, nullable=True)  # Stores JSON array of CellAnomaly dicts

    # File info
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), nullable=False, default="processing")
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="financial_records")
    line_items = relationship("LineItem", back_populates="financial_record", cascade="all, delete-orphan", order_by="LineItem.sort_order")
    invoice_detail = relationship("InvoiceDetail", back_populates="financial_record", uselist=False, cascade="all, delete-orphan")
    receipt_detail = relationship("ReceiptDetail", back_populates="financial_record", uselist=False, cascade="all, delete-orphan")
    purchase_order_detail = relationship("PurchaseOrderDetail", back_populates="financial_record", uselist=False, cascade="all, delete-orphan")
    expense_report_detail = relationship("ExpenseReportDetail", back_populates="financial_record", uselist=False, cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_records_vendor_date", "vendor_name", "record_date"),
        Index("ix_records_total_amount", "total_amount"),
        Index("ix_records_status", "status"),
        Index("ix_records_type_category", "record_type", "category_id"),
    )


class InvoiceDetail(Base):
    """Invoice-specific fields."""
    __tablename__ = "invoice_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    financial_record_id = Column(UUID(as_uuid=True), ForeignKey("financial_records.id", ondelete="CASCADE"), nullable=False, unique=True)

    invoice_number = Column(String(100), nullable=True)
    invoice_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    customer_name = Column(String(255), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=True)
    tax_rate = Column(Numeric(5, 2), nullable=True)
    tax_amount = Column(Numeric(12, 2), nullable=True)
    discount_amount = Column(Numeric(12, 2), nullable=True)
    amount_due = Column(Numeric(12, 2), nullable=True)

    # Relationships
    financial_record = relationship("FinancialRecord", back_populates="invoice_detail")


class ReceiptDetail(Base):
    """Receipt-specific fields."""
    __tablename__ = "receipt_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    financial_record_id = Column(UUID(as_uuid=True), ForeignKey("financial_records.id", ondelete="CASCADE"), nullable=False, unique=True)

    receipt_number = Column(String(100), nullable=True)
    receipt_date = Column(Date, nullable=True)
    merchant_name = Column(String(255), nullable=True)
    payment_method = Column(String(50), nullable=True)  # cash, credit_card, debit_card, etc.
    subtotal = Column(Numeric(12, 2), nullable=True)
    tax_amount = Column(Numeric(12, 2), nullable=True)
    tip_amount = Column(Numeric(12, 2), nullable=True)

    # Relationships
    financial_record = relationship("FinancialRecord", back_populates="receipt_detail")


class PurchaseOrderDetail(Base):
    """Purchase Order-specific fields."""
    __tablename__ = "purchase_order_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    financial_record_id = Column(UUID(as_uuid=True), ForeignKey("financial_records.id", ondelete="CASCADE"), nullable=False, unique=True)

    po_number = Column(String(100), nullable=True)
    po_date = Column(Date, nullable=True)
    delivery_date = Column(Date, nullable=True)
    requester_name = Column(String(255), nullable=True)
    approver_name = Column(String(255), nullable=True)
    po_status = Column(String(20), nullable=True, default="draft")  # draft, submitted, approved, fulfilled
    shipping_address = Column(Text, nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=True)
    tax_amount = Column(Numeric(12, 2), nullable=True)
    shipping_cost = Column(Numeric(12, 2), nullable=True)

    # Relationships
    financial_record = relationship("FinancialRecord", back_populates="purchase_order_detail")


class ExpenseReportDetail(Base):
    """Expense Report-specific fields."""
    __tablename__ = "expense_report_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    financial_record_id = Column(UUID(as_uuid=True), ForeignKey("financial_records.id", ondelete="CASCADE"), nullable=False, unique=True)

    report_number = Column(String(100), nullable=True)
    report_date = Column(Date, nullable=True)
    employee_name = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    purpose = Column(Text, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    reimbursement_amount = Column(Numeric(12, 2), nullable=True)

    # Relationships
    financial_record = relationship("FinancialRecord", back_populates="expense_report_detail")


class LineItem(Base):
    """A single line item within any financial record."""
    __tablename__ = "line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    financial_record_id = Column(UUID(as_uuid=True), ForeignKey("financial_records.id", ondelete="CASCADE"), nullable=False)

    description = Column(Text, nullable=True)
    quantity = Column(Numeric(10, 3), nullable=True)
    unit_price = Column(Numeric(12, 2), nullable=True)
    tax = Column(Numeric(12, 2), nullable=True, default=0)
    discount = Column(Numeric(12, 2), nullable=True, default=0)
    line_total = Column(Numeric(12, 2), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)

    # Relationships
    financial_record = relationship("FinancialRecord", back_populates="line_items")
