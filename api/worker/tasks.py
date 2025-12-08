"""
Celery tasks for agent processing.
"""
from worker.celery_app import celery_app
from worker.task_storage import save_task
from typing import Dict, Any
import logging
import importlib
import sys
import os

# Add the api directory to Python path to ensure imports work
# This is needed because Celery worker might run from a different context
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

# Load all agents to ensure they're registered and importable
from agents.loader import load_all_agents
load_all_agents()

logger = logging.getLogger(__name__)


@celery_app.task(name="worker.tasks.agent_initialization", bind=True)
def agent_initialization_task(
    self, project_id: str, context: str, agent_name: str
) -> Dict[str, Any]:
    """
    Initialize an agent task and execute its process function.
    
    Args:
        project_id: The project ID
        context: The context for the agent
        agent_name: The name of the agent to initialize
        
    Returns:
        Dictionary with task result information
    """
    try:
        logger.info(
            f"Starting agent initialization task: project_id={project_id}, "
            f"agent_name={agent_name}, task_id={self.request.id}"
        )
        
        # Update task state to STARTED (standard Celery state)
        self.update_state(
            state="STARTED",
            meta={
                "status": "processing",
                "project_id": project_id,
                "agent_name": agent_name,
                "message": f"Processing agent {agent_name} for project {project_id}",
            }
        )
        
        # Update task status in database to "processing"
        save_task(
            task_id=self.request.id,
            project_id=project_id,
            queue_name="agent_initialization_queue",
            task_type="agent_initialization",
            agent_name=agent_name,
            context=context,
            status="processing"
        )
        
        # Dynamically import the agent module and get its process function
        try:
            agent_module = importlib.import_module(f"agents.{agent_name}")
            process_func = getattr(agent_module, "process", None)
            
            if not process_func:
                raise AttributeError(f"Agent '{agent_name}' does not have a 'process' function")
            
            # Call the agent's process function
            logger.info(f"Calling process() for agent: {agent_name} with context: {context[:100] if context else 'None'}...")
            
            # Update state to show we're executing the agent
            self.update_state(
                state="STARTED",
                meta={
                    "status": "executing",
                    "project_id": project_id,
                    "agent_name": agent_name,
                    "message": f"Executing {agent_name} process function...",
                }
            )
            
            agent_result = process_func()
            
            logger.info(f"Agent {agent_name} process() returned: {agent_result}")
            
            # Build the complete result
            result = {
                "status": "completed",
                "project_id": project_id,
                "agent_name": agent_name,
                "context": context,
                "task_id": self.request.id,
                "agent_result": agent_result,
            }
            
            logger.info(f"Agent {agent_name} processing completed successfully. Result: {result}")
            
            # Save task status to database (completed)
            save_task(
                task_id=self.request.id,
                project_id=project_id,
                queue_name="agent_initialization_queue",
                task_type="agent_initialization",
                agent_name=agent_name,
                context=context,
                status="completed",
                result=result
            )
            
            # Post result to results queue for further processing
            logger.info(f"Posting result to agent_results_queue for task {self.request.id}")
            try:
                result_task = process_agent_result_task.delay(result)
                logger.info(f"✅ Result task created successfully with ID: {result_task.id}")
                
                # Result task will be saved to database when it completes (not here to avoid duplicates)
            except Exception as queue_error:
                logger.error(f"❌ Failed to post result to queue: {str(queue_error)}", exc_info=True)
                # Don't fail the main task if result posting fails
                # The result is still returned successfully
            
            logger.info(f"✅ Agent initialization task {self.request.id} completed and result posted to queue")
            return result
            
        except ImportError as e:
            error_msg = f"Could not import agent module '{agent_name}': {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except AttributeError as e:
            error_msg = f"Agent '{agent_name}' is missing required 'process' function: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        
    except Exception as e:
        logger.error(f"Error in agent initialization task: {str(e)}", exc_info=True)
        
        # Build error result with full error details as context
        error_details = {
            "original_task_id": self.request.id,
            "agent_name": agent_name,
            "original_context": context,
            "error_message": str(e),
            "error_type": type(e).__name__,
        }
        error_context = f"Agent '{agent_name}' failed: {str(e)}. Original context: {context[:200]}..."
        
        # Save task status to database (failed)
        save_task(
            task_id=self.request.id,
            project_id=project_id,
            queue_name="agent_initialization_queue",
            task_type="agent_initialization",
            agent_name=agent_name,
            context=context,
            status="failed",
            error=str(e)
        )
        
        # Create a new task with error details as context for webhook notification
        # This task will be acknowledged and removed from queue (handled by Celery)
        # The new task will send webhook notification with error details
        try:
            error_result = {
                "status": "failed",
                "project_id": project_id,
                "agent_name": agent_name,
                "context": error_context,
                "task_id": self.request.id,
                "error": str(e),
                "error_details": error_details,
            }
            
            # Post error result to results queue (this creates a new task)
            result_task = process_agent_result_task.delay(error_result)
            logger.info(f"✅ Error notification task created with ID: {result_task.id} for failed task {self.request.id}")
        except Exception as queue_error:
            logger.error(f"❌ Failed to create error notification task: {str(queue_error)}", exc_info=True)
        
        # Update task state to failure
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "failed"}
        )
        raise


