# System Architecture

## 1. Overview

The Intelligent Support Ticket Resolution Assistant is a production-oriented semantic support system designed to help telecom customer-support agents resolve complaints using historical conversations and authoritative knowledge-base (KB) information.

The system combines:

- React + TypeScript frontend
- FastAPI backend
- Complaint intelligence extraction
- Semantic vector retrieval
- PostgreSQL full-text search
- Reciprocal Rank Fusion (RRF)
- Evidence selection and policy enforcement
- LLM-based grounded resolution generation
- Grounding validation and safety fallback
- PostgreSQL + pgvector persistence
- Structured resolution logging
- Docker-based PostgreSQL deployment

The system is designed so that the knowledge base remains the authoritative source for troubleshooting recommendations, while historical support conversations provide supporting context.

---

## 2. High-Level Architecture

```mermaid
flowchart TD

    A[Support Agent] --> B[React + TypeScript Web App]

    B --> C[FastAPI API Service]

    C --> D[Complaint Intelligence Service]

    D --> D1[Intent]
    D --> D2[Sub-intent]
    D --> D3[Product]
    D --> D4[Severity]
    D --> D5[Sentiment]
    D --> D6[Entities]

    C --> E[Resolution Service]

    E --> F[Hybrid Retrieval Service]

    F --> G[Semantic Vector Search]
    F --> H[PostgreSQL Full-Text Search]

    G --> I[Reciprocal Rank Fusion]
    H --> I

    I --> J[Retrieved Historical Evidence]

    C --> K[Knowledge Base Retrieval]

    J --> L[Evidence Policy]
    K --> L

    L --> M[Evidence Builder]

    M --> N[Resolution Prompt]

    N --> O[LLM Provider]

    O --> P[Structured Resolution]

    P --> Q[Grounding Validation]

    Q --> R{Grounded?}

    R -->|Yes| S[Final Resolution]
    R -->|No| T[Safety Fallback]

    S --> B
    T --> B

    C --> U[Resolution Logging]

    G --> V[(PostgreSQL + pgvector)]
    H --> V
    K --> V
    U --> V

    ## 3. Request Flow

A support agent submits a customer complaint through the React frontend.

Example:

> My broadband drops every evening around 8 and I have already restarted the router twice. I work from home and this is costing me.

The request follows these stages:

1.  The React frontend sends the complaint to the FastAPI backend. 
2.  The Complaint Intelligence Service classifies the complaint. 
3.  The system extracts intent, sub-intent, product, severity, sentiment, and entities. 
4.  The complaint is converted into an embedding. 
5.  Semantic retrieval searches historical resolved conversations. 
6.  PostgreSQL Full-Text Search performs lexical retrieval. 
7.  Semantic and lexical candidates are combined using Reciprocal Rank Fusion. 
8.  Knowledge-base retrieval searches authoritative troubleshooting information. 
9.  The Evidence Policy limits and prioritizes the retrieved evidence. 
10.  A grounded prompt is constructed. 
11.  The LLM generates a structured resolution. 
12.  Grounding validation checks the generated troubleshooting steps. 
13.  Unsupported recommendations trigger a safety fallback. 
14.  The final structured response is returned to the frontend. 
15.  Resolution metadata and performance information are logged. 

---

## 4. Frontend Layer

The frontend is implemented using:

-  React 
-  TypeScript 
-  Vite 

The frontend provides the support-agent interface for submitting complaints and viewing:

-  Complaint intelligence 
-  Retrieved evidence 
-  Generated resolution 
-  Recommended troubleshooting steps 
-  Escalation decision 
-  Confidence 
-  Citations 

The frontend communicates with the backend through the FastAPI HTTP API.

---

## 5. API Layer

The backend is implemented using FastAPI.

The main resolution endpoint is:

```
```

```
POST /api/v1/resolve
```

The request contains the customer's complaint.

The API performs:

-  Request validation 
-  Complaint intelligence analysis 
-  Retrieval 
-  Evidence construction 
-  Resolution generation 
-  Grounding validation 
-  Structured response generation 
-  Resolution logging 

The API also handles provider rate limits.

If the LLM provider returns HTTP 429, the backend converts it into a controlled `503 Service Unavailable` response and exposes a `Retry-After` header.

---

## 6. Complaint Intelligence Layer

The Complaint Intelligence Service converts unstructured customer complaints into structured attributes.

The current schema contains:

```
```

```
intent
sub_intent
product
severity
sentiment
entities
confidence
model_version
```

The controlled top-level intent taxonomy currently includes:

```
```

```
Connectivity
Mobile
Billing
Account
Outage
Other
```

Severity levels:

```
```

```
LOW
MEDIUM
HIGH
CRITICAL
UNKNOWN
```

Sentiment levels:

```
```

```
POSITIVE
NEUTRAL
NEGATIVE
UNKNOWN
```

The system intentionally keeps `sub_intent` and `product` extensible so that new ticket classes can be introduced without repeatedly changing the database schema.

---

## 7. Retrieval Layer

The retrieval architecture uses two complementary retrieval strategies.

### 7.1 Semantic Retrieval

Historical support conversations are embedded using:

```
```

```
BAAI/bge-large-en-v1.5
```

The embedding dimension is:

```
```

```
1024
```

The database currently contains:

```
```

```
229,652 embedded conversation chunks
```

Semantic retrieval uses PostgreSQL with pgvector and an HNSW index.

The vector index is:

```
```

```
ix_conversation_chunks_embedding_hnsw
```

The HNSW index uses:

```
```

```
vector_cosine_ops
```

Semantic retrieval currently searches resolved conversations because resolved conversations represent completed support cases with known outcomes.

---

## 8. PostgreSQL Full-Text Search

The system also performs lexical retrieval using PostgreSQL Full-Text Search.

The FTS index is:

```
```

```
ix_conversation_chunks_text_fts_gin
```

The index uses:

```
```

```
GIN
```

with:

```
```

```
to_tsvector('english', text)
```

The lexical retrieval layer provides complementary keyword matching for terminology that may not be captured optimally by semantic similarity.

Broad OR-style searches can generate very large candidate sets, so the implementation uses query tokenization and more selective matching strategies.

---

## 9. Hybrid Retrieval

Semantic and lexical retrieval are combined using Reciprocal Rank Fusion (RRF).

The goal is to combine:

-  semantic similarity 
-  lexical relevance 

without relying exclusively on either retrieval strategy.

Conceptually:

```
```

```
Complaint
    |
    +--> Semantic Retrieval
    |
    +--> Full-Text Retrieval
              |
              v
        Candidate Results
              |
              v
             RRF
              |
              v
       Ranked Hybrid Results
