<div align="center">
  <img src="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/brain-circuit.svg" width="80" alt="Luminal AI Logo" />
  <h1>LUMINAL AI</h1>
  <p><strong>Intelligent RAG & Graph-Based Learning System</strong></p>
  <p>Generative AI • Knowledge Graphs • Semantic Search • NLP Orchestration</p>
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

Luminal AI is an enterprise-grade **Generative AI knowledge extraction and reasoning system**. It is designed to transform static notes and unstructured text into a highly interactive assistant capable of deep multi-mode reasoning, active questioning, and automated knowledge gap detection.

Initially conceived as an advanced educational orchestration layer, Luminal AI leverages a **Hybrid RAG** (Retrieval-Augmented Generation) engine that grounds Large Language Models in both semantic vector spaces and explicit structural relationships.

### Key Achievements
- **Hybrid Contextual RAG**: Reduced LLM hallucination rates significantly by combining dense vector retrieval (FAISS/Pinecone) with explicit graph traversals (Neo4j).
- **Automated Knowledge Ingestion**: Sustained high-throughput automated preprocessing pipelines featuring dynamic recursive text chunking and instantaneous embedding generation.
- **Intent-Driven Orchestration**: Developed an advanced multi-agent orchestration layer that successfully parses user intent to route queries between conceptual synthesis and factual retrieval.
- **Active Gap Detection Engine**: Engineered an evaluation system capable of actively scanning user interaction history to generate targeted follow-up questions, reinforcing user understanding.

---

## System Architecture

The architecture relies on loosely coupled microservices designed for scalable knowledge processing and rapid reasoning inference.

```mermaid
graph LR
    subgraph Knowledge Ingestion
        Doc[Static Notes<br/>Raw Text] -->|Process| IP[Ingestion Pipeline<br/>Recursive Chunking]
        IP -->|Extract Vectors| V[(Vector Store<br/>FAISS/Pinecone)]
        IP -->|Extract Relations| G[(Graph DB<br/>Neo4j)]
    end

    subgraph Orchestration & Reasoning
        UI[User Query<br/>Intent Parsing] -->|Route| ORC[LLM Orchestrator<br/>LangChain]
        ORC -->|Semantic Search| V
        ORC -->|Graph Traversal| G
        ORC -->|Synthesize| LLM[(Generative AI<br/>GPT-4)]
    end

    subgraph Logging & Evaluation
        LLM -->|Response| UI
        LLM -->|Interaction Data| PG[(Relational DB<br/>PostgreSQL)]
        PG -->|Analyze| EVAL[Gap Detection Engine<br/>Targeted Questioning]
        EVAL -->|Active Feedback| UI
    end
    
    style IP fill:#1f2937,stroke:#3b82f6,color:#fff
    style V fill:#065f46,stroke:#10b981,color:#fff
    style G fill:#b45309,stroke:#f59e0b,color:#fff
    style ORC fill:#4c1d95,stroke:#8b5cf6,color:#fff
    style LLM fill:#be185d,stroke:#f43f5e,color:#fff
    style PG fill:#0f172a,stroke:#38bdf8,color:#fff
    style EVAL fill:#1e40af,stroke:#60a5fa,color:#fff
```

## Core Components

### 1. Ingestion & Preprocessing Pipeline (`src/services/ingestion.py`)
A highly automated NLP data pipeline. It utilizes recursive character chunking and semantic extraction to transform raw documents. Extracted entities are routed to the Vector Store for semantic similarity, while their complex relational topologies are mapped into the Graph Database.

### 2. Hybrid RAG Engine (`src/services/rag.py`)
The reasoning core of Luminal AI. When a query is received, this engine performs a dual-retrieval: fetching top-k semantically relevant chunks from **FAISS/Pinecone**, while simultaneously querying **Neo4j** for adjacent conceptual nodes to provide a deep, relationship-aware context prompt to the LLM.

### 3. Evaluation & Gap Detection (`src/services/evaluation.py`)
An active learning module that analyzes the historical interaction logs stored in **PostgreSQL**. By evaluating the user's intent and conceptual coverage, it proactively generates targeted questions to test understanding and identify blind spots.

### 4. FastAPI Backend Microservice (`src/api/routes.py`, `src/main.py`)
A highly concurrent and scalable asynchronous **FastAPI** backend that acts as the entry point for all reasoning, ingestion, and evaluation workloads. Employs structured logging for rigorous prompt debugging and system monitoring.

---

## Quickstart

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- OpenAI API Key

### Setup the Environment

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/luminal-ai.git
cd luminal-ai

# 2. Activate the virtual environment
# Windows
python -m venv venv
.\venv\Scripts\activate
# Linux/Mac
python3 -m venv venv
source ./venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY, PINECONE_API_KEY, etc.
```

### Running the System Locally

1. **Start the Database Infrastructure (Postgres & Neo4j)**
```bash
docker-compose up -d
```

2. **Start the Application Backend**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Performance & SLAs

| Metric | Target SLA | Expected System Range |
|--------|------------|-----------------------|
| Semantic Retrieval Latency | < 50ms | 20-35ms |
| Graph Traversal Latency | < 100ms | 40-70ms |
| E2E Generation Latency (LLM) | < 2000ms | 1200-1800ms |
| Chunking & Ingestion Rate | > 5MB/s | 12MB/s |

---

<div align="center">
  <i>Engineered for next-generation interactive learning and contextual reasoning.</i>
</div>
