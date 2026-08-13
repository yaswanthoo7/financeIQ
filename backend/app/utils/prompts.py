"""
LLM prompt templates for FinanceIQ document extraction.
"""

FINANCIAL_RECORD_EXTRACTION_PROMPT = """You are an expert financial document extraction system. Analyze the provided document and:
1. CLASSIFY the document type
2. ASSIGN a spending category
3. EXTRACT all structured data

## Step 1: Document Classification
Determine if this document is one of:
- "invoice" — a bill from a vendor for goods/services rendered
- "receipt" — proof of payment for a completed transaction
- "purchase_order" — a formal order to purchase goods/services (before payment)
- "expense_report" — a summary of expenses submitted for reimbursement

## Step 2: Category Assignment
Assign the most appropriate spending category from this list:
{categories}

If none of the above categories fit well, use "Uncategorized".

## Step 3: Field Extraction
Based on the document type, extract the relevant fields.

Return a JSON object with this exact structure:

{{
  "record_type": "invoice" | "receipt" | "purchase_order" | "expense_report",
  "category_name": "one of the categories listed above",
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "currency": "3-letter currency code like USD, EUR, GBP, INR or null",
  "total_amount": number or null,
  "record_date": "YYYY-MM-DD (the primary date of the document) or null",
  "confidence_score": number between 0 and 1 representing overall extraction confidence,

  "invoice_detail": {{
    "invoice_number": "string or null",
    "invoice_date": "YYYY-MM-DD or null",
    "due_date": "YYYY-MM-DD or null",
    "customer_name": "string or null",
    "payment_terms": "string like 'Net 30', 'Due on receipt' or null",
    "subtotal": number or null,
    "tax_rate": number (percentage, e.g. 18 for 18%) or null,
    "tax_amount": number or null,
    "discount_amount": number or null,
    "amount_due": number or null
  }},

  "receipt_detail": {{
    "receipt_number": "string or null",
    "receipt_date": "YYYY-MM-DD or null",
    "merchant_name": "string or null",
    "payment_method": "cash, credit_card, debit_card, upi, bank_transfer, or null",
    "subtotal": number or null,
    "tax_amount": number or null,
    "tip_amount": number or null
  }},

  "purchase_order_detail": {{
    "po_number": "string or null",
    "po_date": "YYYY-MM-DD or null",
    "delivery_date": "YYYY-MM-DD or null",
    "requester_name": "string or null",
    "approver_name": "string or null",
    "po_status": "draft, submitted, approved, or fulfilled — infer from document context or null",
    "shipping_address": "string or null",
    "subtotal": number or null,
    "tax_amount": number or null,
    "shipping_cost": number or null
  }},

  "expense_report_detail": {{
    "report_number": "string or null",
    "report_date": "YYYY-MM-DD or null",
    "employee_name": "string or null",
    "department": "string or null",
    "purpose": "string or null",
    "period_start": "YYYY-MM-DD or null",
    "period_end": "YYYY-MM-DD or null",
    "reimbursement_amount": number or null
  }},

  "line_items": [
    {{
      "description": "string",
      "quantity": number or null,
      "unit_price": number or null,
      "tax": number or null,
      "discount": number or null,
      "line_total": number or null
    }}
  ]
}}

Important rules:
1. Only populate the detail object that matches the detected record_type. Set the other detail objects to null.
2. Extract ALL line items from the document, maintaining their original order.
3. For amounts, use numeric values without currency symbols.
4. For dates, use ISO 8601 format (YYYY-MM-DD).
5. If the invoice is in a non-English language, still extract the data and translate field values to English.
6. If the document is not a financial document at all, set confidence_score to 0, record_type to "receipt", and leave other fields null.
7. Be precise with numbers — double-check totals against line items when possible.
8. The confidence_score should reflect how certain you are about the extraction:
   - 0.9-1.0: Clear, well-formatted document with all fields visible
   - 0.7-0.9: Most fields clear, some minor ambiguity
   - 0.5-0.7: Significant ambiguity, blurry text, or unusual format
   - 0.0-0.5: Very poor quality, mostly guessing

Return ONLY the JSON object, no additional text or markdown formatting."""


