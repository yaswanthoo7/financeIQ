"""
Pytest unit tests for document classification and record type validation.
"""
import pytest
from app.services.extraction.pipeline import _validate_record_type
from app.models.enums import RecordType


def test_classify_all_valid_types():
    """All four valid record types should be accepted."""
    for rt in RecordType:
        assert _validate_record_type(rt.value) == rt.value


def test_classify_invalid_type_defaults_to_invoice():
    """Invalid or missing record types should default to 'invoice'."""
    assert _validate_record_type("contract") == "invoice"
    assert _validate_record_type("bank_statement") == "invoice"
    assert _validate_record_type("") == "invoice"
    assert _validate_record_type(None) == "invoice"


def test_classify_case_sensitive():
    """Record type classification should be case-sensitive (LLM returns lowercase)."""
    assert _validate_record_type("INVOICE") == "invoice"  # defaults since not exact match
    assert _validate_record_type("Receipt") == "invoice"  # defaults since not exact match
    assert _validate_record_type("invoice") == "invoice"
    assert _validate_record_type("receipt") == "receipt"


def test_category_list_builder():
    """The category list builder should produce a formatted string."""
    from app.services.extraction.llm_extractor import _get_category_list
    category_list = _get_category_list()
    assert "Office Supplies" in category_list
    assert "Healthcare" in category_list
    assert "Uncategorized" in category_list
    assert "(Business)" in category_list
    assert "(Personal)" in category_list
