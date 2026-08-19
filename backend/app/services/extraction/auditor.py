from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class CellAnomaly:
    field: str
    message: str

class AuditorService:
    def _parse_date(self, date_str: str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    def audit_invoice(self, data: Dict[str, Any]) -> List[CellAnomaly]:
        anomalies = []
        
        # Extract values if they are in the new {"value": val, "confidence": conf} format
        def get_val(key):
            if key in data and isinstance(data[key], dict):
                return data[key].get("value")
            return None
            
        def downgrade(key):
            if key in data and isinstance(data[key], dict):
                data[key]["confidence"] = "low"

        subtotal = get_val("subtotal")
        tax = get_val("tax_amount")
        total = get_val("total_amount")

        if subtotal is not None and tax is not None and total is not None:
            # Floating point tolerance
            if abs((subtotal + tax) - total) > 0.01:
                anomalies.append(CellAnomaly(field="total_amount", message=f"Math conflict: Subtotal ({subtotal}) + Tax ({tax}) != Total ({total})"))
                downgrade("total_amount")

        invoice_date_str = get_val("invoice_date")
        due_date_str = get_val("due_date")

        if invoice_date_str and due_date_str:
            invoice_date = self._parse_date(invoice_date_str)
            due_date = self._parse_date(due_date_str)
            
            if invoice_date and due_date and due_date < invoice_date:
                anomalies.append(CellAnomaly(field="due_date", message="Date conflict: Due date is before invoice date"))
                downgrade("due_date")

        return anomalies
