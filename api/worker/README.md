# Task Worker

This directory contains the Celery task worker for managing background tasks.

## Structure

- `celery_app.py` - Celery application configuration
- `tasks.py` - Task definitions
- `__init__.py` - Package initialization

## Setup

1. **CloudAMQP Configuration**: Set the `CLOUDAMQP_URL` or `RABBITMQ_URL` environment variable with your CloudAMQP connection string.

2. **Running the Worker Locally**:
   ```bash
   celery -A worker.celery_app worker --loglevel=info --queues=agent_initialization_queue
   ```

3. **Running with Multiple Queues**:
   ```bash
   celery -A worker.celery_app worker --loglevel=info --queues=agent_initialization_queue,other_queue
   ```

## Queues

- `agent_initialization_queue` - Handles agent initialization tasks

## Tasks

- `agent_initialization_task` - Initializes an agent with the given project ID, context, and agent name.

## Environment Variables

- `CLOUDAMQP_URL` or `RABBITMQ_URL` - RabbitMQ connection URL (required)
