"""
Task Queue Manager for RabbitMQ.

Manages task queuing to different RabbitMQ queues based on phase/task type.
Adapted from spark-api/workflow/task_queue_manager.py
"""
import logging
from typing import Dict, Optional
import aio_pika
import json
import os
from datetime import datetime
from config.phase_config import PhaseConfig


class TaskQueueManager:
    def __init__(self, rabbitmq_url: Optional[str] = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> aio_pika.Connection:
        """Create a connection to RabbitMQ."""
        try:
            connection = await aio_pika.connect_robust(self.rabbitmq_url)
            return connection
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def get_channel(self, connection: aio_pika.Connection) -> aio_pika.Channel:
        """Get a channel from the connection."""
        try:
            channel = await connection.channel()
            return channel
        except Exception as e:
            self.logger.error(f"Failed to create channel: {str(e)}")
            raise

    async def _declare_queue(self, channel: aio_pika.Channel, queue_name: str) -> aio_pika.Queue:
        """Declare a queue on the channel."""
        try:
            queue = await channel.declare_queue(queue_name, durable=True)
            return queue
        except Exception as e:
            self.logger.error(f"Failed to declare queue {queue_name}: {str(e)}")
            raise

    async def queue_task(self, task_data: Dict, queue_name: Optional[str] = None) -> bool:
        """
        Queue a task for execution.
        
        Args:
            task_data: Dictionary containing:
                - task_id: UUID of the task
                - project_id: UUID of the project
                - type: Type of task to execute
                - action: Action to perform (execute/approve)
                - feedback: Optional feedback for task retry
            queue_name: Optional queue name. If not provided, determined from task_type
        """
        try:
            # Determine queue name from task type if not provided
            if not queue_name:
                task_type = task_data.get("type")
                if task_type:
                    queue_name = PhaseConfig.get_queue_for_task(task_type)
                else:
                    # Default to agent_execution if we can't determine
                    queue_name = "agent_execution"
            
            # Add timestamp to task data
            task_data["queued_at"] = datetime.utcnow().isoformat()
            
            # Convert task data to JSON
            message_body = json.dumps(task_data).encode()
            
            # Create message with persistence
            message = aio_pika.Message(
                message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            
            # Connect and get channel
            connection = await self.connect()
            channel = await self.get_channel(connection)
            
            # Declare queue
            await self._declare_queue(channel, queue_name)
            
            # Publish message
            await channel.default_exchange.publish(
                message,
                routing_key=queue_name,
            )
            
            self.logger.info(f"Task queued successfully to {queue_name}: {task_data}")
            
            # Close connection
            await connection.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to queue task: {str(e)}")
            return False

    async def queue_task_execution(self, task_id: str, project_id: str, task_type: str, feedback: Optional[str] = None) -> bool:
        """Queue a task for execution."""
        task_data = {
            "task_id": str(task_id),
            "project_id": str(project_id),
            "type": task_type,
            "action": "execute"
        }
        
        if feedback:
            task_data["feedback"] = feedback
            
        return await self.queue_task(task_data)

    async def queue_task_approval(self, task_id: str, project_id: str, approved: bool, feedback: Optional[str] = None) -> bool:
        """Queue a task for approval processing."""
        task_data = {
            "task_id": str(task_id),
            "project_id": str(project_id),
            "action": "approve",
            "approved": approved
        }
        
        if feedback:
            task_data["feedback"] = feedback
        
        # For approval, we need to get the task type to determine queue
        # This will be handled by the worker, so we'll use a default queue
        return await self.queue_task(task_data, queue_name="agent_execution")

    async def queue_task_retry(self, task_id: str, project_id: str, task_type: str, feedback: str) -> bool:
        """Queue a task for retry with feedback."""
        return await self.queue_task_execution(task_id, project_id, task_type, feedback)

    async def queue_next_task(self, task_id: str, project_id: str, task_type: str) -> bool:
        """Queue the next task in sequence."""
        return await self.queue_task_execution(task_id, project_id, task_type)

