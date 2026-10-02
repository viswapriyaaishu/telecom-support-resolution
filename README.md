# Intelligent Support Ticket Resolution Assistant

A production-oriented semantic support ticket resolution platform for a telecom customer support desk.

## Overview

Customer support agents often need to search large volumes of historical tickets and knowledge-base documentation to identify how similar issues were previously resolved.

Traditional keyword-based search can miss semantically similar complaints that use different terminology.

This project addresses that problem using semantic retrieval, hybrid search, structured complaint analysis, and retrieval-augmented generation (RAG).

The system analyzes a customer complaint, identifies the relevant issue context, retrieves similar historical support conversations and authoritative telecom knowledge-base content, and generates evidence-grounded resolution guidance with verifiable citations.

## Core Capabilities

- Complaint intent and context analysis
- Semantic retrieval of historical support conversations
- PostgreSQL full-text search
- Hybrid retrieval with Reciprocal Rank Fusion
- Curated telecom knowledge base
- Retrieval-augmented generation
- Grounded resolution recommendations
- Verifiable source citations
- Abstention when sufficient evidence is unavailable
- Agent feedback and evaluation

## Architecture

The system is organized around clear application and business-service boundaries.

```text
Support Agent
      |
      v
Next.js Frontend
      |
      v
FastAPI Backend
      |
      +----------------------+----------------------+
      |                      |                      |
      v                      v                      v
Intelligence             Retrieval             Resolution
      |                      |                      |
      |                Vector + FTS                |
      |                      |                      |
      +----------------------+----------------------+
                             |
                             v
                    PostgreSQL + pgvector
                             ^
                             |
                    Data Ingestion Pipeline
                             ^
                             |
                 Talkmap Telecom Corpus

                 Curated Telecom Knowledge Base
                             |
                             v
                    Authoritative Evidence