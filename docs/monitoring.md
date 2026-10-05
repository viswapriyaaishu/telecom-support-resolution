# Monitoring and System Health

## 1. Purpose

The Intelligent Support Ticket Resolution Assistant records structured operational information for each resolution request.

Monitoring is used to understand:

- Request volume
- Success and failure rates
- Resolution latency
- Retrieval behavior
- Evidence quality
- Grounding behavior
- Resolution confidence
- Provider failures
- Operational regressions

The current repository includes a monitoring script:

```text
scripts/monitor_resolution_health.py

2. Resolution Logging

Each resolution request records structured information including:

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

These fields provide both application-level and operational visibility.

For example, the system can determine not only whether a request succeeded, but also:

how long it took,
whether the response was grounded,
how much evidence was retrieved,
how confident the generated resolution was,
and whether an error occurred.
3. Monitoring Script

The monitoring utility is:

scripts/monitor_resolution_health.py

It accepts a configurable time window.

Example:

python .\scripts\monitor_resolution_health.py --hours 1

The script calculates:

Total requests
Successful requests
Failed requests
Success rate
Failure rate
Grounding rate
Average latency
Median latency (P50)
P95 latency
Average resolution confidence
Average retrieved evidence
Average authoritative evidence
Error types
4. Current Monitoring Snapshot

A recent one-hour monitoring window produced:

Total requests: 7
Successful requests: 5
Failed requests: 2
Success rate: 71.43%
Failure rate: 28.57%
Grounding rate: 100.00%
Average latency: 5190.68 ms
Median latency (P50): 4628.31 ms
P95 latency: 10044.47 ms
Average confidence: 0.898
Average retrieved evidence: 7.60
Average authoritative evidence: 5.00
Errors: RuntimeError: 2

These values represent the observed contents of the current development database for that monitoring window.

They should not be interpreted as production SLO measurements because the sample size is only seven requests.

5. Success and Failure Rate

The monitoring snapshot contained:

Total requests:       7
Successful requests:  5
Failed requests:      2

Therefore:

Success rate = 71.43%
Failure rate = 28.57%

However, the two failures require additional context.

They correspond to historical LLM provider rate-limit failures generated before the explicit rate-limit handling was implemented.

Therefore, the raw failure percentage does not represent the behavior of the latest rate-limit handling implementation.

This distinction is important when interpreting development monitoring data.

6. LLM Rate-Limit Handling

The LLM provider abstraction now explicitly handles HTTP 429 responses.

The provider raises:

LLMRateLimitError

and extracts retry information from:

Retry-After
provider response text
a default retry delay when no value is available

The API converts the rate-limit condition into:

HTTP 503 Service Unavailable

with:

Retry-After

This provides a controlled failure response instead of allowing provider rate limits to become unhandled internal errors.

7. Historical Errors in the Monitoring Window

The monitoring window still contains two older:

RuntimeError

entries.

These entries were created before the explicit LLMRateLimitError handling was added.

The current implementation therefore needs to be evaluated separately from these historical log entries.

The monitoring result demonstrates an important operational consideration:

Monitoring data must be interpreted together with deployment and implementation history.

A failure recorded in the database may correspond to an older version of the application.

8. Grounding Rate

The current monitoring snapshot reported:

Grounding rate: 100.00%

All successful resolutions in the sampled window were grounded according to the application's grounding validation.

Grounding is particularly important because the system generates troubleshooting recommendations using an LLM.

A high grounding rate indicates that generated recommendations are being supported by the retrieved evidence under the current validation logic.

9. Latency Monitoring

The monitoring system tracks multiple latency statistics.

Average latency

Current observed average:

5190.68 ms
Median latency / P50

Current observed median:

4628.31 ms
P95 latency

Current observed P95:

10044.47 ms

The difference between P50 and P95 demonstrates why average latency alone is insufficient.

A production monitoring system should track percentile latency because occasional slow requests can significantly affect user experience even when the average remains acceptable.

10. End-to-End Latency Breakdown

The representative warm end-to-end resolution request produced:

Intelligence:             1936.13 ms
Query Embedding:           267.05 ms
Historical Retrieval:      115.33 ms
KB Retrieval:               58.35 ms
Evidence Retrieval:        441.26 ms
Evidence Policy:             0.03 ms
Prompt Construction:         0.06 ms
Resolution LLM:            2248.63 ms
Grounding Validation:        0.22 ms
Safety Fallback:              0.00 ms
Resolution Service Total:  2691.12 ms
Retrieval + Resolution:    2691.55 ms
Total:                     4628.31 ms

The request therefore completed in approximately:

4.63 seconds
11. Main Latency Contributors

The current timing breakdown shows that the largest components are:

Complaint intelligence

Approximately:

1.94 seconds
Resolution LLM

Approximately:

2.25 seconds

In comparison:

Historical Retrieval ≈ 0.12 seconds
KB Retrieval         ≈ 0.06 seconds
Grounding Validation ≈ 0.0002 seconds

This indicates that the current primary latency bottlenecks are model inference rather than database retrieval.

Future optimization should therefore prioritize the intelligence and resolution-generation stages before prematurely replacing the current database retrieval architecture.

12. Evidence Monitoring

The monitoring script reports two evidence-related metrics:

Average retrieved evidence
Average authoritative evidence

The current snapshot reported:

Average retrieved evidence:       7.60
Average authoritative evidence:   5.00

The distinction is intentional.

Retrieved evidence can include both:

historical support conversations
authoritative KB evidence

The Evidence Policy limits the final evidence set to:

Maximum KB results: 5
Maximum historical results: 1

This helps prevent historical conversations from overwhelming authoritative KB evidence.

13. Confidence Monitoring

The current monitoring snapshot reported:

Average confidence: 0.898

Resolution confidence is generated as part of the structured resolution response and validated through the Pydantic schema.

Confidence should not be interpreted as an independently calibrated probability.

It is primarily an application-level signal that can be monitored for:

sudden drops
model regressions
unusual complaint categories
changes after prompt/model updates
14. Error Monitoring

The resolution log stores:

error_type
error_message

This allows failures to be grouped by category.

Examples of useful production error categories include:

LLM_RATE_LIMIT
LLM_TIMEOUT
LLM_PROVIDER_ERROR
DATABASE_ERROR
RETRIEVAL_ERROR
VALIDATION_ERROR
INTERNAL_ERROR

Grouping errors allows engineering teams to distinguish infrastructure failures from application or provider failures.

15. Monitoring Dimensions

A production monitoring dashboard should organize health information into several dimensions.

Availability
Request count
Success rate
Failure rate
HTTP error rates
Performance
P50 latency
P95 latency
P99 latency
Retrieval latency
LLM latency
Resolution quality
Grounding rate
Unsupported-step rate
Resolution confidence
Escalation rate
Retrieval quality
Retrieved evidence count
Authoritative evidence count
Retrieval latency
Golden-set Recall@5
Golden-set Recall@10
MRR
nDCG@10
Provider health
Rate-limit count
Timeout count
Provider errors
Retry count
Fallback count
16. Health Monitoring Architecture

The current logging model can evolve into a production observability architecture:

                    Resolution Request
                           |
                           v
                    FastAPI Service
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          Metrics         Logs         Traces
             |             |             |
             +-------------+-------------+
                           |
                           v
                 Monitoring Platform

The current PostgreSQL resolution log provides the foundation for this monitoring model.

17. Alerting

Production deployments should define alerts for abnormal conditions.

Examples include:

High error rate

Trigger when the failure rate exceeds an operational threshold for a sustained period.

High latency

Trigger when P95 or P99 latency exceeds the agreed service target.

LLM rate limits

Alert when provider rate-limit events increase unexpectedly.

Grounding degradation

Alert when the grounding rate drops below the validated baseline.

Confidence degradation

Monitor for significant changes in average resolution confidence.

Database problems

Alert on:

Connection exhaustion
High query latency
Disk pressure
Replication problems
18. Monitoring Baselines

Monitoring thresholds should be based on measured system behavior rather than arbitrary numbers.

The current representative warm request provides an initial latency baseline:

P50-like observed request: approximately 4.63 seconds

The current retrieval evaluation provides an initial quality baseline:

Method	Recall@5	Recall@10	MRR	nDCG@10
Semantic	0.3000	0.3000	0.2944	0.2663
FTS	0.0500	0.0833	0.0250	0.0373
Hybrid RRF	0.3333	0.3500	0.2844	0.2740

Future releases can compare their results against these baselines.

19. Quality Regression Detection

Operational monitoring should be combined with offline evaluation.

For example:

Application Change
       |
       +--> Automated Tests
       |
       +--> Retrieval Evaluation
       |
       +--> Production Monitoring
       |
       v
   Regression Analysis

A deployment should not be considered successful only because the API returns HTTP 200 responses.

The system should also be evaluated for:

Retrieval quality
Grounding
Latency
Error rate
Confidence
Resolution usefulness
20. Monitoring Limitations

The current monitoring implementation has several limitations.

Small sample size

The current snapshot contains only seven requests.

Therefore, statistics such as P95 latency should not be interpreted as stable production estimates.

Historical log contamination

The current sample includes older failures generated before explicit rate-limit handling.

No centralized dashboard

Monitoring currently runs through a repository script and database logs rather than a dedicated observability platform.

No distributed tracing

The current system records stage-level timing but does not yet provide distributed traces across independent services.

No automated alerting

The monitoring script reports health metrics but does not currently implement production alert delivery.

No long-term time-series aggregation

The current implementation does not provide a dedicated time-series metrics store for historical trend analysis.

21. Future Monitoring Architecture

A production monitoring stack could include:

Application
    |
    +--> Structured Logs
    |
    +--> Metrics
    |
    +--> Distributed Traces
              |
              v
       Observability Stack
              |
       +------+------+
       |             |
    Dashboard      Alerts

Possible capabilities include:

Centralized log aggregation
Time-series metrics
Distributed tracing
Service dashboards
Alert routing
Error tracking
SLO monitoring

The exact tooling should be selected according to deployment environment and operational requirements.

22. Recommended Production Metrics

The following metrics should be tracked continuously.

API
requests_total
requests_success_total
requests_failure_total
request_latency_ms
Retrieval
retrieval_latency_ms
semantic_candidates
fts_candidates
hybrid_candidates
Resolution
llm_latency_ms
grounding_rate
unsupported_step_rate
resolution_confidence
escalation_rate
Evidence
retrieved_evidence_count
authoritative_evidence_count
Provider
llm_rate_limit_total
llm_timeout_total
llm_provider_error_total
llm_retry_total
Database
db_query_latency
db_connection_usage
db_errors
23. Operational Runbook

When a sudden increase in failures is observed:

Step 1 — Check API health

Verify:

/api/v1/health
Step 2 — Check recent error types

Inspect:

error_type
error_message
Step 3 — Check provider health

Look for:

429
timeouts
provider errors
Step 4 — Check database health

Inspect:

connection usage
query latency
database availability
Step 5 — Check retrieval

Verify that:

semantic retrieval
FTS retrieval
hybrid retrieval

are returning expected candidates.

Step 6 — Check grounding

If grounding rate drops, investigate:

KB availability
Evidence retrieval
Prompt changes
LLM behavior
Validation logic
Step 7 — Compare with recent deployments

Determine whether the issue started after:

Code deployment
Model change
Prompt change
KB update
Database migration
24. Monitoring and Safe Failure

Monitoring is directly connected to system safety.

For example:

Provider Rate Limit
        |
        v
Controlled 503
        |
        v
Monitoring Log
        |
        v
Operational Alert

Similarly:

Ungrounded Resolution
        |
        v
Safety Fallback
        |
        v
Grounding Metric
        |
        v
Quality Investigation

This makes monitoring part of the system's reliability architecture rather than simply a reporting feature.

25. Final Monitoring Conclusion

The current implementation provides a useful foundation for monitoring the resolution system.

The repository already records:

Request outcomes
Latency
Evidence counts
Grounding
Confidence
Error information

The monitoring script converts these logs into an operational health summary.

The current measured development snapshot shows:

Total requests:             7
Success rate:              71.43%
Grounding rate:           100.00%
Average latency:        5190.68 ms
Median latency:         4628.31 ms
P95 latency:           10044.47 ms
Average confidence:        0.898
Average evidence:           7.60
Average authoritative:      5.00

The two failures in that historical monitoring window correspond to older provider rate-limit failures that occurred before explicit LLMRateLimitError handling was implemented.

The latest implementation therefore has a more controlled provider-failure path, and future monitoring should be performed on fresh traffic after deployment.

The next production maturity steps are:

Centralized metrics
Structured log aggregation
Distributed tracing
Automated alerting
Long-term time-series monitoring
SLO tracking
Continuous retrieval-quality monitoring
Production-scale failure analysis

The monitoring design should ultimately connect operational health with resolution quality so that the system can detect not only whether requests succeed, but whether the assistant continues to produce fast, grounded, and useful resolutions.