"""
Context storage utility for saving ingested context data to Supabase.
Stores flexible JSON data in the context_lake table.
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global Supabase client (initialized lazily)
_supabase_client = None


def _init_supabase():
    """Initialize Supabase client if credentials are available"""
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        # Prefer service role key for server-side operations (bypasses RLS)
        # Fall back to anon key if service role is not available
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if supabase_url and supabase_key:
            from supabase import create_client, Client
            _supabase_client = create_client(supabase_url, supabase_key)
            key_type = "service role" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "anon"
            logger.info(f"✓ Context storage: Supabase client initialized ({key_type} key)")
        else:
            _supabase_client = None
            if not supabase_url:
                logger.warning("⚠ Context storage: SUPABASE_URL not found in environment")
            if not supabase_key:
                logger.warning("⚠ Context storage: SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY not found in environment")
    except ImportError:
        # Supabase client not installed, continue without it
        logger.warning("⚠ Context storage: Supabase Python client not installed. Run: pip install supabase")
        _supabase_client = None
    except Exception as e:
        # Log error but continue without Supabase
        logger.warning(f"⚠ Context storage: Could not initialize Supabase client: {e}")
        _supabase_client = None
    
    return _supabase_client


def save_context_data(
    project_id: str,
    data: Dict[str, Any],
    agent_name: Optional[str] = None,
    data_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Save ingested context data to Supabase context_lake table.
    
    Args:
        project_id: Project ID associated with the context data
        data: Flexible dictionary/JSON data to store (will be stored as JSONB)
        agent_name: Optional name of the agent that generated this data
        data_type: Optional type/category of the data (e.g., "log", "event", "result")
        metadata: Optional metadata dictionary (will be stored as JSONB)
        
    Returns:
        True if saved successfully, False otherwise
    """
    client = _init_supabase()
    if not client:
        logger.debug("Context storage: Supabase not configured, skipping save")
        return False
    
    try:
        # Prepare data for insert
        insert_data = {
            "project_id": project_id,
            "raw_data": data,  # Store as JSONB
        }
        
        # Add optional fields
        if agent_name:
            insert_data["agent_name"] = agent_name
        if data_type:
            insert_data["data_type"] = data_type
        if metadata:
            insert_data["metadata"] = metadata
        
        # Insert into context_lake table
        response = client.table("context_lake").insert(insert_data).execute()
        
        if response.data and len(response.data) > 0:
            record_id = response.data[0].get("id")
            logger.info(
                f"Context storage: ✅ Saved context data to database "
                f"(id: {record_id}, project_id: {project_id}, "
                f"agent_name: {agent_name or 'N/A'}, data_type: {data_type or 'N/A'})"
            )
            return True
        else:
            logger.warning(f"Context storage: ⚠️ Insert returned no data for project {project_id}")
            return False
        
    except Exception as e:
        logger.error(
            f"Context storage: ❌ Failed to save context data to database "
            f"(project_id: {project_id}): {e}",
            exc_info=True
        )
        return False
