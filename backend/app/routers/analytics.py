"""
Analytics/dashboard endpoints.
"""
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Cookie, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, literal_column
from app.database import get_db
from app.models.financial_record import FinancialRecord, Category
from app.models.schemas import (
    AnalyticsResponse, VendorSpend, CategorySpend,
    MonthlySpend, RecordTypeBreakdown,
)

router = APIRouter(prefix="/api", tags=["analytics"])


def get_session_id(session_id: str | None = Cookie(default=None), x_session_id: str | None = Header(default=None)) -> str:
    sid = x_session_id or session_id
    if not sid:
        raise HTTPException(status_code=400, detail="No session ID")
    return sid


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """Get dashboard analytics for the current session."""
    base_filter = FinancialRecord.session_id == session_id
    active_statuses = ["completed", "needs_review"]
    
    # Total records
    total_records = await db.scalar(
        select(func.count(FinancialRecord.id)).where(base_filter)
    ) or 0
    
    # Total spend
    total_spend = await db.scalar(
        select(func.coalesce(func.sum(FinancialRecord.total_amount), 0)).where(
            base_filter, FinancialRecord.status.in_(active_statuses)
        )
    ) or Decimal("0")
    
    # Average amount
    avg_amount = await db.scalar(
        select(func.coalesce(func.avg(FinancialRecord.total_amount), 0)).where(
            base_filter, FinancialRecord.status.in_(active_statuses)
        )
    ) or Decimal("0")
    
    # Top vendors by spend
    vendor_query = (
        select(
            FinancialRecord.vendor_name,
            func.sum(FinancialRecord.total_amount).label("total_spend"),
            func.count(FinancialRecord.id).label("record_count"),
        )
        .where(base_filter, FinancialRecord.vendor_name.isnot(None), FinancialRecord.status.in_(active_statuses))
        .group_by(FinancialRecord.vendor_name)
        .order_by(func.sum(FinancialRecord.total_amount).desc())
        .limit(10)
    )
    vendor_result = await db.execute(vendor_query)
    top_vendors = [
        VendorSpend(
            vendor_name=row.vendor_name,
            total_spend=row.total_spend or Decimal("0"),
            record_count=row.record_count,
        )
        for row in vendor_result
    ]
    
    # Spend by category
    category_query = (
        select(
            Category.name,
            Category.color,
            Category.icon,
            func.sum(FinancialRecord.total_amount).label("total_spend"),
            func.count(FinancialRecord.id).label("record_count"),
        )
        .join(Category, FinancialRecord.category_id == Category.id)
        .where(base_filter, FinancialRecord.status.in_(active_statuses))
        .group_by(Category.name, Category.color, Category.icon)
        .order_by(func.sum(FinancialRecord.total_amount).desc())
        .limit(15)
    )
    category_result = await db.execute(category_query)
    spend_by_category = [
        CategorySpend(
            category_name=row.name,
            category_color=row.color,
            category_icon=row.icon,
            total_spend=row.total_spend or Decimal("0"),
            record_count=row.record_count,
        )
        for row in category_result
    ]
    
    # Record type breakdown
    type_query = (
        select(
            FinancialRecord.record_type,
            func.count(FinancialRecord.id).label("count"),
            func.coalesce(func.sum(FinancialRecord.total_amount), 0).label("total_spend"),
        )
        .where(base_filter, FinancialRecord.status.in_(active_statuses))
        .group_by(FinancialRecord.record_type)
    )
    type_result = await db.execute(type_query)
    record_type_breakdown = [
        RecordTypeBreakdown(
            record_type=row.record_type,
            count=row.count,
            total_spend=row.total_spend or Decimal("0"),
        )
        for row in type_result
    ]
    
    # Monthly spending trend
    month_expr = literal_column("to_char(financial_records.record_date, 'YYYY-MM')")
    monthly_query = (
        select(
            month_expr.label("month"),
            func.sum(FinancialRecord.total_amount).label("total_spend"),
            func.count(FinancialRecord.id).label("record_count"),
        )
        .where(base_filter, FinancialRecord.record_date.isnot(None), FinancialRecord.status.in_(active_statuses))
        .group_by(month_expr)
        .order_by(month_expr)
        .limit(12)
    )
    monthly_result = await db.execute(monthly_query)
    monthly_trend = [
        MonthlySpend(
            month=row.month,
            total_spend=row.total_spend or Decimal("0"),
            record_count=row.record_count,
        )
        for row in monthly_result
    ]
    
    # Currencies used
    currency_result = await db.execute(
        select(FinancialRecord.currency)
        .where(base_filter, FinancialRecord.currency.isnot(None))
        .distinct()
    )
    currencies = [row[0] for row in currency_result if row[0]]
    
    # Status breakdown
    status_query = (
        select(FinancialRecord.status, func.count(FinancialRecord.id))
        .where(base_filter)
        .group_by(FinancialRecord.status)
    )
    status_result = await db.execute(status_query)
    status_breakdown = {row[0]: row[1] for row in status_result}
    
    return AnalyticsResponse(
        total_records=total_records,
        total_spend=total_spend,
        average_record_amount=round(avg_amount, 2),
        top_vendors=top_vendors,
        spend_by_category=spend_by_category,
        record_type_breakdown=record_type_breakdown,
        monthly_trend=monthly_trend,
        currencies_used=currencies,
        status_breakdown=status_breakdown,
    )
