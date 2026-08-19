# decisions.md — FinanceIQ

A running log of design decisions, tradeoffs, and reasoning made during the build.

---

## The Hard Problem: Silent Hallucinations and Mathematical Integrity

**The Problem:** Turning messy financial docs into structured data.
**The Hard Part:** LLMs hallucinate numbers and fail at math. In finance, a silently hallucinated total corrupts downstream accounting. Generic "Please review this document" flags are terrible UX. The hard part is catching AI mistakes deterministically and designing a UX that helps humans resolve them instantly.
**The Slice:** We implemented a deterministic `AuditorService` that cross-checks LLM extraction math (e.g. `subtotal + tax == total`) and temporal logic. This is paired with an "Anomaly Resolution" UI that flags exact cell-level conflicts, forcing strict grounding and mathematical integrity over the LLM output.

---

## 1. Problem Scoping: Core Financial Documents, Not Generic Documents

**Decision:** Support four core financial document types — **Invoices, Receipts, Purchase Orders, and Expense Reports** — rather than building a generic document parser or limiting to a single type.

**Alternatives considered:**
- Generic document parser (contracts, resumes, invoices, etc.)
- Invoice-only (deep but narrow)
- All financial documents including tax forms, bank statements, pay stubs (too broad)

**Reasoning:** The problem statement says "messy documents → structured, queryable data." Going fully generic means going shallow — each document type has different schemas, edge cases, and quality issues. Going single-type misses the opportunity to show the system can generalize. Four financial document types hit the sweet spot:
- They share enough financial DNA (vendors, amounts, dates, line items) for a unified data model
- They represent the complete picture of business and personal financial workflows — a finance team deals with all four daily
- Each type has distinct enough fields (PO approval status, receipt payment method, expense report periods) to demonstrate adaptive extraction and UI
- Tax forms and bank statements have fundamentally different structures and would need separate pipelines — we exclude them deliberately

**What this demonstrates:** The architecture isn't hardcoded for one document type. Supporting four types requires a flexible data model, a multi-schema extraction prompt, and an adaptive review UI — all of which show engineering depth beyond a single-type MVP.

---

## 2. AI Auto-Classification and Categorization

**Decision:** The system automatically classifies uploaded documents (Invoice, Receipt, PO, Expense Report) *and* assigns a spending category (e.g., "Software", "Healthcare", "Travel") using AI — with no manual selection step.

**Alternatives considered:**
- User selects document type via dropdown before uploading
- Hybrid — AI classifies but user confirms before extraction proceeds
- Two-stage pipeline — separate classification call, then extraction call
- No categories — rely on natural language search for organization

**Reasoning:** Zero-friction upload is a core product differentiator. Requiring users to label their documents defeats the purpose of an *intelligent* extraction system. If the AI can extract 15+ fields from a document, it can certainly tell the difference between an invoice and a receipt, and determine that a pharmacy receipt belongs in "Healthcare."

We perform classification, extraction, and categorization in a **single Gemini API call** — the prompt instructs the model to first identify the document type, then assign a category from a provided list, then extract type-appropriate fields. This keeps latency and API cost identical to a single-type pipeline (one call per document). Splitting into multiple calls would double or triple both latency (~2-3s per call) and API cost.

**Tradeoff accepted:** If the AI misclassifies a document, the wrong fields will be extracted. We mitigate this by showing the detected type and category prominently in the review UI so users catch errors immediately.

---

## 3. Extraction Pipeline (LLM-Only)

**Decision:** Rely entirely on LLM vision (Gemini 2.0 Flash) for extracting structured data from documents. If extraction confidence is low, we flag it for user review rather than attempting a secondary extraction method.

**Alternatives considered:**
- LLM-only (simpler, fewer dependencies)
- Traditional OCR + rule-based parsing (no LLM cost, but brittle)
- Cloud Document AI (AWS Textract / Google Document AI) — accurate but feels like "just calling an API"

**Reasoning:** LLM vision is remarkably good at understanding document layouts directly from the image/PDF. While we initially considered a hybrid approach (using OCR/unstructured.io as a fallback for dense tables or low-quality scans), the added complexity of maintaining system-level dependencies (like poppler and tesseract) outweighed the benefits. Gemini 2.0 Flash is sophisticated enough to handle edge cases in most documents. By relying solely on the LLM, we simplify our backend infrastructure significantly. When the LLM struggles, human review is the most reliable fallback.

**Tradeoff accepted:** Some very complex documents may require more manual correction if the LLM's confidence drops, since we no longer have an OCR fallback. We mitigate this by providing a highly ergonomic review UI for quick human correction.

---

## 4. Gemini 2.0 Flash Over GPT-4o / Claude

**Decision:** Use Google Gemini 2.0 Flash as the LLM provider.

**Alternatives considered:**
- GPT-4o / GPT-4o-mini (excellent structured output, needs paid API key)
- Claude 3.5 Sonnet/Haiku (strong document understanding, needs paid API key)
- Open-source LLM via Ollama (fully free, but requires GPU and complex deployment)

