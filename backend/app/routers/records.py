"""
Financial records CRUD endpoints.
"""
import os
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Cookie, Header
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.financial_record import (
    FinancialRecord, LineItem, Category,
    InvoiceDetail, ReceiptDetail, PurchaseOrderDetail, ExpenseReportDetail,
)
from app.models.schemas import (
    FinancialRecordResponse, FinancialRecordListResponse, FinancialRecordUpdate,
    PaginatedResponse, LineItemUpdate, CategoryResponse,
)

router = APIRouter(prefix="/api/records", tags=["records"])


def get_session_id(session_id: str | None = Cookie(default=None), x_session_id: str | None = Header(default=None)) -> str:
    sid = x_session_id or session_id
    if not sid:
        raise HTTPException(status_code=400, detail="No session ID. Please upload a document first.")
    return sid


@router.get("", response_model=PaginatedResponse)
async def list_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    vendor_name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    status: Optional[str] = None,
    record_type: Optional[str] = None,
    category_id: Optional[str] = None,
    sort_by: str = Query(default="created_at", pattern="^(created_at|record_date|vendor_name|total_amount)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """List financial records with filtering, sorting, and pagination."""
    query = select(FinancialRecord).where(FinancialRecord.session_id == session_id)
    count_query = select(func.count(FinancialRecord.id)).where(FinancialRecord.session_id == session_id)
    
    # Apply filters
    if vendor_name:
        query = query.where(FinancialRecord.vendor_name.ilike(f"%{vendor_name}%"))
        count_query = count_query.where(FinancialRecord.vendor_name.ilike(f"%{vendor_name}%"))
    if date_from:
        query = query.where(FinancialRecord.record_date >= date_from)
        count_query = count_query.where(FinancialRecord.record_date >= date_from)
    if date_to:
        query = query.where(FinancialRecord.record_date <= date_to)
        count_query = count_query.where(FinancialRecord.record_date <= date_to)
    if amount_min is not None:
        query = query.where(FinancialRecord.total_amount >= amount_min)
        count_query = count_query.where(FinancialRecord.total_amount >= amount_min)
    if amount_max is not None:
        query = query.where(FinancialRecord.total_amount <= amount_max)
        count_query = count_query.where(FinancialRecord.total_amount <= amount_max)
    if status:
        query = query.where(FinancialRecord.status == status)
        count_query = count_query.where(FinancialRecord.status == status)
    if record_type:
        query = query.where(FinancialRecord.record_type == record_type)
        count_query = count_query.where(FinancialRecord.record_type == record_type)
    if category_id:
        query = query.where(FinancialRecord.category_id == UUID(category_id))
        count_query = count_query.where(FinancialRecord.category_id == UUID(category_id))
    
    # Get total count
    total = await db.scalar(count_query) or 0
    
    # Apply sorting
    sort_column = getattr(FinancialRecord, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Load with relationships
    query = query.options(
        selectinload(FinancialRecord.line_items),
        selectinload(FinancialRecord.category),
    )
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    items = [
        FinancialRecordListResponse(
            id=rec.id,
            record_type=rec.record_type,
            vendor_name=rec.vendor_name,
            total_amount=rec.total_amount,
            currency=rec.currency,
            record_date=rec.record_date,
            status=rec.status,
            original_filename=rec.original_filename,
            confidence_score=rec.confidence_score,
            created_at=rec.created_at,
            line_item_count=len(rec.line_items),
            category=CategoryResponse(
                id=rec.category.id,
                name=rec.category.name,
                group=rec.category.group,
                icon=rec.category.icon,
                color=rec.category.color,
                is_system=rec.category.is_system,
            ) if rec.category else None,
        )
        for rec in records
    ]
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{record_id}", response_model=FinancialRecordResponse)
async def get_record(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """Get detailed financial record data including type-specific details and line items."""
    query = (
        select(FinancialRecord)
        .where(FinancialRecord.id == record_id, FinancialRecord.session_id == session_id)
        .options(
            selectinload(FinancialRecord.line_items),
            selectinload(FinancialRecord.category),
            selectinload(FinancialRecord.invoice_detail),
            selectinload(FinancialRecord.receipt_detail),
            selectinload(FinancialRecord.purchase_order_detail),
            selectinload(FinancialRecord.expense_report_detail),
        )
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return record


@router.put("/{record_id}", response_model=FinancialRecordResponse)
async def update_record(
    record_id: UUID,
    update_data: FinancialRecordUpdate,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """Update extracted financial record data (after user review/edit)."""
    query = (
        select(FinancialRecord)
        .where(FinancialRecord.id == record_id, FinancialRecord.session_id == session_id)
        .options(
            selectinload(FinancialRecord.line_items),
            selectinload(FinancialRecord.invoice_detail),
            selectinload(FinancialRecord.receipt_detail),
            selectinload(FinancialRecord.purchase_order_detail),
            selectinload(FinancialRecord.expense_report_detail),
        )
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Update common fields
    update_dict = update_data.model_dump(
        exclude_unset=True,
        exclude={"line_items", "invoice_detail", "receipt_detail", "purchase_order_detail", "expense_report_detail"},
    )
    for key, value in update_dict.items():
        setattr(record, key, value)
    
    # Update type-specific details
    if update_data.invoice_detail is not None and record.invoice_detail:
        detail_dict = update_data.invoice_detail.model_dump(exclude_unset=True)
        for key, value in detail_dict.items():
            setattr(record.invoice_detail, key, value)
    
    if update_data.receipt_detail is not None and record.receipt_detail:
        detail_dict = update_data.receipt_detail.model_dump(exclude_unset=True)
        for key, value in detail_dict.items():
            setattr(record.receipt_detail, key, value)
    
    if update_data.purchase_order_detail is not None and record.purchase_order_detail:
        detail_dict = update_data.purchase_order_detail.model_dump(exclude_unset=True)
        for key, value in detail_dict.items():
            setattr(record.purchase_order_detail, key, value)
    
    if update_data.expense_report_detail is not None and record.expense_report_detail:
        detail_dict = update_data.expense_report_detail.model_dump(exclude_unset=True)
        for key, value in detail_dict.items():
            setattr(record.expense_report_detail, key, value)
    
    # Update line items if provided
    if update_data.line_items is not None:
        # Remove existing line items
        for item in record.line_items:
            await db.delete(item)
        
        # Add new line items
        for i, item_data in enumerate(update_data.line_items):
            line_item = LineItem(
                financial_record_id=record_id,
                sort_order=i,
                **item_data.model_dump(exclude_unset=True, exclude={"sort_order"}),
            )
            db.add(line_item)
    
    # Mark as completed if it was in needs_review
    if record.status == "needs_review":
        record.status = "completed"
    
    await db.commit()
    
    # Reload with all relationships
    query = (
        select(FinancialRecord)
        .where(FinancialRecord.id == record_id)
        .options(
            selectinload(FinancialRecord.line_items),
            selectinload(FinancialRecord.category),
            selectinload(FinancialRecord.invoice_detail),
            selectinload(FinancialRecord.receipt_detail),
            selectinload(FinancialRecord.purchase_order_detail),
            selectinload(FinancialRecord.expense_report_detail),
        )
    )
    result = await db.execute(query)
    return result.scalar_one()


@router.delete("/{record_id}")
async def delete_record(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """Delete a financial record and its file."""
    query = select(FinancialRecord).where(
        FinancialRecord.id == record_id, FinancialRecord.session_id == session_id
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Delete file from disk
    if record.file_path and os.path.exists(record.file_path):
        try:
            os.remove(record.file_path)
        except OSError:
            pass  # File already gone, that's fine
    
    await db.delete(record)
    await db.commit()
    
    return {"message": "Record deleted successfully"}


@router.get("/{record_id}/file")
async def get_record_file(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """Serve the original uploaded file."""
    query = select(FinancialRecord).where(
        FinancialRecord.id == record_id, FinancialRecord.session_id == session_id
    )
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    if not record.file_path or not os.path.exists(record.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Determine media type
    media_type_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(record.file_type or "", "application/octet-stream")
    
    return FileResponse(
        path=record.file_path,
        media_type=media_type,
        filename=record.original_filename,
    )
