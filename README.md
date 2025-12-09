# General Intelligence Agency (GIA)

A comprehensive platform for managing and executing specialized AI agents for business operations, growth, and development tasks.

## Overview

The General Intelligence Agency is a monorepo containing a FastAPI backend, React admin panel, and Celery-based task processing system. It provides a framework for registering, managing, and executing specialized agents that handle various business functions such as brand strategy, growth engineering, product development, and more.

## Architecture

The project consists of three main components:

### 1. **API** (`/api`)
FastAPI backend that provides:
- Agent registry and management system
- RESTful API endpoints for agent operations
- Webhook handling for external integrations
- Monitoring endpoints
- Supabase integration for data persistence

### 2. **Admin Panel** (`/admin-panel`)
React + Vite frontend application featuring:
- Supabase authentication
- Agent session management
- Real-time monitoring dashboard
- Flower (Celery monitoring) integration

### 3. **Task Worker** (`/api/worker`)
Celery-based distributed task processing:
- Background job execution
- Queue management (initialization and results)
- Flower monitoring interface
- Session management for agent workflows

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account and project
- RabbitMQ/CloudAMQP instance (for task queue)

### API Setup

1. Navigate to the API directory:
```bash
cd api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create `.env` file):
```bash
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
CLOUDAMQP_URL=your-rabbitmq-url
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

5. Run the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Admin Panel Setup

1. Navigate to the admin panel directory:
```bash
cd admin-panel
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```bash
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_FLOWER_URL=http://localhost:5555  # Optional, defaults to localhost
```

4. Start the development server:
```bash
npm run dev
```

### Task Worker Setup

1. Navigate to the API directory:
```bash
cd api
```

2. Start the Celery worker:
```bash
celery -A worker.celery_app worker --loglevel=info --queues=agent_initialization_queue,agent_results_queue
```

3. (Optional) Start Flower monitoring:
```bash
celery -A worker.celery_app flower --port=5555 --unauthenticated_api
```

Visit `http://localhost:5555` to view the Flower dashboard.

## Project Structure

```
gia-api/
├── api/                    # FastAPI backend
│   ├── agents/            # Agent definitions and implementations
│   │   ├── brand_strategy/
│   │   ├── growth_engineer/
│   │   ├── developer/
│   │   └── ...            # Additional specialized agents
│   ├── routes/            # API route handlers
│   │   ├── agent/        # Agent management endpoints
│   │   ├── webhook/      # Webhook handling
│   │   └── monitoring/   # Monitoring endpoints
│   ├── worker/            # Celery task worker
│   ├── docs/              # Documentation
│   └── main.py           # FastAPI application entry point
├── admin-panel/           # React frontend
│   └── src/
│       ├── components/   # React components
│       └── lib/          # Utilities (Supabase client)
└── render.yaml           # Render.com deployment configuration
```

## Available Agents

The platform includes specialized agents for various business functions:

- **Brand Strategy** - Brand positioning and strategy development
- **Growth Engineer** - Growth optimization and experimentation
- **Growth Strategy** - Strategic growth planning
- **Growth Systems Engineer** - Growth infrastructure and systems
- **Growth Kit** - Growth tooling and resources
- **Developer** - Software development tasks
- **Tech Lead** - Technical leadership and architecture
- **Product Manager** - Product management and PRD creation
- **Design** - Design and creative tasks
- **DevOps** - Infrastructure and deployment
- **Email Engineer** - Email system development
- **Email Marketing** - Email campaign management
- **Social Media** - Social media strategy and content
- **Market Research** - Market analysis and research
- **Audience Definition** - Target audience identification
- **Ad Creative** - Advertising creative development
- **Brand Kit** - Brand asset management
- **Founder Assets** - Founder resource management
- **QA** - Quality assurance and testing

## Key Features

- **Agent Registry**: Centralized system for registering and managing agents with Supabase sync
- **Task Processing**: Distributed task execution using Celery
- **Session Management**: Track and manage agent execution sessions
- **Webhook Integration**: Handle external events and notifications
- **Monitoring**: Real-time monitoring via Flower and custom endpoints
- **Authentication**: Supabase-based authentication for admin panel
- **CORS Support**: Configurable CORS for frontend integration

## API Endpoints

- `POST /agent` - Create a new agent
- `GET /agents` - Get all registered agents
- `POST /agents/feedback` - Submit feedback for an agent
- `POST /webhook` - Handle webhook events
- `GET /monitoring/health` - Health check endpoint

## Deployment

The project is configured for deployment on Render.com. See `render.yaml` for service configurations:

- **API Service**: FastAPI web service
- **Task Worker**: Celery worker service
- **Flower Monitoring**: Celery monitoring dashboard
- **Admin Panel**: Static React application

### Environment Variables for Production

Required environment variables:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (for server-side operations)
- `CLOUDAMQP_URL` - RabbitMQ connection URL
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)

For the admin panel:
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key
- `VITE_FLOWER_URL` - Flower monitoring URL (optional)

## Documentation

- [API Documentation](./api/README.md) - Detailed API setup and usage
- [Worker Documentation](./api/worker/README.md) - Task worker setup and configuration
- [Admin Panel Documentation](./admin-panel/README.md) - Frontend setup guide
- [Agent Registry](./api/docs/agent-registry.md) - Agent registration system
- [Supabase RLS Setup](./api/docs/supabase-rls-setup.md) - Row-level security configuration
- [Task Flow Debugging](./api/docs/task-flow-debugging.md) - Debugging guide

## Development Workflow

For local development, run these services in separate terminals:

1. **API Server**: `cd api && uvicorn main:app --reload`
2. **Celery Worker**: `cd api && celery -A worker.celery_app worker --loglevel=info --queues=agent_initialization_queue,agent_results_queue`
3. **Flower Monitoring**: `cd api && celery -A worker.celery_app flower --port=5555 --unauthenticated_api`
4. **Admin Panel**: `cd admin-panel && npm run dev`

## Contributing

When adding new agents:
1. Create a new directory under `api/agents/`
2. Implement `definition.py` with agent metadata
3. Implement `main.py` with agent logic
4. Register the agent using the registry system

## License

[Add your license information here]
