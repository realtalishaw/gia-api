"""
Celery application configuration for context worker.
Uses RabbitMQ (CloudAMQP) as the message broker.
"""
import os
import sys
from pathlib import Path
from celery import Celery
from dotenv import load_dotenv

# CRITICAL: Add project root to path BEFORE any other imports or Celery initialization
# This ensures imports work whether running from api/ directory or project root
_current_file = Path(__file__).resolve()
# Get the project root (parent of api directory)
# File structure: project_root/api/context_engine/worker/celery_app.py
project_root = _current_file.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv()

# Get RabbitMQ connection URL from environment
# CloudAMQP provides this as CLOUDAMQP_URL or RABBITMQ_URL
rabbitmq_url = os.getenv("CLOUDAMQP_URL") or os.getenv("RABBITMQ_URL")

if not rabbitmq_url:
    raise ValueError(
        "CLOUDAMQP_URL or RABBITMQ_URL environment variable must be set. "
        "Get this from your CloudAMQP dashboard."
    )

# Create Celery app for context worker
# Explicitly use amqp transport for both broker and backend
celery_app = Celery(
    "gia_context_worker",
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

# Define queues - context ingestion tasks go to context_queue
# Use the full module path that works from project root
celery_app.conf.task_routes = {
    "api.context_engine.worker.tasks.ingest_context_data": {"queue": "context_queue"},
}

# Auto-discover tasks
# Use api.context_engine.worker - this works because we added project_root to sys.path above
celery_app.autodiscover_tasks(["api.context_engine.worker"])
