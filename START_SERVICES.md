# Starting GIA Services

This project includes scripts to help you start all the required services for local development.

## Quick Start

### Option 1: Python Script (Recommended)

The Python script provides better output handling and cross-platform support:

```bash
# Interactive mode - choose which services to start
python start.py

# Start all services
python start.py --all

# Start specific services
python start.py --api --task-worker --flower

# Available flags:
#   --api              FastAPI server
#   --task-worker      Celery task worker (agent tasks)
#   --context-worker   Celery context worker (context ingestion)
#   --flower           Flower monitoring dashboard
#   --web              Admin panel web app
```

### Option 2: Shell Script

A simpler bash script alternative:

```bash
# Interactive mode
./start.sh

# Start all services
./start.sh all

# Start specific services
./start.sh api task-worker flower
```

## Services

### 1. API Server
- **Port**: 8000
- **URL**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Command**: `cd api && uvicorn main:app --reload`

### 2. Task Worker
- **Queues**: `agent_initialization_queue`, `agent_results_queue`
- **Command**: `cd api && celery -A worker.celery_app worker --loglevel=info --queues=agent_initialization_queue,agent_results_queue`

### 3. Context Worker
- **Queues**: `context_queue`
- **Command**: `cd api && celery -A context_engine.worker.celery_app worker --loglevel=info --queues=context_queue`

### 4. Flower Monitoring
- **Port**: 5555
- **URL**: http://localhost:5555
- **Command**: `cd api && celery -A worker.celery_app flower --port=5555 --unauthenticated_api`

### 5. Admin Panel
- **Port**: 5173 (default Vite port)
- **URL**: http://localhost:5173
- **Command**: `cd admin-panel && npm run dev`

## Manual Start (Individual Terminals)

If you prefer to run services manually in separate terminals:

### Terminal 1: API Server
```bash
cd api
uvicorn main:app --reload
```

### Terminal 2: Task Worker
```bash
cd api
celery -A worker.celery_app worker --loglevel=info --queues=agent_initialization_queue,agent_results_queue
```

### Terminal 3: Context Worker
```bash
cd api
celery -A context_engine.worker.celery_app worker --loglevel=info --queues=context_queue
```

### Terminal 4: Flower Monitoring
```bash
cd api
celery -A worker.celery_app flower --port=5555 --unauthenticated_api
```

### Terminal 5: Admin Panel
```bash
cd admin-panel
npm run dev
```

## Stopping Services

### Using the Scripts
- Press `Ctrl+C` in the terminal running the script
- All services will be stopped gracefully

### Manual Stop
- Press `Ctrl+C` in each terminal running a service
- Or use `pkill` to stop specific services:
  ```bash
  pkill -f "uvicorn main:app"
  pkill -f "celery.*worker"
  pkill -f "celery.*flower"
  pkill -f "vite"
  ```

## Environment Variables

Make sure you have the following environment variables set (in `.env` files or your shell):

### API Services (api/.env or environment)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `CLOUDAMQP_URL` or `RABBITMQ_URL` - RabbitMQ connection URL

### Admin Panel (admin-panel/.env)
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key
- `VITE_FLOWER_URL` - Flower URL (optional, defaults to http://localhost:5555)

## Troubleshooting

### Port Already in Use
If a port is already in use, you can:
1. Stop the process using that port
2. Change the port in the service configuration
3. Kill the process: `lsof -ti:8000 | xargs kill` (replace 8000 with your port)

### Services Not Starting
- Check that all dependencies are installed:
  - Python: `pip install -r api/requirements.txt`
  - Node: `cd admin-panel && npm install`
- Verify environment variables are set correctly
- Check service logs for error messages

### Celery Workers Not Processing Tasks
- Ensure RabbitMQ/CloudAMQP is accessible
- Check that the correct queues are specified
- Verify the worker is listening to the right queues in Flower

## Development Workflow

For typical development, you'll want to run:
1. API Server (always needed)
2. Task Worker (for agent processing)
3. Context Worker (for context ingestion)
4. Flower (optional, for monitoring)
5. Admin Panel (for UI)

You can start all of these at once with:
```bash
python start.py --all
```

Or start just what you need:
```bash
python start.py --api --task-worker
```
