# Talkmap Telecom Conversation Corpus

## Source

The historical support conversation dataset used by this project is:

- Dataset: Talkmap Telecom Conversation Corpus
- Source: https://huggingface.co/datasets/talkmap/telecom-conversation-corpus
- Primary file: `telecom_200k.csv`
- Format: CSV
- License: MIT

## Purpose

The dataset provides historical telecom customer-support conversations
used for similarity retrieval and historical resolution analysis.

The dataset is not treated as authoritative troubleshooting guidance.
Historical agent responses are considered supporting evidence only.

Authoritative troubleshooting procedures are maintained separately in
the project's curated knowledge base.

## Schema

The source dataset contains conversation turns with fields including:

- `conversation_id`
- `speaker`
- `date_time`
- `text`

Multiple rows may belong to the same conversation.

The ingestion pipeline reconstructs ordered conversations from these turns.

## Data handling

The raw dataset is not committed to the Git repository because of its size.

Expected local location:

`data/raw/telecom_200k.csv`

The ingestion pipeline validates and processes the raw data before it is
used for retrieval or embedding generation.

Sensitive information detected during processing must be redacted before
embedding, indexing, or application logging.

## Pipeline

```text
Talkmap CSV
    ↓
Schema validation
    ↓
Conversation reconstruction
    ↓
Text normalization
    ↓
Sensitive-data redaction
    ↓
Quality validation
    ↓
Resolution eligibility
    ↓
Chunking
    ↓
Embeddings
    ↓
PostgreSQL + pgvector