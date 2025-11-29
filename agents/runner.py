"""
Agent Runner (Worker).

Consumes messages from RabbitMQ queues and executes agent tasks.
Adapted from spark-api/worker.py
"""
import asyncio
import aio_pika
import json
import logging
import colorlog
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from supabase import create_client
import importlib
from enum import Enum
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.phase_config import PhaseConfig
from orchestrator.task_state_manager import TaskStatus
from orchestrator.status_updates import StatusUpdateHelper

# Load environment variables
load_dotenv()

# Configure colored logging
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize Supabase client
# TODO: Uncomment when Supabase is set up
# supabase = create_client(
#     os.getenv("SUPABASE_URL", ""),
#     os.getenv("SUPABASE_KEY", "")
# )
supabase = None

# Initialize status update helper
# TODO: Uncomment when Supabase is set up
# status_updates = StatusUpdateHelper(supabase)
status_updates = None


async def update_task_status(
    task_id: str,
    status: str,
    result: dict,
    project_id: str,
    error_message: str = None,
    success_message: str = None
):
    """Helper function to update task status and create activity update."""
    try:
        # TODO: Uncomment when Supabase is set up
        # Update task with result
        # update_data = {"output_result": result}
        # if status:
        #     update_data["status"] = status
        #     
        # supabase.table('tasks') \
        #     .update(update_data) \
        #     .eq('id', task_id) \
        #     .execute()
        
        logger.info(f"Task {task_id} status: {status} - {success_message or error_message}")
        
        # Create activity update
        # TODO: Uncomment when Supabase is set up
        # if status == TaskStatus.FAILED.value:
        #     await status_updates.create_error(
        #         project_id=project_id,
        #         message=error_message or "Task failed",
        #         task_id=task_id
        #     )
        # elif status == TaskStatus.COMPLETED.value:
        #     await status_updates.create_success(
        #         project_id=project_id,
        #         message=success_message or "Task completed successfully",
        #         task_id=task_id
        #     )
    except Exception as e:
        logger.error(f"Error updating task status: {str(e)}", exc_info=True)


async def process_task(task_data: dict):
    """Process a task by importing and executing the appropriate agent module."""
    try:
        logger.info(f"Starting to process task: {json.dumps(task_data, indent=2)}")
        
        # Get task details
        # TODO: Uncomment when Supabase is set up
        # task_details = supabase.table('tasks') \
        #     .select("*") \
        #     .eq('id', task_data['task_id']) \
        #     .execute()
        #
        # if not task_details.data:
        #     raise ValueError(f"Task {task_data['task_id']} not found")
        #
        # current_task = task_details.data[0]
        
        # Dummy task for now
        current_task = {
            'id': task_data['task_id'],
            'type': task_data.get('type', 'research_market'),
            'status': 'pending',
            'agent_role': task_data.get('agent_role', 'researcher'),
            'project_id': task_data['project_id']
        }
        
        # Verify task is in a state that allows execution
        if current_task['status'].lower() not in [status.value.lower() for status in TaskStatus]:
            logger.error(f"Invalid task status: '{current_task['status']}'")
            raise ValueError(f"Task has invalid status: {current_task['status']}")
            
        # Check if task can be executed (allow both pending and failed tasks)
        if current_task['status'].lower() not in [
            TaskStatus.PENDING.value.lower(),
            TaskStatus.FAILED.value.lower(),
            TaskStatus.ERROR.value.lower()
        ]:
            raise ValueError(f"Task {task_data['task_id']} cannot be executed. Current status: {current_task['status']}")

        # Update task status to IN_PROGRESS
        try:
            logger.info(f"Updating task status to IN_PROGRESS: {task_data['task_id']}")
            # TODO: Uncomment when Supabase is set up
            # supabase.table('tasks') \
            #     .update({
            #         "status": TaskStatus.IN_PROGRESS.value,
            #         "updated_at": datetime.utcnow().isoformat()
            #     }) \
            #     .eq('id', task_data['task_id']) \
            #     .execute()
        except Exception as e:
            error_message = f"Failed to update task status: {str(e)}"
            # TODO: Uncomment when Supabase is set up
            # await status_updates.create_error(
            #     project_id=task_data['project_id'],
            #     message=error_message,
            #     task_id=task_data['task_id']
            # )
            logger.error(error_message)
            raise ValueError(error_message)

        # Get the task type and agent type
        task_type = current_task['type'].lower()
        agent_role = current_task.get('agent_role', PhaseConfig.get_agent_for_task(task_type))
        
        # Create initial activity update
        # TODO: Uncomment when Supabase is set up
        # await status_updates.create_progress(
        #     project_id=task_data['project_id'],
        #     message=f"Starting task: {task_type}",
        #     agent_role=agent_role,
        #     task_id=task_data['task_id']
        # )
        logger.info(f"Starting task: {task_type} with agent: {agent_role}")
        
        # Import and execute the agent module
        try:
            module_path = f"agents.definitions.{agent_role}"
            logger.info(f"Importing agent module: {module_path}")
            agent_module = importlib.import_module(module_path)
            
            # Execute the agent
            logger.info(f"Executing agent: {agent_role} for task: {task_type}")
            result = await agent_module.execute(task_data)
            logger.info(f"Agent execution result: {json.dumps(result, indent=2)}")
            
            if not result.get('success', False):
                # Agent returned failure
                await update_task_status(
                    task_id=task_data['task_id'],
                    status=TaskStatus.FAILED.value,
                    result=result,
                    project_id=task_data['project_id'],
                    error_message=result.get('message', 'Agent execution failed')
                )
                return
            
            # Agent succeeded
            await update_task_status(
                task_id=task_data['task_id'],
                status=result.get('status', current_task['status']),
                result=result,
                project_id=task_data['project_id'],
                success_message=result.get('message', 'Agent execution completed')
            )
            
        except ImportError as ie:
            error_message = f"Agent module not found: {module_path}"
            await update_task_status(
                task_id=task_data['task_id'],
                status=TaskStatus.FAILED.value,
                result={"error": str(ie)},
                project_id=task_data['project_id'],
                error_message=error_message
            )
            logger.error(error_message, exc_info=True)
            
    except Exception as e:
        error_message = f"Error processing task: {str(e)}"
        logger.error(error_message, exc_info=True)
        
        await update_task_status(
            task_id=task_data['task_id'],
            status=TaskStatus.FAILED.value,
            result={"error": str(e)},
            project_id=task_data['project_id'],
            error_message=error_message
        )