**Reasoning:** Gemini 2.0 Flash offers: (1) a generous free tier (1500 requests/day), (2) native vision capabilities for processing document images, and (3) good structured output quality. Free tier access is critical for rapid iteration and cost-efficiency. The quality is comparable to GPT-4o-mini for structured extraction tasks.

**Tradeoff accepted:** Gemini's structured output is slightly less deterministic than GPT-4o's JSON mode. We mitigate this with careful prompt engineering and JSON parsing with error handling.

---

## 5. Parent-Child Data Model (Shared Table + Type-Specific Tables)

**Decision:** Use a shared `financial_records` parent table for common fields, with separate child tables (`invoice_details`, `receipt_details`, `purchase_order_details`, `expense_report_details`) for type-specific fields. A separate `categories` table manages spending categories.

**Alternatives considered:**
- Single polymorphic table with a `record_type` column and JSONB for type-specific fields
- Completely separate tables per document type (no shared structure)
- MongoDB flexible schema

**Reasoning:** Financial data is fundamentally relational — a record has line items, queries involve date ranges, amount comparisons, vendor grouping, and aggregations. PostgreSQL handles all of these natively. The parent-child model gives us:
- **Unified queries** — listing all records, cross-type analytics, and natural language search work against one table with one set of indexes
- **Type safety** — each child table has properly typed columns (not JSON blobs), so PostgreSQL enforces constraints and enables efficient queries on type-specific fields
- **Clean joins** — a record detail view joins exactly one child table based on `record_type`, no conditional logic needed
- **Shared line items** — the `line_items` table FK's to the parent, so all document types can have line items (invoices and POs commonly do, receipts and expense reports optionally do)

The polymorphic single-table approach (JSONB for type-specific fields) would be simpler upfront but loses query performance and type safety. Separate tables with no shared parent would make unified listing and analytics painful — every query becomes a UNION ALL across four tables. SQLite doesn't support concurrent writes well in containerized deployments.

---

## 6. Dual-Persona Categories (Business + Personal)

**Decision:** Ship with two predefined category groups — **Business** (Office Supplies, Travel, Software & SaaS, Professional Services, Utilities, Marketing, Equipment, Insurance, Shipping & Logistics) and **Personal** (Groceries, Dining & Food, Healthcare, Transportation, Subscriptions, Rent & Housing, Entertainment, Clothing, Education) — with support for user-created custom categories.

**Alternatives considered:**
- Business-only categories (targeting enterprise/finance teams)
- Flat universal category list (no business/personal grouping)
- Let users build their own categories from scratch (no defaults)
- Hierarchical multi-level category tree (e.g., Expenses > Travel > Flights)

**Reasoning:** A financial records tool that only serves businesses misses a huge user segment — individuals tracking personal expenses, freelancers managing both business and personal finance, and small business owners whose company *is* their personal finances. Dual-persona categories acknowledge this reality without adding complexity:
- Categories are flat (not hierarchical) — a category tree adds UI complexity without proportional user value
- Predefined categories mean the AI can assign them immediately on extraction — no cold-start problem
- Custom categories ensure power users aren't constrained by our defaults
- Categories are session-scoped — each user's custom categories are theirs alone

**Product signal:** An enterprise-only tool and a consumer-only tool are both limited. FinanceIQ serves both with one elegant system.

---

## 7. Category-First UI Over Document-Type-First

**Decision:** The Records list page is organized **by category** (what the money was spent on) as the primary dimension, with document type as a secondary filter.

**Alternatives considered:**
- Document-type-first (separate tabs for Invoices, Receipts, POs, Expense Reports)
- Flat list with no primary grouping
- Dashboard-first (category cards with drill-down)

**Reasoning:** When a finance team or an individual looks at their records, the question they're asking is "how much did I spend on software?" or "show me all my healthcare expenses" — not "show me all my receipts." The document type (invoice vs. receipt) is metadata about the *format* the record came in; the category is metadata about the *purpose* of the spend.

The UI reflects this: each record row shows a **color-coded category badge** prominently, with a smaller document type icon as secondary information. Filter controls put category filters first, type filters second. This is a deliberate product opinion — we're designing for how people think about their finances, not how the system stores documents.

---

## 8. Adaptive Side-by-Side Review UI

**Decision:** Invest in a side-by-side document review interface where users see the original document next to extracted data. The right-panel form **dynamically adapts** based on the detected document type.

**Alternatives considered:**
- Separate review pages per document type (`/invoices/[id]`, `/receipts/[id]`, etc.)
- Wizard-style review (step through type → category → fields → save)
- Simple form dump with no document preview

**Reasoning:** Most document extraction tools dump extracted data in a form and hope it's right. The review UI is what turns this from a "cool demo" into a "product I'd actually use." It's genuinely hard: rendering PDFs in-browser, syncing scroll position, inline editing of a complex form with nested line items, and highlighting uncertain fields.

