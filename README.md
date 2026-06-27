<div align="center">
  <img src="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/brain-circuit.svg" width="80" alt="Luminal AI Logo" />
  <h1>LUMINAL AI</h1>
  <p><strong>RAG &amp; Graph-Based Question-Answering System</strong></p>
  <p>FastAPI · LangChain · FAISS · Neo4j · PostgreSQL · React</p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python Version" />
    <img src="https://img.shields.io/badge/FastAPI-0.100%2B-green" alt="FastAPI Version" />
    <img src="https://img.shields.io/badge/Neo4j-5.0%2B-blue" alt="Neo4j Version" />
    <img src="https://img.shields.io/badge/PostgreSQL-15%2B-blue" alt="PostgreSQL Version" />
    <img src="https://img.shields.io/badge/LangChain-0.1%2B-orange" alt="LangChain Version" />
  </p>
</div>

---

## Overview

Luminal AI is a Python backend that lets you ingest text documents and then ask natural-language questions against them. It combines:

- **FAISS vector search** – documents are chunked, embedded with OpenAI's `text-embedding-3-large`, and stored in an in-memory FAISS index for similarity search.
- **Neo4j graph storage** – if the caller supplies explicit entity relationships at ingest time, those are merged into a Neo4j graph and later used to augment the answer context.
- **LLM generation** – GPT-4o classifies the query intent; GPT-4-turbo generates a streamed answer using the retrieved context.
- **Interaction logging** – every query/response pair is stored in PostgreSQL.
- **Gap detection** – a separate endpoint accepts the last *n* interactions and calls GPT-4 to generate a targeted follow-up question about the topic.

A React/TypeScript frontend (Vite) is included and served as a separate Docker container.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Client (React / Vite)  ──►  FastAPI backend (:8000)            │
│                                                                  │
│  POST /api/v1/ingest                                             │
│    └─► AsyncIngestionQueue (asyncio, 3 workers)                  │
│         ├─► RecursiveCharacterTextSplitter → chunks              │
│         ├─► FAISS in-memory index (OpenAI embeddings)            │
│         └─► Neo4j batch merge  (only if relations supplied)      │
│                                                                  │
│  POST /api/v1/query/stream                                       │
│    └─► SemanticRouter (GPT-4o) → FACTUAL_RETRIEVAL |             │
│                                   RELATIONAL_SYNTHESIS |         │
│                                   GENERAL_CHAT                   │
│         ├─► FAISS similarity search  (k=5)                       │
│         │    + keyword re-rank (term-overlap score)              │
│         ├─► Neo4j subgraph query  (depth=2, if concept given)    │
│         └─► GPT-4-turbo streamed response (SSE)                  │
│              └─► PostgreSQL interaction_logs                      │
│                                                                  │
│  POST /api/v1/evaluate                                           │
│    └─► GPT-4 Socratic question from last 3 interactions          │
└─────────────────────────────────────────────────────────────────┘

Infrastructure (docker-compose):
  postgres:15  ·  neo4j:5  ·  redis:alpine  ·  backend  ·  frontend
