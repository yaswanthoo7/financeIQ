"""
Category CRUD endpoints.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Cookie, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db
from app.models.financial_record import Category
from app.models.schemas import CategoryResponse, CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["categories"])


def get_session_id(session_id: str | None = Cookie(default=None), x_session_id: str | None = Header(default=None)) -> str:
    sid = x_session_id or session_id
    if not sid:
        raise HTTPException(status_code=400, detail="No session ID")
    return sid


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """List all categories (system defaults + user-created for this session)."""
    query = select(Category).where(
        (Category.session_id == None) | (Category.session_id == session_id)
    ).order_by(Category.group, Category.name)
    
    result = await db.execute(query)
    categories = result.scalars().all()
    return categories


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """Create a custom category for this session."""
    # Check for duplicate name within this session + system categories
    existing = await db.execute(
        select(Category).where(
            Category.name.ilike(category_data.name),
            (Category.session_id == None) | (Category.session_id == session_id),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Category '{category_data.name}' already exists")
    
    category = Category(
        id=uuid.uuid4(),
        session_id=session_id,
        name=category_data.name,
        group=category_data.group,
        icon=category_data.icon,
        color=category_data.color,
        is_system=False,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    update_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """Update a custom category. System categories cannot be modified."""
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category.is_system:
        raise HTTPException(status_code=403, detail="System categories cannot be modified")
    
    if category.session_id != session_id:
        raise HTTPException(status_code=403, detail="Cannot modify another session's category")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(category, key, value)
    
    await db.commit()
    await db.refresh(category)
    
    return category


@router.delete("/{category_id}")
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    """Delete a custom category. System categories cannot be deleted."""
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category.is_system:
        raise HTTPException(status_code=403, detail="System categories cannot be deleted")
    
    if category.session_id != session_id:
        raise HTTPException(status_code=403, detail="Cannot delete another session's category")
    
    await db.delete(category)
    await db.commit()
    
    return {"message": "Category deleted successfully"}