```

This allows the system to retrieve semantically similar complaints even when wording differs while still benefiting from exact terminology matches.

---

## 10. Knowledge Base Retrieval

The system separately retrieves authoritative troubleshooting information from the knowledge base.

Knowledge-base evidence is treated differently from historical conversations.

### Authoritative evidence

Knowledge-base content is the source of truth for:

-  Troubleshooting steps 
-  Escalation criteria 
-  Operational recommendations 

### Historical evidence

Historical conversations are used primarily for:

-  Similar symptoms 
-  Terminology 
-  Previously observed patterns 
-  Supporting context 

Historical conversations cannot override authoritative KB instructions.

---

## 11. Evidence Policy

The Evidence Policy controls how retrieved information enters the LLM prompt.

Current limits are:

```
```

```
Maximum KB results: 5
Maximum historical results: 1
```

The policy separates authoritative KB evidence from historical evidence before constructing the final evidence set.

This prevents the prompt from becoming unnecessarily large and reduces the possibility that historical conversations dominate authoritative troubleshooting instructions.

---

## 12. Resolution Generation

The Resolution Service constructs a prompt using:

-  Complaint 
-  Complaint intelligence 
-  Retrieved historical evidence 
-  Authoritative KB evidence 
-  Evidence policy output 

The resolution prompt explicitly instructs the LLM that:

1.  KB evidence is authoritative. 
2.  Historical conversations are supporting evidence only. 
3.  Historical text cannot override KB instructions. 
4.  Troubleshooting steps must not be invented. 
5.  Explicit KB steps should be preferred. 
6.  Historical evidence can provide symptoms and terminology. 
7.  KB conflicts always take precedence. 
8.  Insufficient evidence should result in further investigation or escalation. 
9.  Evidence should be cited. 
10.  Secrets must never be exposed. 
11.  Escalation criteria from the KB must be respected. 

---

## 13. Structured Resolution

The generated response follows a Pydantic-validated schema.

The response contains:

```
```

```
summary
diagnosis
recommended_steps
escalation_required
confidence
citations
```

Each citation contains:

```
```

```
source_id
section
```

This prevents the frontend from having to parse arbitrary natural-language LLM output.

---

## 14. Grounding Validation

Generated troubleshooting recommendations are validated against retrieved authoritative evidence.

The system checks whether recommended steps are supported by the available evidence.

If the generated resolution is grounded:

```
```

```
Grounded Resolution
        |
        v