The adaptive approach means one URL pattern (`/records/[id]`), one component tree, and shared editing logic — with type-specific sections that show/hide based on `record_type`:
- **Invoice:** Full form with vendor, dates, payment terms, financial breakdown, and line items table
- **Receipt:** Simplified form with merchant, date, payment method, totals, and optional items
- **Purchase Order:** PO-specific fields including delivery date, approver, PO status (draft → approved → fulfilled), shipping details, and line items
- **Expense Report:** Employee info, department, purpose, period dates, and reimbursement amount

This demonstrates product thinking (users need to verify), UX skill (the interaction design), and engineering depth (the implementation) — across four different document schemas.

---

## 9. No Authentication (Session-Based Isolation)

**Decision:** Use browser session IDs for user isolation instead of implementing authentication.

**Alternatives considered:**
- Email/password auth
- Magic link / passwordless auth
- OAuth (Google sign-in)

**Reasoning:** Session-based isolation prioritizes streamlined access, allowing users to start testing immediately without friction. Each browser session gets its own data space. This avoids the overhead of managing user accounts, password hashing, JWT tokens, and protected routes while still providing data separation.

---

## 10. Next.js + FastAPI (Two-Service Architecture)

**Decision:** Separate frontend (Next.js) and backend (FastAPI/Python) services.

**Alternatives considered:**
- Next.js full-stack (API routes + frontend in one)
- React SPA + FastAPI

**Reasoning:** Document processing in Python is vastly superior to Node.js — libraries like the Google Gemini SDK are Python-first. Next.js gives us SSR, excellent routing, and a mature React ecosystem. The two-service architecture adds Docker Compose complexity but gives each service the best tool for its job.

---

## 11. Tailwind CSS + shadcn/ui for Styling

**Decision:** Use Tailwind CSS with shadcn/ui components for the frontend.

**Alternatives considered:**
- Vanilla CSS (maximum control, more time-consuming)
- Material UI (popular but opinionated)
- Chakra UI (good DX, fewer components)

**Reasoning:** Tailwind + shadcn/ui dramatically accelerates UI development while producing a polished, professional result. shadcn/ui components are copy-pasted into the project (not a dependency), giving us full control. The dark mode aesthetic with vibrant accents maps perfectly to Tailwind's utility classes.

---

## 12. Render for Deployment

**Decision:** Deploy on Render with Docker support and managed PostgreSQL.

**Alternatives considered:**
- Railway (similar features, slightly simpler)
- Vercel + Railway (best-in-class for each service, but two platforms)
- AWS ECS (maximum control, overkill complexity)
- Fly.io (global edge, more complex setup)

**Reasoning:** Render supports Docker builds (essential for our system dependencies), offers managed PostgreSQL, has a usable free tier, and deploys directly from GitHub. It's a single platform for both services, reducing operational complexity.

---

## 13. Test-Driven Development

**Decision:** Write tests *before* implementation for each component.

**Alternatives considered:**
- Write tests after implementation (faster initially, riskier)
- Skip unit tests and rely on manual QA
- Only write integration tests, skip unit tests

**Reasoning:** FinanceIQ touches every layer of the stack — models, extraction, APIs, and UI. Without tests, a change to the extraction prompt could silently break category assignment, or a schema change could miss a foreign key. TDD ensures:
- Each component's expected behavior is documented before code is written
- Regressions from cross-cutting changes are caught immediately
- Classification, categorization, and multi-type extraction each have dedicated test coverage

**Test structure:** Unit tests for data utilities (safe_decimal, safe_date, enum validation), API tests for endpoints (`/api/records`, `/api/categories`), extraction tests for each document type's save logic, and prompt formatting tests for the unified prompt.

---

## 14. Financial Auditor Pipeline and Anomaly Resolution

**Decision:** Intercept LLM data extraction with a deterministic `AuditorService` that verifies math and temporal constraints before saving, highlighting cell-level anomalies in the UI rather than relying solely on the LLM's own self-assessed "confidence score".

**Alternatives considered:**
- Prompting the LLM to "double-check its math" (often fails)
- Failing the extraction entirely if math doesn't align
- Generic document-level warning flag ("Please review")

**Reasoning:** LLMs hallucinate numbers and fail at math. In finance, a silently hallucinated total corrupts downstream accounting. A generic "Please review this document" flag places all the cognitive load on the user to find the error. By writing a deterministic parser that cross-checks the LLM's extraction (e.g., `subtotal + tax == total_amount`), we can pinpoint exactly which cells conflict. We downgrade the confidence of only the conflicting cells and present an "Anomaly Resolution" UI that highlights the exact fields in error, explaining *why* the math doesn't add up.

**What this demonstrates:** This solves a genuinely hard, messy sub-problem of LLM wrappers: strict grounding and mathematical integrity. It shifts the UX from manual proofreading to targeted anomaly resolution.

---

*More decisions will be added as the build progresses.*
