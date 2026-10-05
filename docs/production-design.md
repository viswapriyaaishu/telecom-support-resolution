# Production Design

## 1. Purpose

This document describes how the Intelligent Support Ticket Resolution Assistant can evolve from the current development implementation into a production-scale telecom support platform.

The current repository already implements the core resolution workflow:

```text
React
   ↓
FastAPI
   ↓
Complaint Intelligence
   ↓
Hybrid Retrieval
   ↓
Evidence Policy
   ↓
LLM Resolution
   ↓
Grounding Validation
   ↓
Structured Response

The production design extends this architecture with scalability, reliability, observability, security, deployment, and operational controls.

The production architecture described here represents the intended evolution of the system. Components that are not currently deployed are explicitly described as future production infrastructure rather than being presented as already implemented.

2. Current Implementation vs Production Evolution
Area	Current Implementation	Production Evolution
Frontend	React + TypeScript + Vite	CDN-backed production frontend
API	FastAPI	Horizontally scaled FastAPI instances
Database	PostgreSQL + pgvector	Managed PostgreSQL cluster
Vector search	pgvector HNSW	Tuned/partitioned vector infrastructure
Lexical search	PostgreSQL FTS + GIN	Dedicated search infrastructure if required
LLM	OpenAI-compatible provider	Provider abstraction + fallback strategy
Caching	Not required for current prototype	Redis/cache layer
Background jobs	Limited synchronous workflow	Queue + worker architecture
Monitoring	Structured resolution logs	Centralized metrics/logging/tracing
Deployment	Docker Compose	Container orchestration
Secrets	Environment variables	Managed secrets service
Scaling	Single development environment	Horizontal scaling
Evaluation	30-query golden set	Continuous evaluation pipeline
3. Production Architecture
4. API Scaling

The FastAPI application should remain stateless wherever possible.

A production deployment can run multiple API instances:

                Load Balancer
                     |
        +------------+------------+
        |            |            |
      API-1        API-2        API-N

Requests can then be distributed across instances.

Stateless API instances make horizontal scaling straightforward because any instance can process any request.

Application state should therefore be stored in shared infrastructure such as:

PostgreSQL
Redis
Object storage
Queue systems

rather than local process memory.

5. Database Scaling

PostgreSQL is the central persistence layer.

The current system uses:

PostgreSQL
+
pgvector
+
HNSW
+
GIN FTS

A production deployment can move PostgreSQL to a managed database service with:

Automated backups
Point-in-time recovery
Replication
Monitoring
Storage scaling
High availability

The application should use a connection pool rather than opening a new database connection for every request.

6. Connection Pooling

With multiple FastAPI instances, uncontrolled database connections can exhaust PostgreSQL connection limits.

A production deployment should therefore use:

FastAPI Instances
       |
       v
Connection Pool / Pooler
       |
       v
PostgreSQL

Possible controls include:

Maximum pool size
Minimum pool size
Connection timeout
Idle connection timeout
Statement timeout

Connection pool sizing should be based on:

Number of API instances
Expected concurrency
PostgreSQL connection limits
Average query duration
7. Vector Search Scaling

The current system stores 229,652 embedded conversation chunks.

Vector search currently uses an HNSW index.

As the corpus grows significantly, production operations should monitor:

Index size
Search latency
Recall
Memory usage
Build time
Update frequency

Potential scaling strategies include:

HNSW parameter tuning
Partitioning
Separate retrieval infrastructure
Periodic index maintenance
Archiving old data
Dedicated vector database if PostgreSQL becomes a bottleneck

The decision to introduce a separate vector database should be driven by measured workload rather than architecture preference alone.

8. Lexical Search Scaling

PostgreSQL FTS is currently sufficient for the implemented workload.

The system uses a GIN index to accelerate lexical retrieval.

If the corpus or query volume grows substantially, a dedicated search engine could be introduced.

Possible future architecture:

                 Retrieval Request
                        |
             +----------+----------+
             |                     |
       Vector Search          Search Engine
             |                     |
             +----------+----------+
                        |
                       RRF

A dedicated search engine would be justified only if PostgreSQL FTS no longer provides the required:

Latency
Throughput
Search functionality
Operational scalability
9. Caching Strategy

A production deployment can introduce Redis for frequently reused information.

Potential cache candidates include:

Knowledge-base content

KB documents that change infrequently can be cached.

Query embeddings

Repeated or identical complaints can reuse embeddings for a limited period.

Taxonomy

Intent and product taxonomy can be cached because it changes less frequently than individual requests.

Configuration

Provider configuration and non-secret runtime configuration can be cached where appropriate.

Caching should not bypass correctness requirements.

For example, resolution responses should not be cached indefinitely because KB content may change.

10. Cache Invalidation

Caching introduces a consistency problem.

KB updates must invalidate affected cached information.

A possible strategy is:

KB Update
   |
   v
Version Change
   |
   v
Invalidate Cache
   |
   v
New Retrieval

A version number can be associated with KB content.

For example:

KB version 1
KB version 2
KB version 3

When a KB version changes, cached retrieval or evidence results associated with the old version can be invalidated.

11. Background Processing

Not every operation needs to happen synchronously during a customer-support request.

Long-running operations can be moved to background workers.

Potential asynchronous tasks include:

Document ingestion
OCR
Chunking
Embedding generation
Bulk embedding updates
Evaluation runs
Analytics aggregation
Feedback processing
Taxonomy analysis

A production queue architecture could be:

API
 |
 v
Queue
 |
 +--> Ingestion Worker
 +--> Embedding Worker
 +--> Evaluation Worker
 +--> Analytics Worker

This prevents expensive background workloads from consuming API worker capacity.

12. Ingestion Pipeline

Knowledge-base and historical support data should enter the system through a controlled ingestion pipeline.

A production ingestion flow can be:

Source Documents
      |
      v
Validation
      |
      v
Text Extraction
      |
      v
Chunking
      |
      v
Metadata Enrichment
      |
      v
Embedding
      |
      v
Indexing
      |
      v
Evaluation
      |
      v
Publish

A document should not become authoritative production evidence until it passes validation.

13. Knowledge Base Versioning

Knowledge-base information can change over time.

Production systems should preserve:

Document ID
Version
Effective date
Expiration date
Product
Category
Section
Author or owner
Last updated timestamp

This allows the resolution system to determine which KB information was active when a resolution was generated.

14. LLM Provider Reliability

The current implementation already includes explicit rate-limit handling.

The provider layer raises:

LLMRateLimitError

when a provider returns HTTP 429.

The API converts this into a controlled:

503 Service Unavailable

response with a Retry-After header.

In production, this can be extended with:

Exponential backoff
Jitter
Retry budgets
Circuit breakers
Provider health checks
Provider fallback
Request timeouts
15. Provider Fallback

The LLM provider abstraction allows the system to support multiple compatible providers.

A production design can use:

                 Resolution Request
                         |
                         v
                 Primary Provider
                         |
                 +-------+-------+
                 |               |
              Success          Failure
                 |               |
                 v               v
              Response      Fallback Provider

Fallback should only occur for appropriate failure classes.

For example:

Temporary rate limit → retry or alternate provider
Timeout → retry with controlled budget
Authentication failure → do not blindly retry
Invalid request → return controlled error
Provider outage → fallback if configured
16. Timeout Strategy

Every external dependency should have a bounded timeout.

Relevant dependencies include:

PostgreSQL
LLM provider
External APIs
Redis
Queue services

The production system should avoid unbounded requests.

A request should have an overall deadline:

Incoming Request
       |
       v
Overall Deadline
       |
 +-----+-----+----------+
 |           |          |
DB         LLM       Other
Timeout   Timeout    Timeout

This prevents one slow dependency from consuming resources indefinitely.

17. Retry Strategy

Retries should be applied selectively.

Good candidates:

Temporary network errors
Provider rate limits
Transient database connection failures

Bad candidates:

Invalid request
Authentication failure
Schema validation failure
Permanent configuration errors

Retries should use exponential backoff and jitter to prevent synchronized retry storms.

18. Idempotency

Production APIs should consider request duplication.

For example, a support agent may accidentally submit the same request twice because of a network timeout.

An idempotency key can be used:

POST /api/v1/resolve
Idempotency-Key: <unique-request-id>

The server can associate the request ID with its result for a controlled retention period.

This is especially useful if resolution requests eventually trigger external side effects.

19. Rate Limiting

The API should implement request-level rate limiting.

Possible dimensions include:

User
Support-agent account
Organization
IP address
API key

Example:

Agent
  |
  v
Rate Limiter
  |
  +--> Allowed --> API
  |
  +--> Rejected --> 429

Rate limiting protects the API and downstream LLM provider from accidental or malicious overload.

20. Security Architecture

Production deployment should follow defense-in-depth principles.

Authentication

Support agents should authenticate through an enterprise identity provider or secure authentication mechanism.

Authorization

Permissions should determine which users can:

Submit complaints
View historical tickets
View customer information
Access KB administration
Review monitoring data
Modify taxonomy
Secrets

Secrets should be stored in a managed secrets system rather than committed to source control.

Encryption

Use TLS for external communication.

Database connections should use encrypted transport where supported.

Audit logging

Security-sensitive operations should be logged.

Examples:

Login
Permission changes
KB updates
Taxonomy changes
Administrative operations
21. Customer Data Protection

Telecom support data can contain sensitive customer information.

Production processing should therefore consider:

Data minimization
PII detection
PII masking
Retention policies
Access control
Audit logging
Encryption
Secure deletion

Only information required for support resolution should be passed into the LLM prompt.

Sensitive information should not be unnecessarily included in model context.

22. LLM Prompt Security

The retrieval system should assume that retrieved text may contain malicious or irrelevant instructions.

Retrieved historical conversations should therefore be treated as data rather than executable instructions.

The prompt hierarchy should make the evidence authority explicit:

System instructions
       |
       v
Application rules
       |
       v
Authoritative KB evidence
       |
       v
Historical supporting evidence
       |
       v
Customer complaint

Historical text must not be allowed to override system or application instructions.

23. Grounding and Safety

Production deployment should preserve the current grounding architecture:

Retrieved Evidence
       |
       v
LLM Resolution
       |
       v
Grounding Validation
       |
   +---+---+
   |       |
 Valid   Invalid
   |       |
   v       v
Return   Fallback

This provides an important safety boundary between LLM generation and the final support-agent response.

24. Observability

Production monitoring should cover three major areas:

System metrics
CPU
Memory
Disk
Network
Container health
Database connections
Application metrics
Request count
Success rate
Error rate
API latency
Retrieval latency
LLM latency
Grounding rate
Resolution confidence
Business metrics
Resolution success
Escalation rate
Agent feedback
Retrieval relevance
Frequently occurring complaint types
25. Logging

Application logs should be structured rather than plain unstructured strings.

Example:

{
  "request_id": "abc123",
  "endpoint": "/api/v1/resolve",
  "latency_ms": 4628,
  "grounded": true,
  "retrieval_count": 7,
  "authoritative_evidence_count": 5,
  "confidence": 0.9
}

Logs should not contain:

API keys
Passwords
Database credentials
Unnecessary customer PII

A request ID should allow logs from different services to be correlated.

26. Distributed Tracing

As the system grows into multiple services, distributed tracing becomes useful.

A request can be traced across:

Frontend
   |
API
   |
Intelligence
   |
Embedding
   |
Vector Search
   |
FTS
   |
KB Retrieval
   |
LLM
   |
Validation

This allows engineers to identify which stage contributes most to latency.

27. Performance Budgets

The current representative warm request completed in approximately:

4.63 seconds

with major components including:

Intelligence:          ~1.94 s
Resolution LLM:        ~2.25 s
Historical Retrieval:  ~0.12 s
KB Retrieval:          ~0.06 s

This indicates that model inference currently contributes more latency than database retrieval.

Future optimization should therefore prioritize measured bottlenecks.

Potential improvements include:

Smaller/faster intelligence model
Embedding model optimization
Cached embeddings
Parallel retrieval
Streaming LLM output
Prompt reduction
Faster LLM provider/model
Reranking only when necessary
28. Parallelization Opportunities

Some independent operations can execute concurrently.

For example:

Complaint
   |
   +--------> Semantic Retrieval
   |
   +--------> FTS Retrieval
   |
   +--------> KB Retrieval

The results can then be combined.

Similarly, complaint intelligence and query embedding may be evaluated for parallel execution if they do not depend on each other's output.

Parallelization can reduce wall-clock latency while preserving the same logical workflow.

29. Database Backup and Recovery

Production PostgreSQL should have:

Automated backups
Point-in-time recovery
Backup retention
Restore testing
Disaster recovery procedures

Backups should be encrypted and stored separately from the primary database environment.

A backup strategy is incomplete without periodic restore verification.

30. High Availability

A production deployment should avoid a single point of failure.

Potential architecture:

                 Load Balancer
                      |
             +--------+--------+
             |                 |
          API-A             API-B
             |                 |
             +--------+--------+
                      |
                PostgreSQL HA
                      |
             +--------+--------+
             |                 |
         Primary            Replica

The exact topology should depend on:

Availability requirements
Budget
Traffic
Database workload
Recovery objectives
31. Deployment Strategy

The current system can be containerized for deployment.

A production CI/CD pipeline could be:

Git Push
   |
   v
CI
   |
   +--> Unit Tests
   +--> Integration Tests
   +--> Ruff
   +--> mypy
   +--> Build
   |
   v
Container Image
   |
   v
Deployment
   |
   v
Health Checks
   |
   v
Production

A deployment should not proceed if mandatory quality checks fail.

32. Database Migration Strategy

Database schema changes should continue to use Alembic.

Production migration workflow:

Code Change
    |
    v
Migration
    |
    v
CI Validation
    |
    v
Staging
    |
    v
Backup
    |
    v
Production Migration

Destructive migrations should be handled carefully and preferably through backward-compatible intermediate releases.

33. Blue-Green or Rolling Deployment

API instances can be deployed gradually.

For example:

Current Version
      |
      +----> New Version
               |
          Health Checks
               |
               v
        Gradual Traffic
               |
               v
          Full Traffic

This reduces the risk of deploying a faulty release to every API instance simultaneously.

34. Testing Strategy

Production readiness should include multiple testing layers.

Unit tests

Test individual services and utility functions.

Integration tests

Test:

PostgreSQL
pgvector
API
Retrieval
LLM provider abstraction
End-to-end tests

Test:

Complaint
   |
   v
API
   |
   v
Resolution
Retrieval evaluation

Run the golden retrieval set regularly.

Load testing

Measure:

Requests per second
Concurrent requests
P50 latency
P95 latency
P99 latency
Error rate
35. Continuous Retrieval Evaluation

Retrieval evaluation should become part of CI or scheduled evaluation.

A future pipeline can be:

Retrieval Change
      |
      v
Golden Evaluation
      |
      v
Compare Metrics
      |
      +----> Improvement --> Accept
      |
      +----> Regression --> Review

Metrics such as Recall@5, Recall@10, MRR, and nDCG@10 should be compared against a baseline.

This prevents retrieval changes from silently degrading system quality.

36. Model Versioning

The system should track model versions for reproducibility.

Relevant versions include:

Embedding model
Intelligence model
Resolution model
Prompt version
Taxonomy version
KB version

For example:

embedding_model = bge-large-en-v1.5
intelligence_model = llm-intelligence-v1
prompt_version = resolution-v1
taxonomy_version = v1

A resolution log should make it possible to determine which model and configuration produced a response.

37. Prompt Versioning

Prompts should be treated as application artifacts rather than informal text.

A prompt change can alter:

Resolution quality
Grounding
Escalation decisions
Output style
Token usage

Therefore, production deployments should associate generated responses with a prompt version.

This allows evaluation and rollback when a prompt change introduces regressions.

38. Taxonomy Evolution

The taxonomy should evolve from observed production data.

A possible process is:

Support Tickets
      |
      v
Aggregate Sub-intents
      |
      v
Identify New Patterns
      |
      v
Human Review
      |
      v
Taxonomy Update
      |
      v
Evaluation
      |
      v
Production

Top-level intents should remain controlled, while new sub-intents and products can be introduced without requiring structural database redesign.

39. Feedback Loop

Support agents should eventually be able to provide feedback on:

Retrieval relevance
Diagnosis quality
Recommended steps
Escalation correctness
Overall resolution usefulness

The feedback can be used for:

Retrieval evaluation
Prompt improvement
Taxonomy evolution
Model evaluation
Error analysis

The feedback loop should not automatically change production behavior without validation.

40. Cost Management

LLM usage can become a major operational cost.

Production controls should include:

Token limits
Prompt-size monitoring
Evidence limits
Model selection
Caching
Request budgets
Rate limiting

The current Evidence Policy already limits the number of KB and historical results entering the prompt.

This provides an initial control over prompt growth.

41. Production SLO Examples

Illustrative SLOs can be defined after sufficient production traffic has been observed.

Examples:

API availability:        >= 99.9%
Successful resolution:   >= 99%
P95 API latency:         < target defined from production baseline
Grounded responses:      >= target defined from evaluation
Retrieval Recall@10:     >= validated baseline

These should be treated as targets to validate against actual operational requirements rather than claims about the current system.

42. Failure Scenarios

Important production failure scenarios include:

Database unavailable

Return a controlled service error and alert operations.

LLM provider unavailable

Use retry/fallback logic where appropriate.

LLM rate limited

Respect provider retry information and return controlled 503 responses when necessary.

Retrieval failure

Do not generate an unsupported resolution from empty evidence.

Grounding failure

Use the safety fallback and escalate.

Queue unavailable

Prevent background work from silently disappearing and provide retry/dead-letter handling.

Cache unavailable

The application should continue operating against the primary data source when possible.

43. Disaster Recovery

The production system should define:

RPO

Maximum acceptable amount of data loss.

RTO

Maximum acceptable recovery time.

These values should determine:

Backup frequency
Replication strategy
Database topology
Recovery procedures

Disaster recovery should be tested rather than assumed.

44. Scalability Roadmap

A practical evolution path is:

Stage 1 — Current implementation
React
+
FastAPI
+
PostgreSQL/pgvector
+
LLM
+
Docker Compose
Stage 2 — Production hardening

Add:

Authentication
Rate limiting
Connection pooling
Centralized logging
Metrics
Secrets management
CI/CD
Backups
Stage 3 — Horizontal scaling

Add:

Load balancer
Multiple API instances
Redis
Background workers
Queue
Stage 4 — Large-scale retrieval

Evaluate:

Search infrastructure
Reranking
Partitioning
Dedicated vector infrastructure
Stage 5 — Continuous intelligence

Add:

Feedback loop
Continuous retrieval evaluation
Taxonomy evolution
Model evaluation
A/B testing
45. Design Principles

The production design follows these principles:

Scale horizontally

Keep API services stateless so additional instances can be added as traffic increases.

Measure before optimizing

Use actual latency, throughput, retrieval, and failure metrics to identify bottlenecks.

Keep authoritative evidence separate

KB content remains the source of truth for operational recommendations.

Fail safely

Provider failures, retrieval failures, and grounding failures should produce controlled outcomes.

Separate synchronous and asynchronous work

User-facing resolution should remain focused on operations required to produce the immediate answer.

Version everything important

Models, prompts, taxonomy, KB content, and evaluation sets should be versioned.

Protect customer data

Minimize, mask, secure, and audit sensitive support information.

46. Final Production Perspective

The current implementation demonstrates the core technical architecture required for semantic telecom support resolution.

The production evolution described in this document does not assume that every component is already deployed.

Instead, it provides a concrete path from the current implementation toward a scalable production platform.

The most important production priorities are:

Reliable API scaling
PostgreSQL connection and workload management
LLM reliability and provider fallback
Strong observability
Customer-data protection
Continuous retrieval evaluation
Safe grounding and escalation
Controlled taxonomy and model evolution

The architecture is intentionally incremental: existing components such as FastAPI, PostgreSQL, pgvector, hybrid retrieval, evidence policy, grounding validation, and structured logging can be retained while infrastructure around them is progressively hardened for production workloads.