Final Response
```

If unsupported recommendations are detected:

```
```

```
Ungrounded Resolution
        |
        v
Safety Fallback
        |
        v
Escalation / Further Investigation
```

The fallback response is intentionally conservative rather than allowing unsupported troubleshooting instructions to reach the support agent.

---

## 15. Database Architecture

The application uses PostgreSQL with pgvector.

The database stores:

-  Conversations 
-  Conversation chunks 
-  Embeddings 
-  Knowledge-base content 
-  Knowledge-base chunks 
-  Taxonomy information 
-  Resolution logs 
-  Retrieval information 
-  Feedback-related information 

Conversation chunks are linked to their parent conversations through foreign keys.

The database uses specialized indexes for retrieval workloads:

```
```

```
HNSW
    ↓
Vector similarity search

GIN
    ↓
PostgreSQL Full-Text Search
```

---

## 16. Database Migrations

Database schema and index changes are managed through Alembic.

Current migration sequence:

```
```

```
001460d0a331
      ↓
a9279e7aa50b
      ↓
758e73172ba8
```

The latest migration adds the PostgreSQL Full-Text Search GIN index.

The earlier migration added the HNSW vector index.

This keeps production schema changes reproducible instead of relying on manual database modifications.

---

## 17. Performance Architecture

Several optimizations were introduced to reduce latency.

### Embedding model preload

The embedding model is loaded during FastAPI application startup.

This avoids loading the model during the first user request.

Observed improvement:

```
```

```
Before preload: approximately 11.9 seconds
After preload: approximately 4.36 seconds
```

This corresponds to approximately a 63% reduction in first-request latency.

### Vector indexing

HNSW is used for approximate nearest-neighbor vector retrieval.

### Lexical indexing

GIN indexing is used for PostgreSQL Full-Text Search.

### Evidence limiting

The Evidence Policy limits historical and KB results to reduce prompt size and LLM processing cost.

---

## 18. Current Retrieval Evaluation

A golden retrieval evaluation set containing 30 queries is used to compare:

-  Semantic retrieval 
-  PostgreSQL Full-Text Search 
-  Hybrid RRF retrieval 

Current results:

| Method     | Recall\@5 | Recall\@10 | MRR    | nDCG\@10 |
| ---------- | --------- | ---------- | ------ | -------- |
| Semantic   | 0.3000    | 0.3000     | 0.2944 | 0.2663   |
| FTS        | 0.0500    | 0.0833     | 0.0250 | 0.0373   |
| Hybrid RRF | 0.3333    | 0.3500     | 0.2844 | 0.2740   |

Hybrid retrieval currently provides the strongest Recall\@5, Recall\@10, and nDCG\@10 results.

Semantic retrieval has slightly higher MRR than hybrid retrieval.

---

## 19. End-to-End Performance

For the representative broadband complaint, the current warm API execution produced:

```
```

```
Intelligence:             1936.13 ms
Query Embedding:           267.05 ms
Historical Retrieval:      115.33 ms
KB Retrieval:               58.35 ms
Evidence Retrieval:        441.26 ms
Evidence Policy:             0.03 ms
Prompt Construction:         0.06 ms
Resolution LLM:            2248.63 ms
Grounding Validation:        0.22 ms
Resolution Service Total:  2691.12 ms
Total:                     4628.31 ms
```

The measured end-to-end latency for this request was approximately:

```
```

```
4.63 seconds
```

The largest components are complaint intelligence inference and LLM resolution generation.

---

## 20. Monitoring

Resolution requests are logged with structured operational information including:

```
```

```
complaint
intent
sub_intent
product
severity
sentiment
retrieval_count
authoritative_evidence_count
grounded
unsupported_steps
resolution_confidence
resolution_summary
latency_ms
error_type
error_message
created_at
```

The monitoring script reports:

-  Total requests 
-  Successful requests 
-  Failed requests 
-  Success rate 
-  Failure rate 
-  Grounding rate 
-  Average latency 
-  Median latency 
-  P95 latency 
-  Average confidence 
-  Average retrieved evidence 
-  Average authoritative evidence 
-  Error types 

---

## 21. Reliability and Rate-Limit Handling

The LLM provider is accessed through a provider abstraction.

Provider failures are represented using structured exceptions.

HTTP 429 responses are converted into:

```
```

```
LLMRateLimitError
```

The exception stores the provider retry delay.

The API converts this into:

```
```

```
HTTP 503 Service Unavailable
```

with a:

```
```

```
Retry-After
```

header.

This prevents provider rate limits from becoming unhandled internal server errors.

---

## 22. Security and Privacy

The application follows several security principles.

### Secrets

API keys and database credentials are loaded through environment variables.

Secrets are not stored directly in source code.

The `.env` file is excluded from version control.

### LLM prompts

Prompts explicitly instruct the model not to expose secrets.

### Database

Parameterized database access and ORM abstractions are used rather than constructing SQL from raw user input.

### API validation

Pydantic models validate incoming and outgoing API structures.

### Output safety

Generated recommendations are validated against retrieved evidence before being returned to the support agent.

---

## 23. Production Deployment Model

The current development environment uses Docker Compose for PostgreSQL.

A production deployment can separate the system into independently scalable services:

```
```

```
                    Load Balancer
                          |
              +-----------+-----------+
              |                       |
          API Instance            API Instance
              |                       |
              +-----------+-----------+
                          |
                  Retrieval Services
                          |
              +-----------+-----------+
              |                       |
          PostgreSQL             LLM Provider
          + pgvector
