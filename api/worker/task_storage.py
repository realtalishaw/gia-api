"""
Task storage utility for saving Celery task information to Supabase.
Provides redundancy by storing task metadata in the database.
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

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
            logger.info(f"✓ Task storage: Supabase client initialized ({key_type} key)")
        else:
            _supabase_client = None
            if not supabase_url:
                logger.warning("⚠ Task storage: SUPABASE_URL not found in environment")
            if not supabase_key:
                logger.warning("⚠ Task storage: SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY not found in environment")
    except ImportError:
        # Supabase client not installed, continue without it
        logger.warning("⚠ Task storage: Supabase Python client not installed. Run: pip install supabase")
        _supabase_client = None
    except Exception as e:
        # Log error but continue without Supabase
        logger.warning(f"⚠ Task storage: Could not initialize Supabase client: {e}")
        _supabase_client = None
    
    return _supabase_client


def save_task(
    task_id: str,
    project_id: str,
    queue_name: str,
    agent_name: Optional[str] = None,
    context: Optional[str] = None,
    status: str = "pending",
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> bool:
    """
    Save or update task information in Supabase.
    
    Args:
        task_id: Celery task ID (unique identifier)
        project_id: Project ID associated with the task
        queue_name: Name of the queue the task is in
        agent_name: Name of the agent (if applicable)
        context: Task context/input data
        status: Task status (pending, processing, completed, failed)
        result: Task result data (for completed tasks)
        error: Error message (for failed tasks)
        
    Returns:
        True if saved successfully, False otherwise
    """
    client = _init_supabase()
    if not client:
        logger.debug("Task storage: Supabase not configured, skipping save")
        return False
    
    try:
        # Prepare data for insert/update
        data = {
            "task_id": task_id,
            "project_id": project_id,
            "queue_name": queue_name,
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # Add optional fields
        if agent_name:
            data["agent_name"] = agent_name
        if context:
            data["context"] = context
        if result:
            data["result"] = result
        if error:
            data["error"] = error
        
        # Set timestamps based on status
        if status == "processing" and not data.get("started_at"):
            data["started_at"] = datetime.utcnow().isoformat()
        elif status in ("completed", "failed") and not data.get("completed_at"):
            data["completed_at"] = datetime.utcnow().isoformat()
        
        # Check if task exists first
        existing = client.table("tasks").select("task_id").eq("task_id", task_id).execute()
        
        if existing.data and len(existing.data) > 0:
            # Task exists - update it
            response = client.table("tasks").update(data).eq("task_id", task_id).execute()
        else:
            # Task doesn't exist - insert it
            # Don't set updated_at on initial insert (let database default handle it)
            insert_data = data.copy()
            if "updated_at" in insert_data:
                del insert_data["updated_at"]
            response = client.table("tasks").insert(insert_data).execute()
        
        logger.debug(f"Task storage: Saved task {task_id} to database (status: {status})")
        return True
        
    except Exception as e:
        logger.error(f"Task storage: Failed to save task {task_id} to database: {e}", exc_info=True)
        return False


def update_task_status(
    task_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Update task status in the database.
    
    Args:
        task_id: Celery task ID
        status: New status (pending, processing, completed, failed)
        result: Task result data (for completed tasks)
        error: Error message (for failed tasks)
        meta: Additional metadata to store
        
    Returns:
        True if updated successfully, False otherwise
    """
    client = _init_supabase()
    if not client:
        logger.debug("Task storage: Supabase not configured, skipping update")
        return False
    
    try:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # Set timestamps based on status
        if status == "processing":
            update_data["started_at"] = datetime.utcnow().isoformat()
        elif status in ("completed", "failed"):
            update_data["completed_at"] = datetime.utcnow().isoformat()
        
        # Add optional fields
        if result:
            update_data["result"] = result
        if error:
            update_data["error"] = error
        if meta:
            # Merge meta into result or store separately
            if "result" in update_data:
                if isinstance(update_data["result"], dict):
                    update_data["result"].update(meta)
                else:
                    update_data["result"] = {"data": update_data["result"], **meta}
            else:
                update_data["result"] = meta
        
        response = client.table("tasks").update(update_data).eq("task_id", task_id).execute()
        
        logger.debug(f"Task storage: Updated task {task_id} status to {status}")
        return True
        
    except Exception as e:
        logger.error(f"Task storage: Failed to update task {task_id} status: {e}", exc_info=True)
        return False
