# Context Engine Client

Lightweight client library for agents running on Fly machines. Provides the Context Builder interface that agents use to build optimized context windows for LLM calls.

## Overview

The Context Engine Client is packaged into the Docker image that Fly machines use. It provides a simple interface for agents to:

- Build optimized context windows from the context lake
- Handle real-time summarization, compaction, and pruning
- Query federated context stores (vector DB, memory, graph DB)

## Installation

The client is packaged into the Docker image used by Fly machines. Agents don't need to install it separately.

## Usage

```python
from context_engine_client import Context as ctx

# Initialize with project and agent info
ctx = Context(project_id="project_123", agent_name="developer")

# Build complete context for LLM
message = "what is the weather today"
complete_context = ctx.build(message)

# Use with LLM
llm_response = llm.call(complete_context)
```

## Components

### Context Builder (`builder.py`)
The main interface that agents use. Handles:
- Querying the federated context lake
- Real-time token management
- Summarization when approaching token limits
- Compaction by creating pointers
- Pruning irrelevant context
- Building complete prompts (system message, tools, history, context)

### Query Client (`query.py`)
Federates queries across multiple service APIs:
- Vector DB API (semantic search)
- Memory Store API (structured data)
- Graph DB API (relationships)
- Combines results into unified context

### Decision Engine (`decision_engine.py`)
AI-powered decision making for context optimization:
- Decides when to summarize
- Decides when to compact
- Decides what to prune
- Decides what context to retrieve from lake

## How It Works

1. Agent calls `ctx.build(message)`
2. Context Builder queries federated context lake via `ctx.query()`
3. Decision Engine analyzes current context and lake results
4. Applies real-time optimizations (summarize, compact, prune)
5. Returns complete, optimized context ready for LLM

## Connection to Context Lake

The client connects to the context lake by making API calls to individual services:
- Vector DB service API
- Memory store service API
- Graph DB service API

The `query()` method federates these calls and combines results.
