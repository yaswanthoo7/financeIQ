import pytest
from decimal import Decimal
from app.services.extraction.auditor import AuditorService, CellAnomaly

def test_audit_invoice_valid_math():
    auditor = AuditorService()
    # A mocked parsed result with cell-level confidence
    invoice_data = {
        "subtotal": {"value": 100.0, "confidence": "high"},
        "tax_amount": {"value": 10.0, "confidence": "high"},
        "total_amount": {"value": 110.0, "confidence": "high"},
        "invoice_date": {"value": "2023-01-01", "confidence": "high"},
        "due_date": {"value": "2023-01-15", "confidence": "high"}
    }
    anomalies = auditor.audit_invoice(invoice_data)
    assert len(anomalies) == 0
    assert invoice_data["total_amount"]["confidence"] == "high"

def test_audit_invoice_invalid_math():
    auditor = AuditorService()
    invoice_data = {
        "subtotal": {"value": 100.0, "confidence": "high"},
        "tax_amount": {"value": 10.0, "confidence": "high"},
        "total_amount": {"value": 150.0, "confidence": "high"}
    }
    anomalies = auditor.audit_invoice(invoice_data)
    assert len(anomalies) == 1
    assert anomalies[0].field == "total_amount"
    assert "Math conflict" in anomalies[0].message
    assert invoice_data["total_amount"]["confidence"] == "low"

def test_audit_invoice_invalid_dates():
    auditor = AuditorService()
    invoice_data = {
        "invoice_date": {"value": "2023-01-15", "confidence": "high"},
        "due_date": {"value": "2023-01-01", "confidence": "high"}
    }
    anomalies = auditor.audit_invoice(invoice_data)
    assert len(anomalies) == 1
    assert anomalies[0].field == "due_date"
    assert "Date conflict" in anomalies[0].message
    assert invoice_data["due_date"]["confidence"] == "low"
