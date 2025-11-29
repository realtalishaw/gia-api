"""
Test script to send a task message to RabbitMQ queue.

This script sends a test message to verify the worker can consume and process tasks.
"""
import asyncio
import aio_pika
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()


async def send_test_task():
    """Send a test task to the RabbitMQ queue."""
    # Connect to RabbitMQ
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    
    print(f"Connecting to RabbitMQ at {rabbitmq_url}")
    
    try:
        connection = await aio_pika.connect_robust(rabbitmq_url)
        channel = await connection.channel()
        
        # Declare the queue (same as worker)
        queue_name = "discovery_tasks"  # Using discovery_tasks queue
        queue = await channel.declare_queue(queue_name, durable=True)
        
        # Create test task data
        task_data = {
            "task_id": "test-task-123",
            "project_id": "test-project-456",
            "type": "research_market",
            "action": "execute",
            "agent_role": "researcher"
        }
        
        # Convert to JSON
        message_body = json.dumps(task_data).encode()
        
        # Create message
        message = aio_pika.Message(
            message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        
        # Publish message
        await channel.default_exchange.publish(
            message,
            routing_key=queue_name,
        )
        
        print(f"✅ Task sent successfully to queue '{queue_name}'")
        print(f"Task data: {json.dumps(task_data, indent=2)}")
        
        # Close connection
        await connection.close()
        
    except Exception as e:
        print(f"❌ Error sending task: {str(e)}")
        print("\nMake sure RabbitMQ is running:")
        print("  - Install: brew install rabbitmq (macOS)")
        print("  - Start: rabbitmq-server")
        print("  - Or use Docker: docker run -d -p 5672:5672 rabbitmq:3")
        raise


if __name__ == "__main__":
    asyncio.run(send_test_task())