HYBRID_FINANCIAL_RECORD_PROMPT = """You are an expert financial document extraction system. The following text and table data was extracted from a financial document using OCR/PDF parsing.

Analyze this extracted content, classify the document type, assign a category, and structure the data.

--- EXTRACTED CONTENT ---
{extracted_text}
--- END CONTENT ---

## Document Classification
Determine if this is an: "invoice", "receipt", "purchase_order", or "expense_report".

## Category Assignment
Assign the most appropriate spending category from this list:
{categories}

If none fit, use "Uncategorized".

Return a JSON object with this exact structure:

{{
  "record_type": "invoice" | "receipt" | "purchase_order" | "expense_report",
  "category_name": "one of the categories listed above",
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "currency": "3-letter currency code like USD, EUR, GBP, INR or null",
  "total_amount": number or null,
  "record_date": "YYYY-MM-DD or null",
  "confidence_score": number between 0 and 1,

  "invoice_detail": {{
    "invoice_number": "string or null",
    "invoice_date": "YYYY-MM-DD or null",
    "due_date": "YYYY-MM-DD or null",
    "customer_name": "string or null",
    "payment_terms": "string or null",
    "subtotal": number or null,
    "tax_rate": number or null,
    "tax_amount": number or null,
    "discount_amount": number or null,
    "amount_due": number or null
  }},

  "receipt_detail": {{
    "receipt_number": "string or null",
    "receipt_date": "YYYY-MM-DD or null",
    "merchant_name": "string or null",
    "payment_method": "string or null",
    "subtotal": number or null,
    "tax_amount": number or null,
    "tip_amount": number or null
  }},

  "purchase_order_detail": {{
    "po_number": "string or null",
    "po_date": "YYYY-MM-DD or null",
    "delivery_date": "YYYY-MM-DD or null",
    "requester_name": "string or null",
    "approver_name": "string or null",
    "po_status": "string or null",
    "shipping_address": "string or null",
    "subtotal": number or null,
    "tax_amount": number or null,
    "shipping_cost": number or null
  }},

  "expense_report_detail": {{
    "report_number": "string or null",
    "report_date": "YYYY-MM-DD or null",
    "employee_name": "string or null",
    "department": "string or null",
    "purpose": "string or null",
    "period_start": "YYYY-MM-DD or null",
    "period_end": "YYYY-MM-DD or null",
    "reimbursement_amount": number or null
  }},

  "line_items": [
    {{
      "description": "string",
      "quantity": number or null,
      "unit_price": number or null,
      "tax": number or null,
      "discount": number or null,
      "line_total": number or null
    }}
  ]
}}

Important rules:
1. Only populate the detail object matching the detected record_type. Set others to null.
2. The OCR text may contain errors — use context to correct obvious mistakes.
3. Extract ALL line items, maintaining their original order.
4. For amounts, use numeric values without currency symbols.
5. For dates, use ISO 8601 format (YYYY-MM-DD).
6. The confidence_score should reflect the quality of the source text and your certainty.

Return ONLY the JSON object, no additional text or markdown formatting."""


NL_QUERY_PROMPT = """You are a query interpreter for a financial records management system called FinanceIQ. Convert the user's natural language query into structured filters.

The database has financial records (invoices, receipts, purchase orders, expense reports) with these filterable fields:
- vendor_name (string): The vendor/supplier/merchant name
- date_from (date, YYYY-MM-DD): Filter records on or after this date
- date_to (date, YYYY-MM-DD): Filter records on or before this date
- amount_min (number): Minimum total_amount
- amount_max (number): Maximum total_amount
- currency (string): 3-letter currency code
- status (string): one of 'processing', 'completed', 'failed', 'needs_review'
- record_type (string): one of 'invoice', 'receipt', 'purchase_order', 'expense_report'
- category_name (string): spending category like 'Software & SaaS', 'Healthcare', 'Travel', 'Groceries', 'Office Supplies', etc.

Today's date is {today}.

User query: "{query}"

Return a JSON object with these fields (use null for filters that don't apply):

{{
  "vendor_name": "string or null (use partial match — just the key name part)",
  "date_from": "YYYY-MM-DD or null",
  "date_to": "YYYY-MM-DD or null",
  "amount_min": number or null,
  "amount_max": number or null,
  "currency": "string or null",
  "status": "string or null",
  "record_type": "string or null",
  "category_name": "string or null",
  "explanation": "Brief human-readable explanation of how you interpreted the query"
}}

Examples:
- "invoices from Acme over $500" → {{"vendor_name": "Acme", "record_type": "invoice", "amount_min": 500, "explanation": "Filtering for invoices from vendor Acme with total amount above $500"}}
- "how much did I spend on software this quarter?" → {{"category_name": "Software & SaaS", "date_from": "2026-07-01", "date_to": "2026-09-30", "explanation": "Filtering for records in Software & SaaS category for the current quarter"}}
- "all receipts this month" → {{"record_type": "receipt", "date_from": "2026-08-01", "date_to": "2026-08-31", "explanation": "Filtering for receipts in the current month"}}
- "healthcare expenses over 1000" → {{"category_name": "Healthcare", "amount_min": 1000, "explanation": "Filtering for healthcare records with total above 1000"}}
- "pending purchase orders" → {{"record_type": "purchase_order", "status": "needs_review", "explanation": "Filtering for purchase orders awaiting review"}}

Return ONLY the JSON object, no additional text."""
