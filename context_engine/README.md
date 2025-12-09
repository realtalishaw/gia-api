# Context Engine

The Context Engine is the core brain of the agent system. It manages the context lake, processes ingested data, and provides federated query capabilities.

## Overview

The Context Engine runs as a separate service on Railway, independent of the FastAPI application. It handles:

- **Context Lake**: Federated query engine that queries across vector DB, memory store, and graph DB
- **Context Worker**: Background worker that processes the ingestion queue from agents
- **Curator**: Background process that analyzes logs and cleans up redundant/duplicate context
- **Reflector**: Background process that optimizes memory and creates compacted pointers

## Architecture

```
context_engine/
├── lake/          # Federated query engine
├── worker/         # Ingestion queue processor
├── curator/        # Background cleanup
└── reflector/      # Memory optimization
```

## Components

### Context Lake
The federated query engine that allows querying across all context stores as if they were a single database. Handles permissions and provides unified access to:
- Vector database (embeddings, semantic search)
- Memory store (structured data, key-value)
- Graph database (relationships, knowledge graph)

### Context Worker
Processes the ingestion queue. When agents call `context.ingest()`, data is queued and the worker:
1. Archives raw data to SQL database (never lose data)
2. Routes to appropriate adapters based on policies
3. Handles failures and retries

### Curator
Background process that analyzes logs asynchronously:
- Identifies redundant/duplicate context (e.g., "404 error logged 50 times")
- Compacts duplicates into single entries with counts
- Adds lessons to playbook when agents fail
- Prunes irrelevant context

### Reflector
Background process that optimizes memory:
- Analyzes context usage patterns
- Creates compacted memory pointers
- Optimizes advice and recommendations
- Writes optimized pointers back to storage

## Deployment

The Context Engine runs on Railway as a separate service from the FastAPI API.
