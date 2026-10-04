# 🧠 QueryMind — Natural Language Database Interface

QueryMind is an agentic **Text-to-SQL interface** that converts plain-English questions into valid, optimized PostgreSQL queries in real-time. Built with a self-correcting execution pipeline, dynamic database schema introspection, and read-only safety guardrails.

---

## ✨ Features

- **🔍 Dynamic Schema Introspection**: Extracts live table definitions, primary keys, and foreign-key constraints from PostgreSQL without requiring hardcoded schema files.
- **🛡️ SQL Safety Guardrails**: AST-based validator that blocks destructive operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, etc.) and permits only read-only `SELECT` / `WITH` statements.
- **🔄 Self-Correcting Pipeline**: If a generated query encounters a syntax or runtime error, the engine feeds the PostgreSQL error trace back to the LLM to automatically self-correct.
- **🤖 Multi-Provider LLM Support**: Works with local offline LLMs (**Ollama / Qwen 2.5 Coder**) as well as **OpenAI** (`gpt-4o`) and **Google Gemini**.
- **💻 Modern React UI**: Dark-mode interface with live schema explorer, query chips, SQL syntax highlighting, tabular results view, and performance metrics.
- **📊 Automated Benchmark Suite**: Evaluation runner testing multi-table joins, aggregations, filters, and relationship queries with 100% accuracy.

---

## 🏗️ Architecture

```mermaid
flowchart LR
    User[Natural Language Question] --> UI[React + Vite Frontend]
    UI -->|POST /api/query| API[FastAPI Backend]
    API --> Pipeline[Self-Correction Pipeline]
    Pipeline --> Schema[Schema Introspector]
    Schema -->|Live DDL & FKs| LLM[LLM: Qwen / Ollama / OpenAI / Gemini]
    LLM -->|Generated SQL| Safety[SQL Safety Validator]
    Safety -->|Read-Only SELECT| DB[(PostgreSQL Database)]
    DB -->|Results Table| UI
```

---

## 🚀 Getting Started

### 1. Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+** (e.g. PostgreSQL 18)
- **Ollama** with `qwen2.5-coder:14b` (or 1.5b / 7b)

To install the model via Ollama:
```bash
ollama pull qwen2.5-coder:14b
```

---

### 2. Environment Configuration

Copy the example environment file and configure your database credentials:

```bash
cp .env.example .env
```

Edit `.env` (or `backend/.env`):
```env
# Database Connections
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/DBMS_proj
DATABASE_READONLY_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/DBMS_proj

# LLM Provider (ollama | openai | gemini)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:14b

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

---

### 3. Backend Setup & Run

```bash
cd backend

# Create virtual environment & install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### 4. Frontend Setup & Run

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## 🧪 Testing & Evaluation

### Run Unit & Integration Tests
```bash
PYTHONPATH="backend" backend/venv/bin/pytest tests/ -v
```

### Run Live Benchmark Evaluation
```bash
backend/venv/bin/python evaluation/run_eval.py
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Returns backend health, database connectivity, and LLM configuration |
| `GET` | `/api/schema/tables` | Lists all tables, column counts, and primary keys |
| `GET` | `/api/schema/relationships` | Returns all foreign-key relationship mappings |
| `GET` | `/api/schema/tables/{name}` | Returns detailed schema for a specific table |
| `POST` | `/api/query` | Executes natural language to SQL pipeline with `{ "question": "..." }` |

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy 2.0, Pydantic V2, Psycopg2, Sqlparse, Pytest
- **Frontend**: React 19, Vite, Tailwind CSS v4, Lucide Icons, PrismJS, Axios
- **LLM / AI**: Ollama SDK (`qwen2.5-coder:14b`), OpenAI SDK, Google GenAI SDK
- **Database**: PostgreSQL
