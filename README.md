# FinanceIQ

> Turn messy financial documents into structured, queryable data.

FinanceIQ is a full-stack web application that extracts structured data from various financial documents (Invoices, Receipts, Purchase Orders, Expense Reports) using AI-powered extraction, automatically categorizes them into Business or Personal buckets, and makes them instantly searchable and queryable.

## Features

- **Multi-Document Support** — Handles Invoices, Receipts, Purchase Orders, and Expense Reports
- **Automatic Categorization** — Auto-assigns categories with a dual-persona (Business vs Personal) design
- **Smart Upload** — Drag-and-drop upload with real-time processing status
- **Extraction Pipeline** — LLM vision (Gemini 3.5 Flash Lite)
- **Financial Auditor Pipeline** — Deterministic cross-checks for LLM math and logical constraints
- **Anomaly Resolution UI** — Cell-level precision in flagging AI mistakes
- **Adaptive Review UI** — View original document alongside dynamically generated forms based on document type
- **Natural Language Search** — Query records in plain English ("show me all healthcare expenses from last month")
- **Dashboard Analytics** — Total spend, category breakdowns, record type breakdowns, monthly trends
- **Robust Error Handling** — Graceful degradation for corrupted files, partial extraction recovery

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python 3.12, FastAPI, SQLAlchemy (Async) |
| LLM | Google Gemini 3.5 Flash Lite |
| Document Processing | Gemini 3.5 Flash Lite Vision |
| Database | PostgreSQL 16 |
| Deployment | Render (Docker) |

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A Gemini API key (free — see below)

### 1. Get a Gemini API Key (Free)

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Select a Google Cloud project (or create one — it's free)
5. Copy the generated API key

> **Note:** The free tier includes 1,500 requests/day with Gemini 3.5 Flash Lite, which is more than enough for testing.

### 2. Clone & Configure

```bash
git clone https://github.com/YOUR_USERNAME/unstrut-invoice.git
cd unstrut-invoice

# Create environment file
cp backend/.env.example backend/.env

# Edit backend/.env and add your Gemini API key
# GEMINI_API_KEY=your_key_here
```

### 3. Run with Docker Compose

```bash
# Start all services (PostgreSQL + Backend + Frontend)
docker compose up --build

# The app will be available at:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 4. Run Without Docker (Development)

**Backend:**
```bash
cd backend
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate
# Note for Windows: If you get a script execution disabled error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings

# Start the PostgreSQL database in the background (from the project root directory)
docker compose up -d db

# Run the FastAPI application
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
unstrut-invoice/
├── frontend/              # Next.js 14 app
│   ├── src/app/           # App Router pages
│   ├── src/components/    # React components
│   └── src/lib/           # Utilities & API client
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── models/        # SQLAlchemy models + Pydantic schemas
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic
│   │   │   └── extraction/  # Dual extraction pipeline
│   │   └── utils/         # Prompts, validation
│   └── tests/             # Pytest test suite
├── docker-compose.yml     # Local development orchestration
├── decisions.md           # Design decisions log
└── README.md
```

## Architecture

```
┌──────────────────────────────┐
│      Next.js Frontend        │
│  (Upload, Review, Query,     │
│   Dashboard)                 │
├──────────────────────────────┤
│      FastAPI Backend         │
│ ┌──────────────────────────┐ │
│ │ Extraction & Routing     │ │
│ ├──────────┬───────────────┤ │
│ │ LLM      │ Auditor       │ │
│ │ (Gemini) │ Service       │ │
│ └──────────┴───────────────┘ │
├──────────────────────────────┤
│     PostgreSQL Database      │
└──────────────────────────────┘
```

## Testing

```bash
cd backend
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload document file(s) |
| GET | `/api/records` | List records (filtered, paginated) |
| GET | `/api/records/{id}` | Record detail with type-specific data and line items |
| PUT | `/api/records/{id}` | Update extracted data |
| DELETE | `/api/records/{id}` | Delete a record |
| GET | `/api/records/{id}/file` | Serve original file |
| GET | `/api/categories` | List categories |
| POST | `/api/categories` | Create custom category |
| DELETE | `/api/categories/{id}` | Delete category |
| POST | `/api/query` | Natural language query |
| GET | `/api/analytics` | Dashboard analytics |
| GET | `/api/health` | Health check |

## License

MIT
