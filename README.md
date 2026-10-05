# Use Case 2 — Intelligent Support Ticket Resolution Assistant

A production-oriented semantic resolution assistant for telecom customer support teams.

The system helps support agents resolve customer complaints by combining structured complaint analysis, semantic retrieval, PostgreSQL full-text search, hybrid ranking, authoritative knowledge-base evidence, grounded LLM-generated resolutions, safety validation, evaluation, and operational monitoring.

---

## Table of Contents

- [1. Problem Background](#1-problem-background)
- [2. Solution](#2-solution)
- [3. Architecture](#3-architecture)
- [4. Technology Stack](#4-technology-stack)
- [5. End-to-End Resolution Flow](#5-end-to-end-resolution-flow)
- [6. Complaint Intelligence](#6-complaint-intelligence)
- [7. Semantic Retrieval](#7-semantic-retrieval)
- [8. PostgreSQL Full-Text Search](#8-postgresql-full-text-search)
- [9. Hybrid Retrieval](#9-hybrid-retrieval)
- [10. Retrieval Evaluation](#10-retrieval-evaluation)
- [11. Evidence Policy](#11-evidence-policy)
- [12. Grounded Resolution Generation](#12-grounded-resolution-generation)
- [13. Grounding Validation and Safety](#13-grounding-validation-and-safety)
- [14. Handling Evolving Ticket Classes](#14-handling-evolving-ticket-classes)
- [15. Data Pipeline](#15-data-pipeline)
- [16. Database Design](#16-database-design)
- [17. Performance Optimization](#17-performance-optimization)
- [18. End-to-End Performance](#18-end-to-end-performance)
- [19. Monitoring and System Health](#19-monitoring-and-system-health)
- [20. Failure and Rate-Limit Handling](#20-failure-and-rate-limit-handling)
- [21. API](#21-api)
- [22. Frontend](#22-frontend)
- [23. Screenshots](#23-screenshots)
- [24. Production-Scale Considerations](#24-production-scale-considerations)
- [25. Security and Privacy](#25-security-and-privacy)
- [26. Testing](#26-testing)
- [27. Repository Structure](#27-repository-structure)
- [28. Documentation](#28-documentation)
- [29. Prerequisites](#29-prerequisites)
- [30. Environment Configuration](#30-environment-configuration)
- [31. Running PostgreSQL](#31-running-postgresql)
- [32. Backend Setup](#32-backend-setup)
- [33. Frontend Setup](#33-frontend-setup)
- [34. Running the Full System](#34-running-the-full-system)
- [35. Database Migrations](#35-database-migrations)
- [36. Running Retrieval Evaluation](#36-running-retrieval-evaluation)
- [37. Monitoring](#37-monitoring)
- [38. Development Quality Checks](#38-development-quality-checks)
- [39. Current Measured System Results](#39-current-measured-system-results)
- [40. Design Decisions](#40-design-decisions)
- [41. Limitations](#41-limitations)
- [42. Future Improvements](#42-future-improvements)
- [43. Project Status](#43-project-status)
- [44. Conclusion](#45-conclusion)
- [License](#license)

---

## 1. Problem Background

Telecom support teams handle large volumes of customer complaints covering connectivity, mobile services, billing, account issues, and outages.

Traditional support workflows often depend on keyword-based searches across historical tickets and knowledge-base documentation. This creates several problems:

- Customers describe the same issue using different terminology.
- Exact keyword matches can miss semantically similar historical cases.
- Historical tickets may contain outdated or inconsistent troubleshooting advice.
- LLM-generated answers can introduce unsupported troubleshooting steps.
- Naive retrieval becomes increasingly expensive as the support dataset grows.
- New products, sub-intents, and ticket classes appear continuously.

**Example complaint:**

> My broadband drops every evening around 8 and I've already restarted the router twice. I work from home and this is costing me.

A keyword search may focus on terms such as `broadband`, `router`, and `restart`. A semantic retrieval system can instead recognize the underlying problem as an **intermittent connectivity issue** even when historical tickets use different wording.

The objective is therefore not simply to build a chatbot, but to build an **evidence-grounded support resolution system** that can:

1. Understand the complaint.
2. Retrieve semantically and lexically relevant evidence.
3. Prioritize authoritative knowledge-base information.
4. Generate an actionable resolution.
5. Validate the generated resolution.
6. Provide citations.
7. Measure retrieval and resolution quality.
8. Monitor system health.

---

## 2. Solution

The system follows an evidence-first resolution workflow:

```
Customer Complaint
       |
       v
Complaint Intelligence
       |
       +--> Intent
       +--> Sub-intent
       +--> Product
       +--> Severity
       +--> Sentiment
       +--> Entities
       |
       v
Query Embedding
       |
       v
Hybrid Retrieval
       |
       +--> Semantic Vector Search
       |
       +--> PostgreSQL Full-Text Search
       |
       v
Reciprocal Rank Fusion
       |
       v
Evidence Policy
       |
       +--> Authoritative Knowledge Base
       |
       +--> Supporting Historical Ticket
       |
       v
LLM Resolution Generation
       |
       v
Grounding Validation
       |
       +--> Grounded Resolution
       |
       +--> Safety Fallback
       |
       v
Resolution + Citations
       |
       v
Resolution Health Logging
```

The architecture separates:

- Complaint understanding
- Query embedding
- Retrieval
- Evidence selection
- Resolution generation
- Grounding validation
- Monitoring

This separation makes individual components independently testable and replaceable.

---

## 3. Architecture

> Architecture diagram: `docs/images/architecture.png`

---

## 4. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| Backend | FastAPI + Python |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Vector Index | HNSW |
| Lexical Search | PostgreSQL Full-Text Search |
| Lexical Index | GIN |
| Hybrid Ranking | Reciprocal Rank Fusion |
| Embeddings | BAAI/bge-large-en-v1.5 |
| LLM | OpenAI-compatible provider / Groq |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Testing | pytest |
| Linting | Ruff |
| Type Checking | mypy |
| Containerization | Docker Compose |
| Documentation | Markdown + Mermaid |

---

## 5. End-to-End Resolution Flow

### Step 1: Complaint Input

The support agent submits the customer's raw complaint.

```
My broadband drops every evening around 8 and I have already restarted
the router twice. I work from home and this is costing me.
```

### Step 2: Complaint Intelligence

The system extracts structured information:

```json
{
  "intent": "Connectivity",
  "sub_intent": "Intermittent broadband drop",
  "product": "Broadband",
  "severity": "HIGH",
  "sentiment": "NEGATIVE",
  "entities": {
    "drop_time": "20:00",
    "device": "router"
  },
  "confidence": 0.94,
  "model_version": "llm-intelligence-v1"
}
```

### Step 3: Query Embedding

The complaint is embedded using `BAAI/bge-large-en-v1.5` (dimension: `1024`).

### Step 4: Hybrid Retrieval

```
Semantic Search  +  PostgreSQL FTS
                 |
                 v
                RRF
```

### Step 5: Evidence Selection

The evidence policy limits context passed to the LLM:

- **Maximum KB results:** 5
- **Maximum historical results:** 1

### Step 6: Resolution Generation

The LLM receives the complaint and selected evidence and produces a structured resolution.

### Step 7: Grounding Validation

Generated troubleshooting steps are checked against retrieved evidence.

### Step 8: Final Response

The system returns:

- Summary
- Diagnosis
- Recommended steps
- Escalation decision
- Confidence
- Citations

### Step 9: Monitoring

The request is logged for operational and quality monitoring.

---

## 6. Complaint Intelligence

The complaint intelligence layer converts unstructured complaints into structured attributes.

**Top-level intent taxonomy:**

- `Connectivity`
- `Mobile`
- `Billing`
- `Account`
- `Outage`
- `Other`

**Severity:**

| Value | |
|---|---|
| `LOW` | |
| `MEDIUM` | |
| `HIGH` | |
| `CRITICAL` | |
| `UNKNOWN` | |

**Sentiment:**

| Value | |
|---|---|
| `POSITIVE` | |
| `NEUTRAL` | |
| `NEGATIVE` | |
| `UNKNOWN` | |

Each complaint also contains: `sub_intent`, `product`, `entities`, `confidence`, `model_version`.

The top-level intent is controlled through an enum while `product` and `sub_intent` remain extensible. This allows the system to support evolving ticket classes without requiring a schema migration for every new category.

---

## 7. Semantic Retrieval

The system uses `BAAI/bge-large-en-v1.5` embeddings.

**Current dataset:**

| Metric | Value |
|---|---|
| Conversation chunks | 229,652 |
| Embedded chunks | 229,652 |
| Missing embeddings | 0 |
| Embedding dimension | 1024 |

Embeddings are stored in PostgreSQL using pgvector with **cosine distance**.

**Production vector index:**

```sql
CREATE INDEX ix_conversation_chunks_embedding_hnsw
ON conversation_chunks
USING hnsw (embedding vector_cosine_ops);
```

The retrieval layer filters historical conversations to **resolved cases** before performing the final vector retrieval. This prevents unresolved or escalated tickets from being treated as proven solutions.

---

## 8. PostgreSQL Full-Text Search

Semantic search is complemented by PostgreSQL Full-Text Search via a GIN index:

```sql
CREATE INDEX ix_conversation_chunks_text_fts_gin
ON conversation_chunks
USING gin (to_tsvector('english', text));
```

FTS is especially useful when exact technical terminology matters: `router`, `WAN`, `APN`, `SIM`, `5G`, `ONT`, `ONU`.

| Retrieval | Strength |
|---|---|
| Semantic | Meaning and paraphrase |
| FTS | Exact terminology and lexical overlap |

---

## 9. Hybrid Retrieval

The system combines semantic and lexical candidates using **Reciprocal Rank Fusion (RRF)**:

```
Semantic Search -----> Semantic Rank ---+
                                        |
                                        v
                                   RRF Ranking
                                        ^
                                        |
PostgreSQL FTS -----> FTS Rank ---------+
```

RRF combines relative rankings rather than requiring scores to be calibrated to the same numerical range, producing a robust hybrid retrieval layer.

---

## 10. Retrieval Evaluation

A manually curated golden retrieval set of **30 evaluation queries** was created.

**Metrics measured:**

- Recall@5
- Recall@10
- MRR
- nDCG@10

### Results

| Method | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---|---|---|---|
| Semantic | 0.3000 | 0.3000 | 0.2944 | 0.2663 |
| FTS | 0.0500 | 0.0833 | 0.0250 | 0.0373 |
| **Hybrid RRF** | **0.3333** | **0.3500** | 0.2844 | **0.2740** |

Hybrid retrieval provides the strongest overall retrieval coverage. Semantic retrieval has slightly higher MRR, while hybrid retrieval performs best on Recall@5, Recall@10, and nDCG@10.

### Retrieval Improvement Over Baseline

| Metric | Baseline | Current | Improvement |
|---|---|---|---|
| Recall@5 | 0.1500 | 0.3000 | ~2× |
| Recall@10 | 0.1833 | 0.3000 | ~1.64× |
| MRR | 0.1031 | 0.2944 | ~2.86× |
| nDCG@10 | 0.1203 | 0.2663 | ~2.22× |

The improvement came primarily from restricting resolution retrieval to **resolved conversations**.

Golden data is stored in: `data/evaluation/golden_retrieval.json`

---

## 11. Evidence Policy

Retrieved results are not directly passed to the LLM. The evidence policy separates sources into:

```
Authoritative Knowledge Base
            +
Supporting Historical Ticket
```

**Current limits:**

| Source | Maximum |
|---|---|
| KB results | 5 |
| Historical results | 1 |

The knowledge base is treated as the **authoritative source of truth**. Historical tickets are supporting context only. This prevents outdated historical troubleshooting instructions from overriding current official guidance.

---

## 12. Grounded Resolution Generation

The resolution service constructs a structured prompt containing:

- Customer complaint
- Complaint intelligence
- Selected KB evidence
- Supporting historical evidence
- Resolution instructions
- Output schema requirements

The LLM is instructed to:

- Treat the KB as authoritative.
- Treat historical tickets as supporting evidence only.
- Prefer explicit KB troubleshooting procedures.
- Avoid unsupported troubleshooting steps.
- Cite evidence.
- Escalate when evidence requires escalation.
- Avoid secrets and sensitive information.
- Return structured JSON.
- Request further investigation when evidence is insufficient.

**Expected response structure:**

```json
{
  "summary": "Customer reports recurring broadband disconnects.",
  "diagnosis": "Intermittent broadband connection issue.",
  "recommended_steps": [
    "Confirm whether the outage affects multiple devices.",
    "Check the router WAN indicator during the outage.",
    "Test the connection using Ethernet."
  ],
  "escalation_required": false,
  "confidence": 0.9,
  "citations": [
    {
      "source_id": "KB-CONN-001",
      "section": "1. Intermittent Broadband Connection"
    }
  ]
}
```

---

## 13. Grounding Validation and Safety

Generated troubleshooting steps are validated after LLM generation:

```
LLM Response
     |
     v
Grounding Validation
     |
     +---- Supported ----> Return Response
     |
     +---- Unsupported --> Safety Fallback
```

If unsupported steps are detected:

- The generated resolution is not blindly trusted.
- Unsupported actions are rejected.
- The system produces a safer fallback.
- Escalation is enabled.
- Confidence is reduced.

The system therefore treats the LLM as a **generation layer** rather than the ultimate source of truth.

**Example — representative broadband complaint:**

| Field | Value |
|---|---|
| Grounded | `true` |
| Unsupported steps | `[]` |
| Authoritative evidence | 5 sources |

The final resolution included: `KB-CONN-001`, Section: `1. Intermittent Broadband Connection`.

---

## 14. Handling Evolving Ticket Classes

Telecom support data changes continuously. New products, services, sub-intents, failure modes, and customer terminology can appear over time.

The schema intentionally uses:

```
Controlled Intent
       +
Extensible Sub-intent
       +
Extensible Product
```

For example, a future ticket class could be:

- **Product:** `5G Home Broadband`
- **Sub-intent:** `Intermittent 5G Signal Degradation`

This can be introduced without changing the underlying conversation schema.

**Future taxonomy improvements could include:**

- Taxonomy versioning
- Class discovery and clustering
- Human approval workflows
- Taxonomy drift detection
- Historical class mapping

---

## 15. Data Pipeline

```
Raw Support Dataset
        |
        v
Data Cleaning
        |
        v
Conversation Processing
        |
        v
Chunking
        |
        v
Embedding Generation
        |
        +----------------+
        |                |
        v                v
 Original Text       Vector Embedding
        |                |
        +--------+-------+
                 |
                 v
        PostgreSQL + pgvector
```

**Current searchable corpus:** 229,652 conversation chunks (all chunks have embeddings).

---

## 16. Database Design

**Important entities:**

- `conversations`
- `conversation_chunks`
- `knowledge_base_documents`
- `knowledge_base_chunks`
- `resolution_logs`

**Conversation metadata includes:**

`id`, `external_id`, `product`, `intent`, `sub_intent`, `sentiment`, `severity`, `resolution_status`, `quality_status`, `source_dataset`, `dataset_version`, `created_at`, `updated_at`

**Conversation chunks contain:**

`id`, `conversation_id`, `chunk_index`, `text`, `embedding`, `created_at`

`conversation_chunks.conversation_id` references the parent conversation, allowing the system to maintain relational integrity, conversation-level filtering, vector retrieval, lexical retrieval, and resolution-state filtering.

---

## 17. Performance Optimization

### Embedding Model Preload

The embedding model is loaded during FastAPI startup rather than on first request.

| Before | After | Improvement |
|---|---|---|
| ~11.9 s | ~4.36 s | ~63% reduction |

### HNSW Vector Index

The HNSW index avoids brute-force comparison against every embedding.

**Measured verification query:** ~114 ms

### GIN Full-Text Index

| Query | Before GIN | After GIN |
|---|---|---|
| Broad query | ~138,560 ms | ~38,977 ms |
| `"broadband disconnecting router"` | — | ~1.38 ms |
| `"broadband router"` | — | ~11.5 ms |

### Evidence Limiting

| Source | Limit |
|---|---|
| KB results | 5 maximum |
| Historical results | 1 maximum |

This reduces prompt size, token consumption, conflicting context, and LLM latency.

---

## 18. End-to-End Performance

**Representative warm resolution request:**

| Stage | Latency |
|---|---|
| Complaint intelligence | 1936 ms |
| Query embedding | 267 ms |
| Historical retrieval | 115 ms |
| KB retrieval | 58 ms |
| Evidence retrieval | 441 ms |
| Evidence policy | <1 ms |
| Prompt construction | <1 ms |
| Resolution LLM | 2249 ms |
| Grounding validation | <1 ms |
| Safety fallback | <1 ms |
| **Total** | **~4628 ms** |

The main latency contributors are complaint intelligence and LLM resolution generation. Retrieval itself is comparatively lightweight after indexing and model preload.

---

## 19. Monitoring and System Health

Each resolution request is logged. Tracked fields include:

`complaint`, `intent`, `sub_intent`, `product`, `severity`, `sentiment`, `retrieval_count`, `authoritative_evidence_count`, `grounded`, `unsupported_steps`, `resolution_confidence`, `resolution_summary`, `latency_ms`, `error_type`, `error_message`, `created_at`

**The monitoring script reports:**

- Total / successful / failed requests
- Success rate / failure rate
- Grounding rate
- Average latency, P50, P95
- Average confidence
- Average retrieved / authoritative evidence
- Error types

**Example one-hour monitoring output:**

```
Total requests:              7
Successful requests:         5
Failed requests:             2
Success rate:                71.43%
Failure rate:                28.57%
Grounding rate:              100.00%
Average latency:             5190.68 ms
Median latency (P50):        4628.31 ms
P95 latency:                 10044.47 ms
Average confidence:          0.898
Average retrieved evidence:  7.60
Average authoritative evidence: 5.00
Errors: RuntimeError:        2
```

> The two failures in this sample were provider-rate-limit events generated before dedicated rate-limit handling was implemented.

---

## 20. Failure and Rate-Limit Handling

The LLM provider layer explicitly handles provider throttling:

```
Provider
   |
   v
HTTP 429
   |
   v
Retry-After / retry message parsing
   |
   v
LLMRateLimitError
   |
   v
FastAPI  -->  HTTP 503 + Retry-After
```

**Other failure boundaries:**

| Scenario | Behavior |
|---|---|
| Insufficient evidence | Prefers investigation or escalation over inventing a resolution |
| Unsupported LLM steps | Activates grounding fallback |
| Provider failures | Returns structured server errors |
| Database failures | Surfaced through API layer and captured in resolution logs |

---

## 21. API

### Resolve Endpoint

```
POST /api/v1/resolve
```

**Example request:**

```json
{
  "complaint": "My broadband keeps disconnecting every evening and restarting the router does not fix it."
}
```

**Example PowerShell request:**

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8000/api/v1/resolve" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"complaint":"My broadband keeps disconnecting every evening and restarting the router does not fix it."}'
```

### Health Endpoint

```
GET /api/v1/health
```

**Expected response:**

```json
{
  "status": "ok"
}
```

---

## 22. Frontend

The frontend is implemented using **React + TypeScript + Vite**.

**Support workflow:**

```
Complaint Input
      |
      v
Resolution Request
      |
      v
Complaint Intelligence
      |
      v
Recommended Resolution
      |
      v
Evidence / Citations
```

The frontend communicates with the FastAPI backend.

---

## 23. Screenshots

### Use Case 2 — Intelligent Support Ticket Resolution Assistant

The following screenshots demonstrate the end-to-end support resolution workflow, from submitting a natural-language customer complaint to generating a grounded resolution with evidence and knowledge-base citations.

**Support assistant interface and customer complaint**

![Support assistant interface](docs/images/use-case-2-resolution1.png)

**Complaint intelligence**

![Complaint intelligence](docs/images/use-case-2-resolution2.png)

**Generated resolution, grounding and knowledge sources**

![Generated resolution and evidence](docs/images/use-case-2-resolution3.png)

## 24. Production-Scale Considerations

### Database Scaling

PostgreSQL + pgvector currently provides relational storage, vector search, full-text search, metadata filtering, transactional consistency, and monitoring storage.

For larger deployments, the following can be introduced:

- Connection pooling
- Read replicas
- Partitioning
- Query caching
- Database monitoring
- Backup automation
- Dedicated vector infrastructure

### Retrieval Scaling

At larger scale, retrieval can be separated into a dedicated service with parallel candidate generation:

```
                  +--> Semantic Search
                  |
Query ------------+--> FTS
                  |
                  +--> Metadata Filtering
                  |
                  v
                 RRF
                  |
                  v
        Cross-Encoder Reranker
                  |
                  v
            Top Evidence
```

### LLM Scaling

The LLM provider is abstracted behind a provider interface, making it possible to introduce:

- Provider fallback
- Model routing
- Retries with exponential backoff
- Concurrency limits and request queues
- Token budgets
- Response caching
- Circuit breakers

### API Scaling

The FastAPI service can be horizontally scaled since resolution requests are stateless:

```
Load Balancer
      |
      +---- FastAPI Instance
      +---- FastAPI Instance
      +---- FastAPI Instance
```

---

## 25. Security and Privacy

### Secrets

LLM API keys and database credentials are stored through environment variables. Secrets must **never** be committed to Git. The repository contains `.env.example` rather than actual credentials.

### Database Security

Production deployments should use:

- Least-privilege database users
- Encrypted database connections
- Restricted network access
- Managed credentials
- Regular backups and audit logging

### Customer Data

Production deployments should consider:

- PII detection and redaction
- Data retention policies
- Access control
- Encryption at rest and in transit
- Audit trails

### LLM Security

Production hardening should include:

- Prompt-injection detection
- Strict evidence boundaries
- Output validation
- Sensitive-data filtering
- Model-provider data-retention controls

> The LLM should not be allowed to override system-level evidence policies.

### Authentication and Authorization

Before external deployment, the application should include agent authentication, role-based authorization, organization-level access control, API authentication, and audit logging.

---

## 26. Testing

The repository contains tests covering:

- Configuration
- Health endpoint
- Conversation services
- Retrieval
- Resolution services and pipeline
- API behavior
- LLM provider behavior
- Rate-limit handling
- Integration behavior

**Current results:**

| Scope | Result |
|---|---|
| Backend | 37 passed, 1 warning |
| Repository-wide | 78 passed, 1 warning |

> The warning is related to the current Starlette/httpx TestClient compatibility path and does not represent a failed test.

**Rate-limit test:** Verifies that HTTP `429` is converted into `LLMRateLimitError`, that retry information is parsed correctly, and that the API returns `503 Service Unavailable` with a `Retry-After` header — without making a real LLM request.

---

## 27. Repository Structure

```
telecom-support-resolution/
│
├── .github/
│
├── apps/
│   ├── backend/
│   │   ├── alembic/
│   │   ├── src/
│   │   │   └── app/
│   │   │       ├── api/
│   │   │       ├── db/
│   │   │       ├── services/
│   │   │       ├── config.py
│   │   │       └── main.py
│   │   └── tests/
│   │
│   └── frontend/
│       ├── public/
│       └── src/
│
├── data/
│   └── evaluation/
│       └── golden_retrieval.json
│
├── docs/
│   ├── architecture.md
│   ├── retrieval-evaluation.md
│   ├── production-design.md
│   ├── monitoring.md
│   ├── taxonomy-evolution.md
│   └── images/
│
├── knowledge-base/
│
├── packages/
│   ├── database/
│   └── schemas/
│
├── pipelines/
│   └── ingestion/
│
├── scripts/
│   ├── create_golden_retrieval_set.py
│   ├── evaluate_retrieval.py
│   ├── embedding_export.py
│   └── monitor_resolution_health.py
│
├── tests/
│
├── .env.example
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

## 28. Documentation

The `docs/` directory is reserved for supporting technical documentation,
including:

- Architecture
- Retrieval evaluation
- Production design
- Monitoring
- Taxonomy evolution
- Screenshots and diagrams

---

## 29. Prerequisites

**Required:**

- Python 3.12
- Node.js
- npm
- Docker
- Docker Compose
- Git

**Validated with:**

| Tool | Version |
|---|---|
| Python | 3.12.10 |
| Node.js | 22.19.0 |
| npm | 11.6.1 |
| Docker | 29.7.2 |
| Docker Compose | 5.4.0 |
| Git | 2.45.2 |

> Backend requires: `Python >= 3.12` and `Python < 3.13`

---

## 30. Environment Configuration

Copy the example environment file:

```powershell
Copy-Item .\.env.example .\.env
```

Configure the following variables:

```env
DATABASE_URL=postgresql+psycopg://telecom:telecom_dev_password@localhost:5433/telecom_support

POSTGRES_DB=telecom_support
POSTGRES_USER=telecom
POSTGRES_PASSWORD=telecom_dev_password

LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=<your-api-key>
LLM_MODEL=<your-model>
```

> **Never commit `.env` to Git.**

---

## 31. Running PostgreSQL

**Start PostgreSQL + pgvector:**

```bash
docker compose up -d
```

**Check status:**

```bash
docker compose ps
```

The PostgreSQL service is exposed locally on `localhost:5433`. The database uses a Docker volume so data survives container restarts.

**Stop services:**

```bash
docker compose down
```

---

## 32. Backend Setup

**Create the Python environment:**

```powershell
py -3.12 -m venv .\apps\backend\.venv
```

**Activate:**

```powershell
.\apps\backend\.venv\Scripts\Activate.ps1
```

**Install backend dependencies:**

```powershell
pip install -r .\apps\backend\requirements.txt
```

**Install local packages:**

```powershell
pip install -e .\packages\schemas
pip install -e .\packages\database
```

**Run database migrations:**

```powershell
alembic -c .\apps\backend\alembic.ini upgrade head
```

---

## 33. Frontend Setup

**Navigate to the frontend:**

```bash
cd .\apps\frontend
```

**Install dependencies:**

```bash
npm install
```

**Start the development server:**

```bash
npm run dev
```

Frontend available at: `http://localhost:5173`

---

## 34. Running the Full System

**Terminal 1 — Database:**

```bash
docker compose up -d
```

**Terminal 2 — Backend:**

```powershell
.\apps\backend\.venv\Scripts\Activate.ps1
uvicorn app.main:app --app-dir .\apps\backend\src --reload
```

Backend: `http://localhost:8000`

**Terminal 3 — Frontend:**

```powershell
cd .\apps\frontend
npm run dev
```

Frontend: `http://localhost:5173`

---

## 35. Database Migrations

Alembic manages database schema changes.

**Current migration chain:**

```
001460d0a331
       |
       v
a9279e7aa50b
       |
       v
758e73172ba8
```

Migrations include: initial schema, HNSW vector index, GIN full-text-search index.

**Apply migrations:**

```powershell
alembic -c .\apps\backend\alembic.ini upgrade head
```

---

## 36. Running Retrieval Evaluation

```powershell
.\apps\backend\.venv\Scripts\python.exe .\scripts\evaluate_retrieval.py
```

The evaluator compares Semantic, FTS, and Hybrid RRF against `data/evaluation/golden_retrieval.json`.

**Metrics:** Recall@5, Recall@10, MRR, nDCG@10

---

## 37. Monitoring

**Run monitoring for one hour:**

```powershell
.\apps\backend\.venv\Scripts\python.exe .\scripts\monitor_resolution_health.py --hours 1
```

**Run monitoring for 24 hours:**

```powershell
.\apps\backend\.venv\Scripts\python.exe .\scripts\monitor_resolution_health.py --hours 24
```

**Reported metrics:** total requests, successful/failed requests, success/failure/grounding rates, average/P50/P95 latency, average confidence, average retrieved/authoritative evidence, error types.

---

## 38. Development Quality Checks

**Linting:**

```bash
ruff check .
```

**Type checking:**

```bash
mypy .\apps\backend\src
```

**Backend tests:**

```bash
pytest .\apps\backend\tests
```

**All tests:**

```bash
pytest
```

---

## 39. Current Measured System Results

### Dataset

| Metric | Result |
|---|---|
| Conversation chunks | 229,652 |
| Embedded chunks | 229,652 |
| Missing embeddings | 0 |
| Embedding model | BGE-large-en-v1.5 |
| Embedding dimension | 1024 |

### Retrieval

| Method | Recall@5 | Recall@10 | MRR | nDCG@10 |
|---|---|---|---|---|
| Semantic | 0.3000 | 0.3000 | 0.2944 | 0.2663 |
| FTS | 0.0500 | 0.0833 | 0.0250 | 0.0373 |
| Hybrid RRF | 0.3333 | 0.3500 | 0.2844 | 0.2740 |

### Vector Search

- **HNSW index:** Active
- **Measured verification query:** ~114 ms
- **Representative hybrid retrieval:** ~70.69 ms

### First Request Optimization

| Before | After | Improvement |
|---|---|---|
| ~11.9 s | ~4.36 s | ~63% |

### Warm End-to-End Resolution

- **Representative request:** ~4.63 seconds
- **Complaint intelligence:** ~1.94 seconds
- **LLM resolution:** ~2.25 seconds

### Grounding

| Field | Value |
|---|---|
| Grounded | `true` |
| Unsupported steps | `[]` |
| Authoritative evidence | 5 |

### Tests

| Scope | Result |
|---|---|
| Backend | 37 passed, 1 warning |
| Repository | 78 passed, 1 warning |

---

## 40. Design Decisions

### Why PostgreSQL + pgvector?

PostgreSQL provides structured data, relational integrity, vector search, full-text search, metadata filtering, and monitoring storage in a single system — avoiding unnecessary infrastructure at the current scale.

### Why HNSW?

HNSW provides approximate nearest-neighbor search, avoiding brute-force vector comparison and scaling efficiently for the current corpus.

### Why PostgreSQL FTS?

Telecom support contains terminology where exact lexical matching is valuable (`router`, `WAN`, `APN`, `SIM`, `5G`, `ONT`, `ONU`). FTS complements semantic search by preserving exact terminology signals.

### Why Hybrid Retrieval?

Semantic retrieval handles paraphrases. FTS handles exact terminology. Combining both improves retrieval coverage.

### Why RRF?

Semantic similarity scores and FTS scores are not directly comparable. RRF combines ranking positions instead of requiring score calibration.

### Why Resolved-Only Retrieval?

Unresolved and escalated tickets should not be treated as proven solutions. Restricting historical retrieval to resolved cases improves evidence quality.

### Why Separate KB and Historical Evidence?

The KB is authoritative; historical tickets are supporting evidence only. Separating the two prevents outdated historical instructions from overriding current documentation.

### Why Grounding Validation?

LLMs can produce plausible but unsupported troubleshooting steps. Grounding validation creates a safety boundary before the response reaches the support agent.

---

## 41. Limitations

### 1. Retrieval Quality

Current hybrid Recall@10 is `0.3500`. Potential improvements include cross-encoder reranking, query expansion, metadata-aware filtering, better chunking, domain-specific embeddings, and hard-negative evaluation.

### 2. Limited Golden Dataset

The current retrieval benchmark contains 30 queries. A larger human-reviewed benchmark would provide stronger confidence.

### 3. Incomplete Historical Metadata

Many source conversations lack reliable `product`, `intent`, and `sub_intent` metadata. The system relies heavily on text retrieval and runtime complaint intelligence.

### 4. LLM Dependency

Resolution quality and latency depend on the external LLM provider. Provider outages and rate limits can affect the system.

### 5. Frontend Authentication

The current implementation focuses on the support-resolution workflow. Enterprise authentication and authorization would be required before external deployment.

### 6. Monitoring Maturity

A production deployment should additionally introduce Prometheus, Grafana, distributed tracing, centralized logs, alerting, SLOs, and error budgets.

### 7. Local Deployment

The current deployment is primarily Docker Compose + FastAPI + React + PostgreSQL. A production deployment would require managed infrastructure, scaling, backups, secrets management, and disaster recovery.

---

## 42. Future Improvements

### Retrieval

- Cross-encoder reranking
- Query expansion
- Metadata-aware filtering
- Domain-specific embedding models
- Hard-negative evaluation
- Better chunking and retrieval weight optimization
- Learned hybrid ranking

### Resolution Quality

- Step-level grounding
- Citation correctness evaluation
- Human feedback and resolution acceptance rate tracking
- LLM-as-judge evaluation
- Automated escalation evaluation

### Taxonomy

- Taxonomy versioning
- Automatic class discovery and clustering
- Human approval workflow
- Taxonomy drift monitoring
- Historical class mapping

### Reliability

- LLM provider fallback and circuit breakers
- Exponential backoff and request queues
- Dead-letter queues
- Provider health checks and retry policies

### Infrastructure

- Kubernetes with horizontal autoscaling
- Redis caching and connection pooling
- Read replicas and centralized observability
- Managed PostgreSQL and dedicated vector infrastructure

### Security

- Authentication and role-based authorization
- PII redaction
- Prompt-injection detection
- Audit logging, secret management, data retention controls

---

## 43. Project Status

| Component | Status |
|---|---|
| Complaint intelligence | ✅ Complete |
| Semantic retrieval | ✅ Complete |
| PostgreSQL FTS | ✅ Complete |
| HNSW vector indexing | ✅ Complete |
| GIN FTS indexing | ✅ Complete |
| Hybrid RRF retrieval | ✅ Complete |
| Resolved-only retrieval | ✅ Complete |
| Evidence policy | ✅ Complete |
| KB-authoritative generation | ✅ Complete |
| Grounding validation | ✅ Complete |
| Safety fallback | ✅ Complete |
| LLM rate-limit handling | ✅ Complete |
| Resolution logging | ✅ Complete |
| Health monitoring | ✅ Complete |
| Retrieval evaluation | ✅ Complete |
| Automated tests | ✅ Complete |
| Docker PostgreSQL setup | ✅ Complete |
| React frontend | ✅ Complete |
| Production documentation | ✅ Complete |
| Frontend screenshots | ✅ Complete |
| Final repository cleanup | ✅ Complete |

---

## 44. Conclusion

This project implements an **evidence-grounded semantic resolution assistant** for telecom customer support.

The system goes beyond basic semantic search or LLM-based question answering by combining:

```
Complaint Intelligence
        +
Semantic Retrieval
        +
PostgreSQL Full-Text Search
        +
Hybrid RRF Ranking
        +
Authoritative Knowledge Base
        +
Historical Support Evidence
        +
Structured LLM Generation
        +
Grounding Validation
        +
Safety Fallback
        +
Evaluation
        +
Operational Monitoring
```

**Core design principle:**

```
Understand → Retrieve → Rank → Select Evidence → Generate → Validate → Monitor
```

The LLM is not treated as the source of truth. Instead:

```
Knowledge Base → Evidence → LLM → Validation → Agent
```

This provides a safer and more maintainable architecture for support resolution.

The current implementation demonstrates measurable improvements in retrieval quality, indexed vector and lexical search, structured complaint understanding, grounded resolution generation, rate-limit handling, monitoring, and automated testing.

The remaining work is primarily focused on final documentation, frontend screenshots, repository cleanup, stronger production observability, and future retrieval and deployment improvements.

---

## License

This project is provided for academic and evaluation purposes.