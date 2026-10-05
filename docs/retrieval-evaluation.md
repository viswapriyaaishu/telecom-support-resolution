# Retrieval Evaluation

## 1. Purpose

The retrieval layer is one of the most important components of the Intelligent Support Ticket Resolution Assistant.

The objective is to determine whether a customer's complaint can be matched with relevant historical support cases and knowledge-base information even when the customer's wording differs from previous tickets.

The evaluation compares three retrieval strategies:

1. Semantic vector retrieval
2. PostgreSQL Full-Text Search (FTS)
3. Hybrid retrieval using Reciprocal Rank Fusion (RRF)

The evaluation uses a manually curated golden set of 30 support queries with known relevant historical conversation IDs.

---

## 2. Evaluation Dataset

The evaluation dataset is stored at:

```text
data/evaluation/golden_retrieval.json
```

---

## 3. Retrieval Methods

### 3.1 Semantic Retrieval

Semantic retrieval converts the complaint into an embedding using:

```
BAAI/bge-large-en-v1.5
```

The embedding dimension is:

```
1024
```

The resulting vector is compared against conversation chunk embeddings stored in PostgreSQL using pgvector.

The database uses an HNSW index with cosine distance:

```
ix_conversation_chunks_embedding_hnsw
```

Semantic retrieval is particularly useful when the customer and historical ticket use different wording for the same underlying problem.

For example:

```
Customer:
"My broadband keeps dropping every evening."

Historical ticket:
"Internet connection becomes unstable during the night."
```

The wording is different, but the underlying issue may be semantically similar.

---

## 4. PostgreSQL Full-Text Search

The second retrieval strategy uses PostgreSQL Full-Text Search.

The system uses a GIN index:

```
ix_conversation_chunks_text_fts_gin
```

The indexed representation is based on:

```
to_tsvector('english', text)
```

FTS provides lexical matching and can be useful when important technical terminology appears explicitly in both the query and historical conversation.

For example:

```
"broadband router disconnecting"
```

may benefit from lexical matches containing:

```
broadband
router
disconnecting
```

However, broad OR-style lexical searches can produce large candidate sets, increasing ranking and heap-processing costs.

---

## 5. Hybrid Retrieval

The third strategy combines semantic and lexical retrieval.

The system first obtains candidates from:

```
Semantic Retrieval
        +
PostgreSQL FTS
```

The candidate rankings are then combined using Reciprocal Rank Fusion.

Conceptually:

```
                Query
                  |
        +---------+---------+
        |                   |
        v                   v
 Semantic Search          FTS Search
        |                   |
        +---------+---------+
                  |
                  v
             RRF Ranking
                  |
                  v
          Hybrid Results
```

RRF is useful because the two retrieval systems provide different signals.

Semantic retrieval captures conceptual similarity, while FTS captures explicit lexical overlap.

---

## 6. Evaluation Metrics

The evaluation uses four ranking metrics.

### Recall@5

Recall@5 measures whether at least one relevant conversation appears within the first five retrieved results.

A higher value means the system is more likely to surface a useful historical case immediately.

### Recall@10

Recall@10 measures whether relevant conversations appear within the first ten retrieved results.

This provides a slightly larger retrieval window than Recall@5.

### Mean Reciprocal Rank (MRR)

MRR measures how early the first relevant result appears.

If the first relevant result is ranked first:

```
Reciprocal Rank = 1
```

If it appears at rank 5:

```
Reciprocal Rank = 1/5
```

The final MRR is the mean reciprocal rank across all evaluation queries.

MRR therefore rewards systems that place a relevant result very high in the ranking.

### nDCG@10

Normalized Discounted Cumulative Gain at 10 measures the quality of the ranking within the top ten results.

It gives more importance to relevant results appearing near the top of the ranking.

This is useful because retrieval quality is not only about whether a relevant ticket appears, but also about whether it appears early enough for a support agent to use it efficiently.

---

## 7. Baseline Evaluation

The initial evaluation was performed before restricting semantic retrieval to resolved conversations.

The baseline results were:

| Method     | Recall@5 | Recall@10 | MRR    | nDCG@10 |
| ---------- | -------- | --------- | ------ | ------- |
| Semantic   | 0.1500   | 0.1833    | 0.1031 | 0.1203  |
| FTS        | 0.0500   | 0.0833    | 0.0250 | 0.0373  |
| Hybrid RRF | 0.1333   | 0.2000    | 0.0897 | 0.1169  |

The baseline demonstrated that semantic retrieval provided a substantially stronger signal than FTS for this evaluation set.

However, hybrid retrieval did not consistently outperform semantic retrieval.

This motivated investigation into the quality and resolution status of the historical conversation corpus.

---

## 8. Resolved-Conversation Filtering

The source dataset contains conversations with several resolution states.

The observed conversation status distribution includes:

```
UNKNOWN      138,722
ESCALATED     61,538
UNRESOLVED    15,316
RESOLVED       4,535
```

The retrieval system was therefore changed to restrict historical semantic retrieval to:

