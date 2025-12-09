"""
Context Engine Client - Lightweight client library for agents running on Fly machines.

This package provides the Context Builder interface that agents use to build
optimized context windows for LLM calls.

Usage:
    from context_engine_client import Context as ctx
    
    # Initialize with project and agent info
    ctx = Context(project_id="...", agent_name="...")
    
    # Build complete context for LLM
    message = "what is the weather today"
    complete_context = ctx.build(message)
    
    # Use with LLM
    llm_response = llm.call(complete_context)
"""

__version__ = "0.1.0"

# Main exports will be available once builder.py is implemented
# from context_engine_client.builder import Context

__all__ = []  # Will be ["Context"] once implemented
