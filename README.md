# E-commerce AI Operations Agent

An AI-powered operations platform for e-commerce businesses. A multi-agent LLM
pipeline (demand, inventory, and pricing agents synthesized by an executive
agent) analyzes live sales, inventory, and customer data to generate
actionable recommendations — with full reasoning shown and a human-in-the-loop
approval workflow — alongside a full operations dashboard for managing
products, customers, orders, and inventory.

![Dashboard](docs/screenshots/dashboard.png)

## Features

- **AI Recommendations** — a Groq-backed multi-agent workflow (demand →
  inventory → pricing → executive synthesis) produces pricing/inventory
  recommendations with a transparent reasoning breakdown per decision, plus a
  confidence score and approve/reject workflow
- **Operations Dashboard** — real-time sales, inventory, and product metrics
- **Products** — search, low-stock filtering, full CRUD
- **Customers** — segmentation breakdown, lifetime-value ranking, order history
- **Orders** — status workflow (ship / refund / cancel), line-item detail
- **Inventory** — low-stock alerts, one-click reorder, manual adjustment
- **Analytics** — revenue, product performance, and customer segment charts
- **Auth** — JWT-based single-admin authentication

| | | |
|---|---|---|
| ![Analytics](docs/screenshots/analytics.png) | ![Recommendations](docs/screenshots/recommendations.png) | ![Products](docs/screenshots/products.png) |

## Tech Stack

**Backend** — FastAPI · SQLAlchemy · PostgreSQL (Neon) · Groq (Llama 3.3) ·
LangGraph-style agent workflow · ChromaDB · PyJWT

**Frontend** — Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS ·
Recharts · Axios

## Project Structure

```
.
├── backend/
│   ├── app.py                  # FastAPI app, metrics & workflow endpoints
│   ├── config.py                # Settings (env-driven)
│   ├── agents/                  # Agent tool definitions
│   ├── database/                # SQLAlchemy models & session
│   ├── llm/                     # Groq client & prompts
│   ├── memory/                  # ChromaDB vector store
│   ├── routers/                 # auth, products, customers, orders,
│   │                             #   inventory, analytics, ai_ops
│   ├── scheduler/                # Scheduled workflow tasks
│   ├── services/                 # Business logic per domain
│   ├── workflows/                # Multi-agent orchestration
│   └── scripts/load_kaggle_data.py  # Sample data loader
│
└── frontend/
    └── src/
        ├── app/
        │   ├── login/            # Login page
        │   └── dashboard/         # Protected app shell + 8 pages
        │       ├── products/ customers/ orders/ inventory/
        │       └── analytics/ recommendations/ settings/
        ├── components/
        │   ├── ui/                # Button, Modal, Badge, StatCard, ...
        │   └── layout/Sidebar.tsx
        ├── context/AuthContext.tsx
        ├── lib/                   # api.ts (API client), format.ts
        └── types/                 # Shared TypeScript types
```

## Prerequisites

- Python 3.12+
- Node.js 18+ and npm
- A PostgreSQL database (e.g. a free [Neon](https://console.neon.tech) instance)
- A [Groq API key](https://console.groq.com) for the LLM agents

## Setup

### 1. Backend

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r backend/requirements.txt

cp .env.example backend/.env    # then fill in DATABASE_URL, GROQ_API_KEY, etc.
```

Run it:

```bash
python -m uvicorn backend.app:app --reload --port 8001
```

The API is now live at `http://localhost:8001` (interactive docs at `/docs`).
On first startup it creates all tables automatically.

### 2. Frontend

```bash
cd frontend
npm install
```

`frontend/.env.local` should point at the backend:

```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

Run it:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and log in with the
`ADMIN_EMAIL` / `ADMIN_PASSWORD` configured in `backend/.env`.

## Sample Data

To populate the database with sample products, customers, orders, and
inventory (from a Kaggle e-commerce dataset), see
`backend/scripts/load_kaggle_data.py`.

## API Overview

All endpoints (other than `/health`, `/info`, and `/api/auth/login`) require a
`Bearer` token obtained from `POST /api/auth/login`.

| Area | Base path |
|---|---|
| Auth | `POST /api/auth/login` |
| Metrics & Workflow | `GET /api/metrics`, `POST /api/workflow/trigger` |
| Recommendations | `GET /api/recommendations`, `POST /api/approve/{id}`, `POST /api/reject/{id}` |
| Products | `/api/products` (CRUD, `/search`, `/category`, `/low-stock`, `/import`) |
| Customers | `/api/customers` (CRUD, `/segments`, `/lifetime`, `/{id}/orders`) |
| Orders | `/api/orders` (CRUD, `/{id}/items`, `/{id}/ship`, `/{id}/refund`) |
| Inventory | `/api/inventory` (CRUD, `/low-stock`, `/reorder`, `/transfer`) |
| Analytics | `/api/analytics/revenue`, `/products`, `/customers`, `/forecast` |
| AI Ops | `/api/ai/forecast`, `/optimize-inventory`, `/optimize-pricing`, `/performance` |

Full request/response models are visible in the auto-generated Swagger UI at
`http://localhost:8001/docs` once the backend is running.

## Development

```bash
# Type-check, lint, and build the frontend
cd frontend
npm run type-check
npm run lint
npm run build
```