```
RESOLVED
```

conversations.

The reasoning is that resolved conversations represent completed support cases with known outcomes and are therefore more useful as examples for resolution assistance.

All 40 unique relevant conversation IDs in the golden retrieval set were confirmed to be in the RESOLVED state.

---

## 9. Evaluation After Resolved Filtering

After restricting semantic retrieval to resolved conversations, the results became:

| Method     | Recall@5 | Recall@10 | MRR    | nDCG@10 |
| ---------- | -------- | --------- | ------ | ------- |
| Semantic   | 0.3000   | 0.3000    | 0.2944 | 0.2663  |
| FTS        | 0.0500   | 0.0833    | 0.0250 | 0.0373  |
| Hybrid RRF | 0.3333   | 0.3500    | 0.2844 | 0.2740  |

These results are the current measured retrieval results for the 30-query evaluation set.

---

## 10. Results Comparison

The semantic retrieval improvement after resolved-only filtering was significant.

### Recall@5

Semantic retrieval improved from:

```
0.1500 → 0.3000
```

This represents a doubling of Recall@5.

### Recall@10

Semantic retrieval improved from:

```
0.1833 → 0.3000
```

This indicates that restricting the candidate population to resolved conversations substantially improved the relevance of the retrieved results.

### MRR

Semantic MRR improved from:

```
0.1031 → 0.2944
```

This is approximately a 2.86× improvement.

The result indicates that relevant historical cases are appearing substantially earlier in the ranking.

### nDCG@10

Semantic nDCG@10 improved from:

```
0.1203 → 0.2663
```

This is approximately a 2.22× improvement.

This indicates that the ranking quality within the top ten results improved considerably.

---

## 11. Current Best Retrieval Strategy

Based on the current evaluation:

**Best Recall@5:** Hybrid RRF = 0.3333

**Best Recall@10:** Hybrid RRF = 0.3500

**Best MRR:** Semantic = 0.2944

**Best nDCG@10:** Hybrid RRF = 0.2740

Therefore, hybrid retrieval currently provides the strongest overall recall and top-10 ranking quality.

Semantic retrieval has a slightly higher MRR, meaning that when it finds a relevant result, it places the first relevant result slightly earlier on average.

---

## 12. Interpretation

The evaluation demonstrates that the retrieval methods provide complementary behavior.

### Semantic retrieval

Semantic retrieval is the strongest individual retrieval strategy in this evaluation.

It is particularly useful when:

- Wording differs
- Customers describe symptoms indirectly
- Similar concepts use different terminology
- Exact keyword overlap is weak

### FTS

FTS alone performs poorly on the current golden set.

Current results:

```
Recall@5  = 0.0500
Recall@10 = 0.0833
MRR       = 0.0250
nDCG@10   = 0.0373
```

This does not mean FTS is unnecessary.

Lexical retrieval remains useful as a complementary signal, particularly for technical terms, product names, error messages, and explicit terminology.

### Hybrid RRF

Hybrid retrieval benefits from both retrieval signals.

Current results:

```
Recall@5  = 0.3333
Recall@10 = 0.3500
MRR       = 0.2844
nDCG@10   = 0.2740
```

The hybrid system achieves the best Recall@5, Recall@10, and nDCG@10 among the evaluated approaches.

This supports the architectural decision to retain both semantic and lexical retrieval rather than relying exclusively on one method.

---

## 13. Why Resolved Filtering Matters

A major observation from the evaluation was that retrieval quality depends not only on the retrieval algorithm but also on the quality of the candidate corpus.

The source dataset contains many conversations that are:

- Unknown
- Escalated
- Unresolved

Including these cases increases the probability of retrieving incomplete or operationally less useful examples.

Restricting retrieval to resolved conversations creates a more useful retrieval population for a resolution assistant.

The experiment therefore demonstrates an important production principle:

> Retrieval quality is a combination of model quality, indexing strategy, query strategy, and candidate-data quality.

---

## 14. HNSW Verification

The semantic retrieval database uses an HNSW index.

