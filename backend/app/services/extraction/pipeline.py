"""
Extraction pipeline orchestration.
Manages the extraction flow with fallback logic and database updates.
Handles all four document types: invoices, receipts, purchase orders, expense reports.
"""
import asyncio
import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models.financial_record import (
    FinancialRecord, InvoiceDetail, ReceiptDetail,
    PurchaseOrderDetail, ExpenseReportDetail, LineItem, Category,
)
from app.models.enums import RecordType
from app.config import get_settings
from app.services.extraction.llm_extractor import extract_with_llm
from app.services.extraction.auditor import AuditorService
import json

logger = logging.getLogger(__name__)
settings = get_settings()


def safe_decimal(value) -> Decimal | None:
    """Safely convert a value to Decimal."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def safe_date(value) -> date | None:
    """Safely parse a date string."""
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


async def process_record(record_id: str):
    """
    Extraction pipeline called by FastAPI BackgroundTasks.
    """
    await _process_record_async(record_id)


async def _process_record_async(record_id: str):
    """
    Main extraction pipeline:
    1. Try LLM-only extraction
    2. If confidence is low, try hybrid extraction
    3. Save results to database (with type-specific detail + category)
    """
    async with async_session() as db:
        try:
            # Get the record
            query = select(FinancialRecord).where(FinancialRecord.id == UUID(record_id))
            result = await db.execute(query)
            record = result.scalar_one_or_none()
            
            if not record:
                logger.error(f"Record {record_id} not found")
                return
            
            logger.info(f"Starting extraction for record {record_id}: {record.original_filename}")
            
            extracted_data = None
            extraction_error = None
            
            # Step 1: LLM-only extraction
            try:
                extracted_data = await extract_with_llm(record.file_path)
                confidence = extracted_data.get("confidence_score", 0)
                
                logger.info(f"LLM-only extraction confidence: {confidence}")
                
            except Exception as e:
                logger.warning(f"LLM-only extraction failed: {e}")
                extraction_error = f"Extraction failed: {str(e)[:200]}"
                logger.error(extraction_error)
            
            # Step 2: Save results
            if extracted_data:
                await _save_extraction_results(db, record, extracted_data)
            else:
                record.status = "failed"
                record.error_message = extraction_error or "Extraction failed with no results"
                await db.commit()
                
        except Exception as e:
            logger.exception(f"Unexpected error processing record {record_id}: {e}")
            try:
                record.status = "failed"
                record.error_message = f"Unexpected error: {str(e)[:500]}"
                await db.commit()
            except Exception:
                pass


async def _match_or_create_category(db, session_id: str, category_name: str | None) -> UUID | None:
    """Match extracted category name to an existing category, or return None."""
    if not category_name or category_name.strip() == "Uncategorized":
        return None
    
    import re
    
    # Strip group suffix the LLM may append, e.g. "Healthcare (Personal)" → "Healthcare"
    cleaned_name = re.sub(r'\s*\((?:Business|Personal|Custom)\)\s*$', '', category_name, flags=re.IGNORECASE).strip()
    
    # Try exact match first (case-insensitive)
    session_filter = (Category.session_id == None) | (Category.session_id == session_id)
    
    for name_to_try in [cleaned_name, category_name]:
        query = select(Category).where(
            Category.name.ilike(name_to_try),
            session_filter,
        )
        result = await db.execute(query)
        category = result.scalar_one_or_none()
        if category:
            return category.id
    
    # Fallback: partial match — check if the LLM name contains a known category name
    all_cats_result = await db.execute(
        select(Category).where(session_filter)
    )
    all_cats = all_cats_result.scalars().all()
    
    for cat in all_cats:
        if cat.name.lower() in cleaned_name.lower() or cleaned_name.lower() in cat.name.lower():
            logger.info(f"Partial category match: '{category_name}' → '{cat.name}'")
            return cat.id
    
    # No match found — return None (don't create unknown categories)
    logger.info(f"No matching category found for '{category_name}'")
    return None


def _validate_record_type(record_type: str | None) -> str:
    """Validate and normalize the record_type field."""
    valid_types = {rt.value for rt in RecordType}
    if record_type and record_type in valid_types:
        return record_type
    # Default to invoice if classification fails
    return RecordType.INVOICE.value


async def _save_extraction_results(db, record: FinancialRecord, data: dict):
    """Save extracted data to the financial record and create type-specific details + line items."""
    
    # Set record type from classification
    record_type = _validate_record_type(data.get("record_type"))
    record.record_type = record_type
    
    # Match category
    category_id = await _match_or_create_category(
        db, record.session_id, data.get("category_name")
    )
    record.category_id = category_id
    
    # Update common fields
    record.vendor_name = data.get("vendor_name")
    record.vendor_address = data.get("vendor_address")
    record.currency = data.get("currency", "USD")
    record.total_amount = safe_decimal(data.get("total_amount"))
    record.record_date = safe_date(data.get("record_date"))
    record.extraction_method = data.get("extraction_method", "llm_only")
    record.confidence_score = safe_decimal(data.get("confidence_score"))
    record.raw_text = data.get("raw_text", "")
    
    # Determine status based on confidence
    confidence = float(data.get("confidence_score", 0))
    if confidence >= 0.8:
        record.status = "completed"
    elif confidence >= 0.5:
        record.status = "needs_review"
    else:
        record.status = "needs_review"
        record.error_message = "Low confidence extraction — please review all fields"

    # Audit the data
    if record_type == RecordType.INVOICE.value:
        auditor = AuditorService()
        invoice_detail = data.get("invoice_detail") or {}
        anomalies = auditor.audit_invoice(invoice_detail)
        if anomalies:
            record.status = "needs_review"
            record.anomalies = json.dumps([{"field": a.field, "message": a.message} for a in anomalies])
    
    # Create type-specific detail record
    if record_type == RecordType.INVOICE.value:
        _save_invoice_detail(db, record, data.get("invoice_detail") or {})
    elif record_type == RecordType.RECEIPT.value:
        _save_receipt_detail(db, record, data.get("receipt_detail") or {})
    elif record_type == RecordType.PURCHASE_ORDER.value:
        _save_purchase_order_detail(db, record, data.get("purchase_order_detail") or {})
    elif record_type == RecordType.EXPENSE_REPORT.value:
        _save_expense_report_detail(db, record, data.get("expense_report_detail") or {})
    
    # Create line items
    line_items = data.get("line_items") or []
    for i, item_data in enumerate(line_items):
        if not isinstance(item_data, dict):
            continue
        line_item = LineItem(
            financial_record_id=record.id,
            description=item_data.get("description"),
            quantity=safe_decimal(item_data.get("quantity")),
            unit_price=safe_decimal(item_data.get("unit_price")),
            tax=safe_decimal(item_data.get("tax", 0)),
            discount=safe_decimal(item_data.get("discount", 0)),
            line_total=safe_decimal(item_data.get("line_total")),
            sort_order=i,
        )
        db.add(line_item)
    
    await db.commit()
    logger.info(
        f"Record {record.id} extraction saved: "
        f"type={record.record_type}, "
        f"method={record.extraction_method}, "
        f"confidence={record.confidence_score}, "
        f"status={record.status}, "
        f"category_id={record.category_id}, "
        f"line_items={len(line_items)}"
    )


def _save_invoice_detail(db, record: FinancialRecord, detail: dict):
    """Create InvoiceDetail child record."""
    invoice_detail = InvoiceDetail(
        financial_record_id=record.id,
        invoice_number=detail.get("invoice_number"),
        invoice_date=safe_date(detail.get("invoice_date")),
        due_date=safe_date(detail.get("due_date")),
        customer_name=detail.get("customer_name"),
        payment_terms=detail.get("payment_terms"),
        subtotal=safe_decimal(detail.get("subtotal")),
        tax_rate=safe_decimal(detail.get("tax_rate")),
        tax_amount=safe_decimal(detail.get("tax_amount")),
        discount_amount=safe_decimal(detail.get("discount_amount")),
        amount_due=safe_decimal(detail.get("amount_due")),
    )
    db.add(invoice_detail)


def _save_receipt_detail(db, record: FinancialRecord, detail: dict):
    """Create ReceiptDetail child record."""
    receipt_detail = ReceiptDetail(
        financial_record_id=record.id,
        receipt_number=detail.get("receipt_number"),
        receipt_date=safe_date(detail.get("receipt_date")),
        merchant_name=detail.get("merchant_name"),
        payment_method=detail.get("payment_method"),
        subtotal=safe_decimal(detail.get("subtotal")),
        tax_amount=safe_decimal(detail.get("tax_amount")),
        tip_amount=safe_decimal(detail.get("tip_amount")),
    )
    db.add(receipt_detail)


def _save_purchase_order_detail(db, record: FinancialRecord, detail: dict):
    """Create PurchaseOrderDetail child record."""
    po_detail = PurchaseOrderDetail(
        financial_record_id=record.id,
        po_number=detail.get("po_number"),
        po_date=safe_date(detail.get("po_date")),
        delivery_date=safe_date(detail.get("delivery_date")),
        requester_name=detail.get("requester_name"),
        approver_name=detail.get("approver_name"),
        po_status=detail.get("po_status"),
        shipping_address=detail.get("shipping_address"),
        subtotal=safe_decimal(detail.get("subtotal")),
        tax_amount=safe_decimal(detail.get("tax_amount")),
        shipping_cost=safe_decimal(detail.get("shipping_cost")),
    )
    db.add(po_detail)


def _save_expense_report_detail(db, record: FinancialRecord, detail: dict):
    """Create ExpenseReportDetail child record."""
    expense_detail = ExpenseReportDetail(
        financial_record_id=record.id,
        report_number=detail.get("report_number"),
        report_date=safe_date(detail.get("report_date")),
        employee_name=detail.get("employee_name"),
        department=detail.get("department"),
        purpose=detail.get("purpose"),
        period_start=safe_date(detail.get("period_start")),
        period_end=safe_date(detail.get("period_end")),
        reimbursement_amount=safe_decimal(detail.get("reimbursement_amount")),
    )
    db.add(expense_detail)
