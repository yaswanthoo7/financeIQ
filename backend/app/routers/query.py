"""
Natural language query endpoint.
"""
import json
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Cookie, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.config import get_settings
from app.models.financial_record import FinancialRecord, Category
from app.models.schemas import (
    QueryRequest, QueryResponse, QueryFilter,
    FinancialRecordListResponse, CategoryResponse,
)

router = APIRouter(prefix="/api", tags=["query"])
settings = get_settings()


def get_session_id(session_id: str | None = Cookie(default=None), x_session_id: str | None = Header(default=None)) -> str:
    sid = x_session_id or session_id
    if not sid:
        raise HTTPException(status_code=400, detail="No session ID")
    return sid


@router.post("/query", response_model=QueryResponse)
async def natural_language_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """
    Process a natural language query and return matching financial records.
    Uses Gemini to interpret the query into structured filters.
    Supports filtering by record type, category, vendor, date range, and amount.
    """
    from app.utils.prompts import NL_QUERY_PROMPT
    
    try:
        from google import genai
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = NL_QUERY_PROMPT.format(
            today=date.today().isoformat(),
            query=request.query,
        )
        
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        
        # Parse LLM response
        response_text = response.text.strip()
        # Remove markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            response_text = response_text.rsplit("```", 1)[0]
        
        parsed = json.loads(response_text)
        explanation = parsed.pop("explanation", "Query interpreted successfully")
        filters = QueryFilter(**{k: v for k, v in parsed.items() if k in QueryFilter.model_fields})
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Failed to interpret the query. Please try rephrasing.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")
    
    # Build database query from filters
    query = select(FinancialRecord).where(FinancialRecord.session_id == session_id)
    
    if filters.vendor_name:
        words = [w.strip() for w in filters.vendor_name.split() if w.strip()]
        for word in words:
            query = query.where(FinancialRecord.vendor_name.ilike(f"%{word}%"))
    if filters.date_from:
        query = query.where(FinancialRecord.record_date >= filters.date_from)
    if filters.date_to:
        query = query.where(FinancialRecord.record_date <= filters.date_to)
    if filters.amount_min is not None:
        query = query.where(FinancialRecord.total_amount >= filters.amount_min)
    if filters.amount_max is not None:
        query = query.where(FinancialRecord.total_amount <= filters.amount_max)
    if filters.currency:
        query = query.where(FinancialRecord.currency == filters.currency)
    if filters.status:
        query = query.where(FinancialRecord.status == filters.status)
    if filters.record_type:
        query = query.where(FinancialRecord.record_type == filters.record_type)
    if filters.category_name:
        # Join with Category to filter by name
        query = query.join(Category, FinancialRecord.category_id == Category.id)
        query = query.where(Category.name.ilike(f"%{filters.category_name}%"))
    
    query = query.options(
        selectinload(FinancialRecord.line_items),
        selectinload(FinancialRecord.category),
    ).order_by(desc(FinancialRecord.created_at))
    
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
    
    return QueryResponse(
        query=request.query,
        interpreted_filters=filters,
        results=items,
        total_count=len(items),
        explanation=explanation,
    )