```

---

## Core Components

### 1. Ingestion Pipeline — [`src/services/ingestion.py`](src/services/ingestion.py)

- Uses `asyncio.Queue` (max 100 items) and 3 background worker tasks.
- Splits text with LangChain's `RecursiveCharacterTextSplitter` (chunk size 1 200 chars, overlap 250).
- Embeds chunks and adds them to an **in-memory FAISS index** via `AsyncVectorStoreManager`. The index is not persisted to disk — it is lost on restart.
- Entity extraction is **regex-based**: capitalised multi-word phrases (e.g., `[A-Z][a-z]+ ...`) are treated as candidate entities. No NLP NER model is used.
- Relationships (edges in Neo4j) are only created when the caller explicitly provides a `relations` list in the request body. They are not inferred from text automatically.

### 2. Vector Store — [`src/db/vector_store.py`](src/db/vector_store.py)

- Wraps LangChain's `FAISS` with async helpers.
- `async_hybrid_search` fetches `2k` dense neighbours, then re-ranks by plain keyword term-overlap, and returns the top `k`. It is **not** a true sparse+dense hybrid (no BM25 or Pinecone sparse index).
- Pinecone credentials are present in the config but **no Pinecone code path is implemented**.

### 3. RAG Agent — [`src/services/rag.py`](src/services/rag.py)

- `SemanticRouter` sends the query to GPT-4o with a few-shot prompt to get one of three intent labels.
- `AsyncHybridRAGAgent._gather_context` fans out FAISS search and (optionally) a Neo4j Cypher subgraph query concurrently via `asyncio.gather`.
- Streams the GPT-4-turbo response as Server-Sent Events. The intent label and retrieved context are injected into the system prompt.

### 4. Neo4j Client — [`src/db/neo4j_client.py`](src/db/neo4j_client.py)

- Async driver with a connection pool (max 50 connections).
- `extract_subgraph` traverses up to depth 2 from a named `Concept` node and returns nodes + edges (max 50 nodes).
- `batch_merge_entities` uses `MERGE` for nodes and `apoc.create.relationship` for edges inside a single transaction — **requires APOC plugin** to be installed in Neo4j.

### 5. Evaluation — [`src/services/evaluation.py`](src/services/evaluation.py)

- Accepts an `interaction_history` list and a `current_topic` string.
- Formats the **last 3** entries from the history into a prompt and asks GPT-4 to generate one Socratic follow-up question.
- Does not query PostgreSQL; the caller is responsible for supplying the history.

### 6. FastAPI Backend — [`src/main.py`](src/main.py) · [`src/api/routes.py`](src/api/routes.py)

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Liveness check |
| `/api/v1/ingest` | `POST` | Queue a document for background processing |
| `/api/v1/query/stream` | `POST` | Stream an LLM answer (SSE) |
| `/api/v1/evaluate` | `POST` | Generate a targeted follow-up question |

- Per-request logging middleware attaches a UUID and measures latency in milliseconds.
- `InteractionLog` rows are written to PostgreSQL after each streamed response. The `intent` field is currently hardcoded to `"unknown"` in the route handler.

### 7. Frontend — [`frontend/`](frontend/)

- Vite + React + TypeScript project with Tailwind CSS.
- Runs on port 3000 inside Docker and proxies API calls to the backend container.

---

## Quickstart

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for local development without Docker)
- OpenAI API key
- Neo4j with the **APOC** plugin enabled (required for relationship creation)

### Environment Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/luminal-ai.git
cd luminal-ai

# 2. Create and activate a virtual environment
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux / macOS
source ./venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env — required keys:
#   OPENAI_API_KEY
#   NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD
#   POSTGRES_URL
```

### Running with Docker Compose

```bash
# Start all services (postgres, neo4j, redis, backend, frontend)
docker-compose up -d
```

- Backend API: http://localhost:8000
- Frontend UI: http://localhost:3000
- Neo4j Browser: http://localhost:7474

### Running the Backend Locally

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Known Limitations

| Area | Limitation |
|---|---|
| FAISS index | In-memory only — all embeddings are lost on restart. Add `index.faiss` save/load calls to persist data. |
| Pinecone | Configuration keys are present but Pinecone is not used in any code path. |
| Entity extraction | Regex-based (capitalised phrases). Not an NLP model — noisy for general text. |
| Graph relations | Only created when explicitly provided by the caller. No automatic relation extraction from text. |
| Intent logging | The `intent` column in PostgreSQL is always stored as `"unknown"` (see `routes.py` line 52). |
| Evaluation history | The gap-detection endpoint uses only the last 3 messages passed in the request; it does not query the database. |
| APOC dependency | `batch_merge_entities` calls `apoc.create.relationship`, which requires the APOC plugin. Without it, relationship creation will fail. |
| Redis / Celery | Both are declared as dependencies and listed in `requirements.txt` but are not used in the application code. |

---

## Project Structure

```
luminal-ai/
├── docker-compose.yaml
├── requirements.txt
├── frontend/               # Vite + React + TypeScript UI
└── src/
    ├── main.py             # FastAPI app, middleware, lifespan
    ├── api/
    │   └── routes.py       # API endpoints
    ├── core/
    │   ├── config.py       # Pydantic settings
    │   ├── exceptions.py   # Custom exception classes
    │   ├── llm.py
    │   └── logger.py       # Structlog configuration
    ├── db/
    │   ├── neo4j_client.py # Async Neo4j driver wrapper
    │   ├── postgres.py     # SQLAlchemy models & session
    │   └── vector_store.py # FAISS + OpenAI embeddings wrapper
    └── services/
        ├── evaluation.py   # GPT-4 Socratic question generation
        ├── ingestion.py    # Async queue + chunking + indexing
        └── rag.py          # Intent router + context gathering + LLM streaming
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `fastapi` + `uvicorn` | Async HTTP server |
| `langchain` + `langchain-openai` + `langchain-community` | LLM chains, FAISS wrapper, text splitter |
| `openai` | OpenAI API client |
| `faiss-cpu` | In-memory vector index |
| `neo4j` | Async graph database driver |
| `sqlalchemy` + `psycopg2-binary` | PostgreSQL ORM |
| `pydantic` + `pydantic-settings` | Request validation & configuration |
| `structlog` | Structured JSON logging |
| `tiktoken` | Token counting for chunking |
| `redis` + `celery` | Declared but currently unused |