```

Potential production infrastructure includes:

-  Multiple FastAPI instances 
-  Managed PostgreSQL 
-  pgvector 
-  Connection pooling 
-  Redis for caching 
-  Background workers 
-  Centralized logging 
-  Metrics collection 
-  Distributed tracing 
-  Secrets management 
-  Load balancing 
-  Horizontal autoscaling 

The current repository demonstrates the core architecture but does not claim that all of these production infrastructure components are already deployed.

---

## 24. Design Principles

The architecture follows several key design principles.

### Retrieval before generation

The LLM does not directly answer from its general knowledge.

Relevant evidence is retrieved first and passed into the resolution generation process.

### Authoritative evidence hierarchy

KB evidence has higher authority than historical conversations.

### Hybrid retrieval

Semantic and lexical retrieval complement each other.

### Structured outputs

Pydantic schemas enforce predictable API responses.

### Safety fallback

Unsupported generated recommendations do not automatically reach the support agent.

### Observability

Resolution requests record latency, grounding, evidence, confidence, and error information.

### Evolvable taxonomy

Top-level intents are controlled while sub-intents and products remain extensible.

---

## 25. Current Architecture Summary

The implemented architecture can be summarized as:

```
```

```
Customer Complaint
       |
       v
React + TypeScript
       |
       v
FastAPI
       |
       +----------------------+
       |                      |
       v                      v
Complaint              Hybrid Retrieval
Intelligence                 |
       |              +-------+-------+
       |              |               |
       |          Vector Search      FTS
       |              |               |
       |              +-------+-------+
       |                      |
       |                     RRF
       |                      |
       +----------+-----------+
                  |
                  v
           Evidence Policy
                  |
                  v
          Grounded LLM Prompt
                  |
                  v
          Structured Resolution
                  |
                  v
         Grounding Validation
                  |
          +-------+-------+
          |               |
       Grounded        Ungrounded
          |               |
          v               v
      Resolution      Safety Fallback
          |
          v
       Frontend
```

This architecture provides the foundation for a semantic telecom support-resolution assistant while keeping retrieval, evidence authority, generation, validation, and observability as separate concerns.

```
```

```
```

