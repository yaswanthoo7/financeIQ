"""
Enum definitions for FinanceIQ.
"""
from enum import Enum


class RecordType(str, Enum):
    """Types of financial documents the system can process."""
    INVOICE = "invoice"
    RECEIPT = "receipt"
    PURCHASE_ORDER = "purchase_order"
    EXPENSE_REPORT = "expense_report"


class RecordStatus(str, Enum):
    """Processing status of a financial record."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class CategoryGroup(str, Enum):
    """Grouping for spending categories."""
    BUSINESS = "business"
    PERSONAL = "personal"
    CUSTOM = "custom"


class POStatus(str, Enum):
    """Approval workflow status for Purchase Orders."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    FULFILLED = "fulfilled"


# ──── Seed Category Definitions ────

SEED_CATEGORIES = {
    CategoryGroup.BUSINESS: [
        {"name": "Office Supplies", "icon": "📎", "color": "#6366f1"},
        {"name": "Travel", "icon": "✈️", "color": "#8b5cf6"},
        {"name": "Software & SaaS", "icon": "💻", "color": "#3b82f6"},
        {"name": "Professional Services", "icon": "👔", "color": "#0ea5e9"},
        {"name": "Utilities", "icon": "⚡", "color": "#f59e0b"},
        {"name": "Marketing", "icon": "📢", "color": "#ec4899"},
        {"name": "Equipment", "icon": "🔧", "color": "#64748b"},
        {"name": "Insurance", "icon": "🛡️", "color": "#14b8a6"},
        {"name": "Shipping & Logistics", "icon": "📦", "color": "#f97316"},
    ],
    CategoryGroup.PERSONAL: [
        {"name": "Groceries", "icon": "🛒", "color": "#22c55e"},
        {"name": "Dining & Food", "icon": "🍽️", "color": "#ef4444"},
        {"name": "Healthcare", "icon": "🏥", "color": "#06b6d4"},
        {"name": "Transportation", "icon": "🚗", "color": "#a855f7"},
        {"name": "Subscriptions", "icon": "🔄", "color": "#6366f1"},
        {"name": "Rent & Housing", "icon": "🏠", "color": "#78716c"},
        {"name": "Entertainment", "icon": "🎬", "color": "#f43f5e"},
        {"name": "Clothing", "icon": "👕", "color": "#d946ef"},
        {"name": "Education", "icon": "📚", "color": "#0284c7"},
    ],
}
