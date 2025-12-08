"""
Task storage utility for saving Celery task information to Supabase.
Each task is saved as a separate record for complete history and redundancy.
Also sends webhook notifications when tasks are saved.
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
    task_type: str = "agent_initialization",
    agent_name: Optional[str] = None,
    context: Optional[str] = None,
    status: str = "pending",
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    parent_task_id: Optional[str] = None,
) -> bool:
    """
    Save a new task record to Supabase.
    Each task is saved as a separate record for complete history.
    
    Args:
        task_id: Celery task ID (unique identifier for this task instance)
        project_id: Project ID associated with the task
        queue_name: Name of the queue the task is in
        task_type: Type of task ('agent_initialization' or 'agent_result_processing')
        agent_name: Name of the agent (if applicable)
        context: Task context/input data
        status: Task status (pending, processing, completed, failed)
        result: Task result data (for completed tasks)
        error: Error message (for failed tasks)
        parent_task_id: ID of the parent task (for result processing tasks)
        
    Returns:
        True if saved successfully, False otherwise
    """
    client = _init_supabase()
    if not client:
        logger.debug("Task storage: Supabase not configured, skipping save")
        return False
    
    try:
        # Prepare data for insert
        data = {
            "task_id": task_id,
            "project_id": project_id,
            "queue_name": queue_name,
            "task_type": task_type,
            "status": status,
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
        if parent_task_id:
            data["parent_task_id"] = parent_task_id
        
        # Set timestamps based on status
        if status == "processing":
            data["started_at"] = datetime.utcnow().isoformat()
        elif status in ("completed", "failed"):
            data["completed_at"] = datetime.utcnow().isoformat()
        
        # Always insert a new record (no checking for existing)
        response = client.table("tasks").insert(data).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Task storage: ✅ Saved task {task_id} ({task_type}) to database with status: {status}")
            
            # Send webhook notification after successful save
            logger.info(f"Task storage: Attempting to send webhook for task {task_id}")
            try:
                from worker.webhook_client import send_task_created_webhook
                webhook_sent = send_task_created_webhook(
                    task_id=task_id,
                    project_id=project_id,
                    queue_name=queue_name,
                    task_type=task_type,
                    status=status,
                    agent_name=agent_name,
                    context=context,
                    parent_task_id=parent_task_id,
                    result=result,
                    error=error,
                )
                if webhook_sent:
                    logger.info(f"Task storage: ✅ Webhook sent successfully for task {task_id}")
                else:
                    logger.info(f"Task storage: ⚠️ Webhook not sent for task {task_id} (not configured or failed)")
            except Exception as webhook_error:
                # Don't fail the task save if webhook fails - just log it
                logger.warning(f"Task storage: ❌ Exception sending webhook for task {task_id}: {webhook_error}", exc_info=True)
            
            return True
        else:
            logger.warning(f"Task storage: ⚠️ Insert returned no data for task {task_id}")
            return False
        
    except Exception as e:
        logger.error(f"Task storage: ❌ Failed to save task {task_id} to database: {e}", exc_info=True)
        return False
