"""
Celery tasks for context ingestion.
"""
from api.context_engine.worker.celery_app import celery_app
from api.context_engine.worker.context_storage import save_context_data
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="context_engine.worker.tasks.ingest_context_data", bind=True)
def ingest_context_data_task(self, *args, **kwargs) -> Dict[str, Any]:
    """
    Ingest context data and save it to the context_lake table.
    
    Accepts both positional arguments (from Celery invocation) and keyword
    arguments (from direct function calls in tests). This prevents the
    "multiple values for argument" error when callers provide `project_id`
    and `data` as keywords while Celery passes them positionally.
    
    Args:
        project_id: Project ID associated with the context data
        data: Flexible dictionary/JSON data to store (required)
        agent_name: Optional name of the agent that generated this data
        data_type: Optional type/category of the data (e.g., "log", "event", "result")
        metadata: Optional metadata dictionary
        
    Returns:
        Dictionary with ingestion status and result information
    """
    # Normalize parameters from positional (Celery) or keyword (tests) inputs
    project_id = kwargs.pop("project_id", None)
    data = kwargs.pop("data", None)
    agent_name = kwargs.pop("agent_name", None)
    data_type = kwargs.pop("data_type", None)
    metadata = kwargs.pop("metadata", None)

    # If values weren't supplied via kwargs, fall back to positional order
    # expected by Celery: project_id, data, agent_name, data_type, metadata.
    positional_args = list(args)

    # Allow tests to inject a mock task context as the first positional arg
    task_context = self
    if positional_args and hasattr(positional_args[0], "update_state"):
        task_context = positional_args.pop(0)
    if project_id is None and positional_args:
        project_id = positional_args.pop(0)
    if data is None and positional_args:
        data = positional_args.pop(0)
    if agent_name is None and positional_args:
        agent_name = positional_args.pop(0)
    if data_type is None and positional_args:
        data_type = positional_args.pop(0)
    if metadata is None and positional_args:
        metadata = positional_args.pop(0)
    logger.info("=" * 80)
    logger.info(f"🚀 CONTEXT INGESTION TASK STARTED")
    logger.info(f"   Task ID: {getattr(getattr(task_context, 'request', None), 'id', None)}")
    logger.info(f"   Project ID: {project_id}")
    logger.info(f"   Agent Name: {agent_name or 'N/A'}")
    logger.info(f"   Data Type: {data_type or 'N/A'}")
    logger.info(f"   Data Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
    logger.info("=" * 80)
    
    try:
        # Validate required inputs
        if not project_id:
            raise ValueError("project_id is required")
        
        if not data:
            raise ValueError("data is required and cannot be empty")
        
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary/JSON object")
        
        # Update task state to STARTED
        task_context.update_state(
            state="STARTED",
            meta={
                "status": "processing",
                "project_id": project_id,
                "agent_name": agent_name,
                "data_type": data_type,
                "message": f"Processing context ingestion for project {project_id}",
            }
        )
        
        # Save context data to Supabase
        logger.info(f"Saving context data to database for project {project_id}")
        save_success = save_context_data(
            project_id=project_id,
            data=data,
            agent_name=agent_name,
            data_type=data_type,
            metadata=metadata,
        )
        
        if not save_success:
            error_msg = f"Failed to save context data to database for project {project_id}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        logger.info(f"✅ Successfully saved context data to database for project {project_id}")
        
        # Build success result
        result = {
            "status": "completed",
            "project_id": project_id,
            "agent_name": agent_name,
            "data_type": data_type,
            "task_id": getattr(getattr(task_context, "request", None), "id", None),
            "message": f"Context data ingested successfully for project {project_id}",
        }
        
        logger.info(f"✅ Context ingestion task {self.request.id} completed successfully")
        
        return result
        
    except ValueError as e:
        # Validation error - log and re-raise
        error_msg = f"Validation error in context ingestion task: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Update task state to failure
        task_context.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "status": "failed",
                "error_type": "validation_error",
            }
        )
        raise ValueError(error_msg) from e
        
    except Exception as e:
        # General error - log and re-raise
        error_msg = f"Error in context ingestion task: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Update task state to failure
        task_context.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "status": "failed",
                "error_type": type(e).__name__,
            }
        )
        raise
