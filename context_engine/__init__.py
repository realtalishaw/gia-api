"""
Context Engine - The core brain of the agent system.

The Context Engine manages the context lake, processes ingested data,
and provides federated query capabilities across vector DB, memory, and graph stores.

Components:
- lake: Federated query engine that queries across all context stores
- worker: Background worker that processes ingestion queue
- curator: Background process that cleans up redundant/duplicate context
- reflector: Background process that optimizes and compacts memory
"""

__version__ = "0.1.0"