The query plan was inspected using:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, conversation_id, text
FROM conversation_chunks
WHERE embedding IS NOT NULL
ORDER BY embedding <=> (
    SELECT embedding
    FROM conversation_chunks
    WHERE embedding IS NOT NULL
    LIMIT 1
)
LIMIT 10;
```

The query plan confirmed:

```
Index Scan using ix_conversation_chunks_embedding_hnsw
```

with:

```
Order By: (embedding <=> (InitPlan 1).col1)
```

The measured execution time was:

```
114.255 ms
```

The PostgreSQL index statistics also confirmed index usage:

```
idx_scan       = 1
idx_tup_read   = 10
idx_tup_fetch  = 10
```

This verifies that vector retrieval is using the intended HNSW index rather than performing a full sequential scan.

---

## 15. Full-Text Search Performance

The PostgreSQL FTS experiment also demonstrated the importance of query selectivity.

A broad OR-style FTS query was initially measured at approximately:

```
138,560 ms
```

After adding the GIN index, the broad query improved to approximately:

```
38,977 ms
```

This represents a substantial improvement, but the query remained expensive because broad lexical conditions can match very large numbers of rows.

More selective AND-style searches were much faster.

Examples observed during evaluation included:

```
broadband disconnecting router   ≈ 1.38 ms
broadband router                 ≈ 11.5 ms
```

A full meaningful AND query returning zero rows was also measured at approximately:

```
2.4 ms
```

The experiment demonstrated that an index can accelerate candidate lookup, but query selectivity and downstream ranking cost still matter.

---

## 16. Retrieval Smoke Test

A representative complaint was used to verify the complete hybrid retrieval path:

> My broadband keeps disconnecting every evening and restarting the router does not fix it.

The hybrid retrieval execution completed in approximately:

```
70.69 ms
```

and returned five results.

The retrieved candidates included examples related to:

- Home device disconnections
- Broadband/router restart issues
- Wi-Fi drops
- Mobile broadband router problems
- Broadband slowness
- Router resets

This demonstrates that the hybrid retrieval pipeline is operational and able to surface multiple related historical patterns for a natural-language complaint.

---

## 17. Embedding Coverage

The conversation chunk dataset currently contains:

```
229,652 chunks
```

Embedding verification showed:

```
Total:    229,652
Embedded: 229,652
Missing:        0
```

The embedding export script subsequently reported:

```
Exported: 0 chunks
```

This indicates that there were no remaining chunks requiring embedding export.

The embedding pipeline therefore currently has complete embedding coverage for the indexed conversation chunks.

---

## 18. Evaluation Reproducibility

The retrieval evaluation can be reproduced using:

```
python .\scripts\evaluate_retrieval.py
```

The evaluation script:

1. Loads the golden retrieval dataset.
2. Loads the embedding model.
3. Generates query embeddings.
4. Runs semantic retrieval.
5. Runs FTS retrieval.
6. Runs hybrid retrieval.
7. Computes ranking metrics.
8. Prints the comparative results.

The golden dataset is stored separately from the retrieval implementation so that retrieval changes can be evaluated against a stable reference set.

---

## 19. Evaluation Limitations

The current evaluation has several limitations.

### Limited query count

The golden set currently contains:

```
30 queries
```

This is sufficient for an initial evaluation but is not large enough to represent every possible telecom support scenario.

### Golden-set coverage

The current golden set focuses on known relevant conversation IDs.

It does not represent the complete diversity of real-world customer complaints.

### Dataset quality

The evaluation depends on the quality of the historical conversation dataset.

Incorrect, incomplete, or poorly resolved historical conversations can affect retrieval measurements.

### Single embedding model

The current semantic evaluation uses:

```
BAAI/bge-large-en-v1.5
```

Other embedding models have not been systematically compared in this evaluation.

### No large-scale relevance annotation

The current evaluation uses a manually constructed golden set rather than a large professionally annotated relevance dataset.

---

## 20. Future Retrieval Improvements

Potential improvements include:

### Larger golden evaluation set

Expand the evaluation set across:

- Connectivity
- Mobile
- Billing
- Account
- Outage
- Device issues
- Authentication
- Service activation
- Cancellation
- Plan changes

### Hard-negative evaluation

Add difficult examples where tickets share terminology but describe different underlying problems.

This would test whether semantic retrieval can distinguish closely related issues.

### Retrieval threshold tuning

Evaluate different:

- Semantic similarity thresholds
- FTS candidate limits
- RRF weights
- Top-K values

### Reranking

A dedicated reranking model could be introduced after initial candidate retrieval.

Potential pipeline:

```
Vector + FTS
     |
     v
Top-N candidates
     |
     v
Cross-encoder / reranker
     |
     v
Final Top-K
```

### Query expansion

The system could generate controlled query variants for:

- Product terminology
- Technical synonyms
- Common customer wording
- Abbreviations

### Feedback-driven evaluation

Support agents could provide relevance feedback on retrieved historical cases.

That feedback could become additional evaluation data for future retrieval improvements.

---

## 21. Final Evaluation Conclusion

The current retrieval experiments support the following architectural conclusions:

1. Semantic retrieval is substantially stronger than standalone FTS for the current evaluation set.
2. Restricting semantic retrieval to resolved conversations significantly improves retrieval quality.
3. Hybrid RRF retrieval currently provides the best Recall@5, Recall@10, and nDCG@10.
4. Semantic retrieval has the highest MRR in the current evaluation.
5. HNSW indexing is successfully being used for vector search.
6. GIN indexing substantially improves PostgreSQL FTS performance.
7. FTS remains valuable as a complementary lexical retrieval signal.
8. Candidate-data quality has a major impact on retrieval quality.
9. The current 30-query golden set provides a reproducible baseline for future improvements.
10. Further optimization should be driven by measured evaluation results rather than isolated latency or ranking observations.

The retrieval layer is therefore suitable as the foundation for the current resolution assistant while leaving clear opportunities for larger-scale evaluation, reranking, query expansion, and feedback-driven optimization.