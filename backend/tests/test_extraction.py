"""
Pytest unit tests for extraction schemas and data processing.
"""
import pytest
from decimal import Decimal
from datetime import date
from app.services.extraction.pipeline import safe_decimal, safe_date, _validate_record_type


def test_safe_decimal():
    assert safe_decimal("123.45") == Decimal("123.45")
    assert safe_decimal(100) == Decimal("100")
    assert safe_decimal(None) is None
    assert safe_decimal("invalid") is None


def test_safe_date():
    assert safe_date("2024-05-15") == date(2024, 5, 15)
    assert safe_date(None) is None
    assert safe_date("invalid-date") is None
    assert safe_date("15/05/2024") is None  # strict ISO format


def test_validate_record_type():
    assert _validate_record_type("invoice") == "invoice"
    assert _validate_record_type("receipt") == "receipt"
    assert _validate_record_type("purchase_order") == "purchase_order"
    assert _validate_record_type("expense_report") == "expense_report"
    # Invalid types should default to invoice
    assert _validate_record_type("unknown") == "invoice"
    assert _validate_record_type(None) == "invoice"
    assert _validate_record_type("") == "invoice"
