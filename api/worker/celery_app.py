"""
Celery application configuration for task worker.
Uses RabbitMQ (CloudAMQP) as the message broker.
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Get RabbitMQ connection URL from environment
# CloudAMQP provides this as CLOUDAMQP_URL or RABBITMQ_URL
rabbitmq_url = os.getenv("CLOUDAMQP_URL") or os.getenv("RABBITMQ_URL")

if not rabbitmq_url:
    raise ValueError(
        "CLOUDAMQP_URL or RABBITMQ_URL environment variable must be set. "
        "Get this from your CloudAMQP dashboard."
    )

# Create Celery app
# Explicitly use amqp transport for both broker and backend
celery_app = Celery(
    "gia_worker",
    broker=rabbitmq_url,
    backend=f"rpc://",  # Use RPC backend (stores results in RabbitMQ) - simpler and works with amqp
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Define queues
celery_app.conf.task_routes = {
    "worker.tasks.agent_initialization": {"queue": "agent_initialization_queue"},
    "worker.tasks.process_agent_result": {"queue": "agent_results_queue"},
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["worker"])
