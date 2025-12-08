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
   cd api
   celery -A worker.celery_app worker --loglevel=info --queues=agent_initialization_queue
   ```

3. **Running with Multiple Queues**:
   ```bash
   celery -A worker.celery_app worker --loglevel=info --queues=agent_initialization_queue,other_queue
   ```

4. **Running Flower Monitoring Locally**:
   
   Flower provides a web interface to monitor your Celery workers and queues.
   
   **Option 1: Using the command flag** (recommended for local dev):
   ```bash
   cd api
   celery -A worker.celery_app flower --port=5555 --unauthenticated_api
   ```
   
   **Option 2: Using environment variable**:
   ```bash
   cd api
   export FLOWER_UNAUTHENTICATED_API=true
   celery -A worker.celery_app flower --port=5555
   ```
   
   The `--unauthenticated_api` flag or `FLOWER_UNAUTHENTICATED_API=true` environment variable allows the admin panel to access Flower's API endpoints without authentication (safe for local development only).
   
   Then open your browser to `http://localhost:5555` to view the Flower dashboard.
   
   **Note**: Make sure your worker is running before starting Flower, and that both have access to the same `CLOUDAMQP_URL` environment variable.

## Queues

- `agent_initialization_queue` - Handles agent initialization tasks

## Tasks

- `agent_initialization_task` - Initializes an agent with the given project ID, context, and agent name.

## Environment Variables

- `CLOUDAMQP_URL` or `RABBITMQ_URL` - RabbitMQ connection URL (required)

## Local Development Workflow

For local development, you'll typically need to run three services:

1. **API Server** (in one terminal):
   ```bash
   cd api
   uvicorn main:app --reload
   ```

2. **Celery Worker** (in another terminal):
   ```bash
   cd api
   celery -A worker.celery_app worker --loglevel=info --queues=agent_initialization_queue
   ```

3. **Flower Monitoring** (in a third terminal, optional):
   ```bash
   cd api
   celery -A worker.celery_app flower --port=5555 --unauthenticated_api
   ```
   
   Or set the environment variable:
   ```bash
   export FLOWER_UNAUTHENTICATED_API=true
   celery -A worker.celery_app flower --port=5555
   ```

4. **Admin Panel** (in a fourth terminal):
   ```bash
   cd admin-panel
   npm run dev
   ```

The admin panel will automatically connect to Flower at `http://localhost:5555` if `VITE_FLOWER_URL` is not set in your `.env` file.

## Production Authentication

For production deployments, **never use `--unauthenticated_api`**. Instead, use one of these authentication methods:

### Option 1: Basic Authentication (Simplest)

Run Flower with Basic Auth:
```bash
celery -A worker.celery_app flower --port=$PORT --address=0.0.0.0 --basic-auth=admin:your-secure-password
```

You can specify multiple users:
```bash
celery -A worker.celery_app flower --port=$PORT --address=0.0.0.0 --basic-auth=admin:password1,user2:password2
```

**Note**: When using Basic Auth, the admin panel iframe will need to handle authentication. You may need to:
- Use a proxy endpoint that adds authentication headers
- Or configure the admin panel to open Flower in a new window instead of an iframe

### Option 2: OAuth Authentication (Recommended for Production)

Flower supports OAuth with Google, GitHub, GitLab, or Okta. Create a `flowerconfig.py` file:

```python
# flowerconfig.py
auth_provider = 'flower.views.auth.GoogleAuth2LoginHandler'  # or GithubLoginHandler, GitLabLoginHandler, OktaLoginHandler
auth = 'allowed-emails.*@yourdomain.com'
oauth2_key = '<your_client_id>'
oauth2_secret = '<your_client_secret>'
oauth2_redirect_uri = 'https://your-flower-domain.com/login'
```

Then run Flower with:
```bash
celery -A worker.celery_app flower --port=$PORT --address=0.0.0.0 --conf=flowerconfig.py
```

### Option 3: Reverse Proxy with Authentication

Run Flower behind a reverse proxy (Nginx/Apache) that handles SSL/TLS and authentication. This is the most secure option for production.

### Environment Variables for Production

- `FLOWER_UNAUTHENTICATED_API` - Set to `true` only for local development. **Never use in production.**
- `FLOWER_BASIC_AUTH` - Alternative to `--basic-auth` flag (format: `user1:pass1,user2:pass2`)