@celery_app.task(name="worker.tasks.process_agent_result", bind=True)
def process_agent_result_task(self, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process completed agent results.
    This task handles the results from agent processing, such as:
    - Storing results in database
    - Sending webhooks
    - Triggering next steps in workflow
    
    Args:
        result: Dictionary containing agent processing result
        
    Returns:
        Dictionary with processing status
    """
    original_task_id = result.get("task_id") if result else None
    
    try:
        logger.info(
            f"Processing agent result task started: task_id={self.request.id}, "
            f"original_task_id={result.get('task_id')}, agent={result.get('agent_name')}"
        )
        
        # Update task state to STARTED (standard Celery state)
        self.update_state(
            state="STARTED",
            meta={
                "status": "processing",
                "original_task_id": result.get("task_id"),
                "agent_name": result.get("agent_name"),
                "message": f"Processing result for agent {result.get('agent_name')}",
            }
        )
        
        # Save task to database when it completes (includes webhook notification)
        
        status = result.get("status", "unknown")
        project_id = result.get("project_id")
        agent_name = result.get("agent_name")
        # original_task_id is already extracted at the top of the function
        
        if status == "completed":
            logger.info(
                f"Agent {agent_name} completed successfully for project {project_id}. "
                f"Result: {result.get('agent_result', {})}"
            )
            
            # TODO: Add logic here to:
            # - Send webhook notifications
            # - Trigger dependent agents/workflows
            # - Update project status
            
        elif status == "failed":
            logger.error(
                f"Agent {agent_name} failed for project {project_id}. "
                f"Error: {result.get('error', 'Unknown error')}"
            )
            
            # TODO: Add logic here to:
            # - Send failure notifications
            # - Handle retry logic if needed
        
        processed_result = {
            "status": "processed",
            "result_id": result.get("task_id"),
            "original_task_id": result.get("task_id"),
            "agent_name": agent_name,
            "project_id": project_id,
            "message": f"Result processed for agent {agent_name}",
        }
        
        # Build result to save - include both processed summary AND full original result
        # This preserves all error details (error_details, error_context, etc.)
        result_to_save = {
            "processed_summary": processed_result,
            "original_result": result,  # Preserves all error details, error_details dict, etc.
        }
        
        # Save task status to database (completed) with the full result including error details
        save_task(
            task_id=self.request.id,
            project_id=project_id,
            queue_name="agent_results_queue",
            task_type="agent_result_processing",
            agent_name=agent_name,
            status="completed",
            result=result_to_save,
            parent_task_id=original_task_id
        )
        
        logger.info(f"Agent result processing completed: {processed_result}")
        return processed_result
        
    except Exception as e:
        logger.error(f"Error processing agent result: {str(e)}", exc_info=True)
        
        # Build error info preserving original result if available
        error_info = {
            "processing_error": str(e),
            "error_type": type(e).__name__,
            "original_result": result if result else None,  # Preserve original result with error details
        }
        
        # Save task status to database (failed) with full error context
        save_task(
            task_id=self.request.id,
            project_id=result.get("project_id", "unknown") if result else "unknown",
            queue_name="agent_results_queue",
            task_type="agent_result_processing",
            agent_name=result.get("agent_name") if result else None,
            status="failed",
            error=str(e),
            result=error_info,  # Include full error info including original result
            parent_task_id=original_task_id
        )
        
        # Update task state to failure
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "failed"}
        )
        raise