async def process_message(message: aio_pika.IncomingMessage):
    """Process incoming messages from RabbitMQ."""
    async with message.process():
        try:
            # Parse message body
            task_data = json.loads(message.body.decode())
            logger.info(f"Received message: {json.dumps(task_data, indent=2)}")
            
            if task_data.get('action') == 'execute':
                await process_task(task_data)
            elif task_data.get('action') == 'approve':
                # Get task type and import appropriate agent module
                # TODO: Uncomment when Supabase is set up
                # task_details = supabase.table('tasks') \
                #     .select("type, agent_role") \
                #     .eq('id', task_data['task_id']) \
                #     .execute()
                #
                # if not task_details.data:
                #     raise ValueError(f"Task {task_data['task_id']} not found")
                #
                # task_type = task_details.data[0]['type'].lower()
                # agent_role = task_details.data[0].get('agent_role', PhaseConfig.get_agent_for_task(task_type))
                
                # Dummy for now
                task_type = task_data.get('type', 'research_market').lower()
                agent_role = task_data.get('agent_role', PhaseConfig.get_agent_for_task(task_type))
                
                # Import and call the approve function
                module_path = f"agents.definitions.{agent_role}"
                logger.info(f"Importing agent module for approval: {module_path}")
                agent_module = importlib.import_module(module_path)
                
                result = await agent_module.approve(task_data)
                logger.info(f"Task approval result: {json.dumps(result, indent=2)}")
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)


async def consume_queue(queue_name: str):
    """Consume messages from a specific queue."""
    try:
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(
            os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
        )
        
        # Create channel
        channel = await connection.channel()
        
        # Declare queue
        queue = await channel.declare_queue(queue_name, durable=True)
        
        # Start consuming messages
        logger.info(f"🚀 Worker started and waiting for tasks on queue: {queue_name}...")
        await queue.consume(process_message)
        
        try:
            # Wait until terminate
            await asyncio.Future()
        finally:
            await connection.close()
            
    except Exception as e:
        logger.error(f"Error consuming queue {queue_name}: {str(e)}", exc_info=True)
        raise


async def main():
    """Main worker function. Can consume from multiple queues."""
    # Get queues from environment or use defaults
    queues_env = os.getenv("WORKER_QUEUES", "discovery_tasks,build_tasks,agent_execution,deployment_tasks")
    queues = [q.strip() for q in queues_env.split(",")]
    
    logger.info(f"Starting worker for queues: {queues}")
    
    # For now, consume from the first queue
    # TODO: Support multiple queues concurrently
    if queues:
        await consume_queue(queues[0])
    else:
        logger.error("No queues configured!")
        raise ValueError("No queues configured for worker")


if __name__ == "__main__":
    asyncio.run(main())

