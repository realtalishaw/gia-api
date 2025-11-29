# GIA API - Autonomous MVP Builder

An autonomous multi-agent system for building MVPs from concept to deployment. Agents work collaboratively through defined phases, with some tasks following deterministic SOPs and others creating subtasks probabilistically.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [System Components](#system-components)
- [File Structure](#file-structure)
- [How It Works](#how-it-works)
- [Task Types](#task-types)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Development](#development)

## Overview

GIA (Generative Intelligence Assistant) is an autonomous MVP builder that uses specialized AI agents to:

1. **Research** the market and competitors
2. **Design** brand identity and UI/UX mockups
3. **Build** the MVP with code
4. **Setup** marketing and analytics
5. **Deploy** and prepare for handoff

The system uses an **asynchronous event-driven architecture** where:
- API receives requests and queues tasks
- Workers consume tasks from RabbitMQ
- Agents execute tasks in isolated sandboxes
- Real-time updates stream to frontend via Supabase

## Architecture

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  FastAPI    │─────▶│  RabbitMQ    │─────▶│   Worker    │
│   (API)     │      │   (Queue)    │      │  (Agents)   │
└──────┬──────┘      └──────────────┘      └──────┬──────┘
       │                                           │
       │                                           │
       ▼                                           ▼
┌─────────────┐                              ┌─────────────┐
│  Supabase  │                              │    Modal    │
│ (Database) │                              │  (Sandbox)  │
└─────────────┘                              └─────────────┘
```

### Key Concepts

- **Phases**: High-level workflow stages (Discovery, Design, Development, etc.)
- **Tasks**: Individual work items that agents execute
- **Deterministic Tasks**: Follow SOP/system prompts, use progress updates
- **Probabilistic Tasks**: Agents create subtasks dynamically
- **Progress Updates**: Visibility-only updates (not queued)
- **Real Tasks**: Executable tasks (queued to RabbitMQ)

## System Components

### 1. **Orchestrator** (`orchestrator/`)
The "Tech Lead" that manages workflow progression, task creation, and phase transitions.

### 2. **Agents** (`agents/`)
Specialized workers that execute tasks. Each agent has its own isolated sandbox.

### 3. **Phase Config** (`config/`)
Defines the SOP/checklist structure - what needs to be done, not how.

### 4. **API Routes** (`routes/`)
FastAPI endpoints for project management and task approval.

## File Structure

```
gia-api/
├── main.py                          # FastAPI application entry point
├── worker.py                        # Agent runner (consumes from RabbitMQ)
├── config/
│   └── phase_config.py             # Phase definitions and task mappings
├── orchestrator/
│   ├── engine.py                    # AgentOrchestrator - main workflow manager
│   ├── task_queue_manager.py       # RabbitMQ task queuing
│   ├── task_state_manager.py       # Task state management (Supabase)
│   └── status_updates.py           # Activity feed helper
├── agents/
│   ├── runner.py                    # Worker that processes tasks
│   └── definitions/
│       └── researcher.py           # Example agent implementation
├── routes/
│   ├── projects/
│   │   ├── projects.py             # Project API endpoints
│   │   └── schemas.py              # Pydantic models
│   └── health/
│       └── health.py               # Health check endpoint
└── requirements.txt                # Python dependencies
```

## How It Works

### 1. Project Start

```python
# Frontend calls API
POST /projects/start
{
  "project_id": "uuid",
  "project_brief": "Build a task management app"
}

# API creates project and queues first task
orchestrator.create_task(project_id, "conduct_market_research")
```

### 2. Task Execution Flow

```
1. Task queued to RabbitMQ
   ↓
2. Worker picks up task
   ↓
3. Worker imports agent module (e.g., agents.definitions.researcher)
   ↓
4. Agent executes task
   ↓
5. Agent creates progress updates (if deterministic)
   OR creates subtasks (if probabilistic)
   ↓
6. Task marked complete
   ↓
7. Orchestrator creates next task
```

### 3. Deterministic Tasks (SOP)

**Example: Market Research**

```python
# Agent creates progress updates for visibility
await orchestrator.create_progress_update(
    project_id=project_id,
    message="🔍 Looking up competitors...",
    task_id=task_id
)
# Agent does work internally
# No separate tasks created
```

**Characteristics:**
- Follows system prompt/SOP
- Creates progress updates (status_updates table)
- Same agent does all work
- No queuing needed

### 4. Probabilistic Tasks (Agent Creates Subtasks)

**Example: Build MVP**

```python
# Agent creates real subtasks
success, subtask_id, error = await orchestrator.create_task(
    project_id=project_id,
    task_type="implement_auth",
    parent_task_id=parent_task_id
)
# This creates a task AND queues it
# Different agent/sandbox can pick it up
```

**Characteristics:**
- Agent decides what subtasks are needed
- Creates real tasks (tasks table)
- Tasks are queued to RabbitMQ
- Different agents can work in parallel

## Task Types

### Phase 0: Discovery (Deterministic)
- `conduct_market_research` - Researcher agent
- `create_brand_identity` - Brand Strategist (requires approval)
- `write_prd` - Planner (requires approval)

### Phase 1: Design (Deterministic)
- `create_ui_ux_mockups` - Designer (requires approval)

### Phase 2: Development (Probabilistic)
- `build_mvp` - Developer (creates subtasks dynamically)

### Phase 3: Marketing & Setup (Deterministic)
- `setup_email` - DevOps
- `setup_analytics` - DevOps
- `finalize_finishing_touches` - Marketer

### Phase 4: Deployment (Deterministic)
- `deploy_app` - DevOps
- `prepare_handoff` - DevOps

## File Descriptions

### Core Application

**`main.py`**
- FastAPI application entry point
- Sets up CORS, includes routers
- Root endpoint for health checks

**`worker.py`** (Future: `agents/runner.py`)
- Consumes messages from RabbitMQ queues
- Dynamically imports agent modules
- Executes tasks and updates status

### Configuration

**`config/phase_config.py`**
- Defines all phases and their tasks
- Maps tasks to agents and queues
- Defines approval requirements
- Helper methods for phase/task lookups

**Key Classes:**
- `Phase`: Enum of phase designations
- `PhaseConfig`: Phase definitions and helper methods

### Orchestrator

**`orchestrator/engine.py`**
- `AgentOrchestrator`: Main workflow manager
- Manages phase transitions
- Creates tasks and handles completion
- Generates next phase prompts (autonomous)

**Key Methods:**
- `create_task()`: Create and queue a real task
- `create_progress_update()`: Create visibility-only update
- `handle_task_completion()`: Process task completion
- `handle_phase_completion()`: Transition to next phase

**`orchestrator/task_queue_manager.py`**
- Manages RabbitMQ connections
- Queues tasks to appropriate queues
- Determines queue from task type

**`orchestrator/task_state_manager.py`**
- Manages task state in Supabase
- Updates task status
- Handles approvals

**`orchestrator/status_updates.py`**
- Creates activity feed entries
- Used for real-time updates to frontend
- Different from task state (visibility vs. workflow)

### Agents

**`agents/runner.py`**
- Worker that processes RabbitMQ messages
- Imports agent modules dynamically
- Updates task status
- Creates activity updates

**`agents/definitions/researcher.py`**
- Example agent implementation
- Shows pattern for deterministic tasks
- Demonstrates progress updates

**Agent Interface:**
```python
async def execute(task_data: dict) -> Dict:
    """Execute the agent task."""
    # Create progress updates
    # Do work
    # Return result

async def approve(task_data: dict) -> Dict:
    """Handle task approval."""
    # Process approval
    # Return result
```

### API Routes

**`routes/projects/projects.py`**
- `POST /projects/start`: Start a new project
- `GET /projects`: List projects for user
- `GET /projects/{project_id}`: Get project details
- `POST /projects/{project_id}/approve_phase`: Approve/reject phase

**`routes/projects/schemas.py`**
- Pydantic models for request/response
- Type safety and validation

## Getting Started

### Prerequisites

- Python 3.11+
- RabbitMQ (for task queuing)
- Supabase (for database and real-time)

### Installation

```bash
# Clone repository
cd gia-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file:

```env
# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost/

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Worker Configuration
WORKER_QUEUES=discovery_tasks,build_tasks,agent_execution,deployment_tasks
```

### Running the API

```bash
# Start FastAPI server
uvicorn main:app --reload

# API will be available at http://localhost:8000
```

### Running the Worker

```bash
# Start worker (consumes from RabbitMQ)
python agents/runner.py

# Worker will listen to queues and process tasks
```

### Testing

```bash
# Test phase configuration
python test_phase_config.py

# Test orchestrator logic
python test_orchestrator.py

# Send test task to queue
python test_send_task.py
```

## API Endpoints

### Projects

#### `POST /projects/start`
Start a new project.

**Request:**
```json
{
  "project_id": "uuid",
  "project_brief": "Build a task management app"
}
```

**Response:**
```json
{
  "success": true,
  "project_id": "uuid",
  "message": "Project started successfully"
}
```

#### `GET /projects?user_id={user_id}`
List all projects for a user.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Task Management App",
    "status": "building",
    "current_phase": "Phase 0: Discovery",
    "progress": 20
  }
]
```

#### `GET /projects/{project_id}`
Get detailed project information.

**Response:**
```json
{
  "id": "uuid",
  "status": "waiting_approval",
  "current_phase": "Phase 0: Discovery",
  "artifacts": {
    "prd": "# Product Requirements...",
    "logo_url": "https://...",
    "market_analysis": "## Market Analysis..."
  }
}
```

#### `POST /projects/{project_id}/approve_phase`
Approve or reject a phase.

**Request:**
```json
{
  "approved": true,
  "feedback": "Looks good!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Phase approved. Moving to next phase.",
  "next_phase": "Phase 1: Design"
}
```

## Development

### Adding a New Agent

1. Create agent file in `agents/definitions/`:
```python
# agents/definitions/my_agent.py
async def execute(task_data: dict) -> Dict:
    # Agent logic here
    return {"success": True, ...}

async def approve(task_data: dict) -> Dict:
    # Approval logic here
    return {"success": True, ...}
```

2. Add task to `config/phase_config.py`:
```python
{
    "type": "my_task",
    "agent": "my_agent",
    "description": "Does something"
}
```

3. Worker will automatically import and execute it!

### Adding a New Phase

1. Add phase to `Phase` enum in `config/phase_config.py`
2. Add phase definition to `PHASES` list
3. Define tasks, dependencies, and deliverables
4. Update approval requirements if needed

### Task Patterns

**Deterministic Task Pattern:**
```python
async def execute(task_data: dict, orchestrator) -> Dict:
    # Create progress updates
    await orchestrator.create_progress_update(...)
    
    # Do work
    result = do_work()
    
    # Return success
    return {"success": True, "result": result}
```

**Probabilistic Task Pattern:**
```python
async def execute(task_data: dict, orchestrator) -> Dict:
    # Create subtasks
    for subtask in subtasks_needed:
        await orchestrator.create_task(
            project_id=project_id,
            task_type=subtask,
            parent_task_id=task_data['task_id']
        )
    
    # Wait for subtasks or mark complete
    return {"success": True}
```

## Architecture Decisions

### Why Two Update Systems?

- **`tasks` table**: Workflow state (what needs to be done)
- **`project_activity` table**: User visibility (what's happening)

This separation allows:
- Internal subtasks to show progress without creating workflow items
- Real tasks to be tracked for execution
- Clean separation of concerns

### Why Deterministic vs Probabilistic?

- **Deterministic**: Tasks follow a known SOP (market research, design)
- **Probabilistic**: Tasks require agent judgment (what features to build)

This allows:
- Predictable workflow for standard tasks
- Flexibility for complex tasks
- Better user experience (know what's coming vs. adaptive)

### Why Parent-Child Tasks?

- Allows task hierarchy
- Enables parallel execution of subtasks
- Tracks relationships between work items
- Supports complex workflows

## Troubleshooting

### Worker Not Processing Tasks

1. Check RabbitMQ is running: `rabbitmq-server`
2. Verify queue names match in config
3. Check worker logs for errors

### Tasks Not Creating

1. Verify Supabase connection
2. Check task type exists in phase config
3. Verify no blockers (failed tasks, pending approvals)

### Progress Updates Not Showing

1. Check Supabase `project_activity` table
2. Verify orchestrator has Supabase client
3. Check activity_type is correct

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]
