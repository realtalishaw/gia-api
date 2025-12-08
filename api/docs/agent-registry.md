# Agent Registry Documentation

## Overview

The Agent Registry is a centralized system for managing agent definitions with automatic synchronization to Supabase. It provides a clean, extensible architecture where each agent owns its definition and automatically registers itself when imported.

## Architecture

### Core Components

1. **AgentDefinition Model** (`agents/models.py`)
   - Pydantic model defining the schema for agent metadata
   - Fields: `name`, `role`, `description`, `goal`, `requirements`, `artifacts`, `requires_approval`

2. **AgentRegistry Class** (`agents/registry.py`)
   - Singleton registry that manages all agent definitions
   - Handles CRUD operations and Supabase synchronization
   - Maintains an in-memory dictionary of registered agents

3. **Individual Agent Folders**
   - Each agent has its own folder (e.g., `agents/market_research/`)
   - Contains:
     - `definition.py` - Agent's own definition
     - `main.py` - Agent's process function
     - `__init__.py` - Auto-registration logic

4. **Agent Loader** (`agents/loader.py`)
   - Imports all agents to trigger registration
   - Called on application startup

## How It Works

### 1. Agent Registration Flow

```
Application Start
    ↓
main.py loads agents.loader
    ↓
loader.py imports all agent modules
    ↓
Each agent's __init__.py executes
    ↓
register_agent(AGENT_DEFINITION) is called
    ↓
AgentRegistry.register_agent() stores agent
    ↓
Agent syncs to Supabase (if configured)
    ↓
sync_all_agents_to_supabase() runs as backup
```

### 2. Agent Structure

Each agent follows this structure:

```
agents/
  └── agent_name/
      ├── __init__.py          # Auto-registration
      ├── definition.py         # Agent definition
      └── main.py              # Process function
```

**Example: `agents/market_research/__init__.py`**
```python
from .main import process
from .definition import AGENT_DEFINITION
from ..registry import register_agent

# Register this agent on import
register_agent(AGENT_DEFINITION)

__all__ = ["process", "AGENT_DEFINITION"]
```

**Example: `agents/market_research/definition.py`**
```python
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="market_research",
    role="Market Research Analyst",
    description="...",
    goal="...",
    requirements=["project_brief"],
    artifacts=["market_research_report"],
    requires_approval=False
)
```

### 3. Registry Operations

#### Register an Agent
```python
from agents import register_agent, AgentDefinition

agent = AgentDefinition(
    name="new_agent",
    role="Agent Role",
    description="Agent description",
    goal="Agent goal",
    requirements=["requirement1"],
    artifacts=["artifact1"],
    requires_approval=False
)

register_agent(agent)  # Automatically syncs to Supabase
```

#### Get an Agent
```python
from agents import get_agent

agent = get_agent("market_research")
if agent:
    print(agent.role)  # "Market Research Analyst"
```

#### Get All Agents
```python
from agents import get_all_agents

all_agents = get_all_agents()
for agent in all_agents:
    print(f"{agent.name}: {agent.role}")
```

#### Update an Agent
```python
from agents import update_agent, AgentDefinition

updated_agent = AgentDefinition(
    name="market_research",
    role="Updated Role",
    # ... other fields
)

update_agent("market_research", updated_agent)  # Syncs to Supabase
```

#### Delete an Agent
```python
from agents import delete_agent

delete_agent("market_research")  # Removes from registry and Supabase
```

### 4. Supabase Synchronization

The registry automatically syncs agents to Supabase when:
- An agent is registered
- An agent is updated
- An agent is deleted
- Application starts (via `sync_all_agents_to_supabase()`)

#### Supabase Table Schema

The registry expects an `agents` table with:
- `name` (text, primary key) - Unique agent identifier
- `role` (text) - Agent's role/title
- `description` (text) - What the agent does
- `goal` (text) - Agent's primary goal
- `requirements` (jsonb or text[]) - Required inputs/artifacts
- `artifacts` (jsonb or text[]) - Outputs produced
- `requires_approval` (boolean) - Whether approval is needed

#### Configuration

Set environment variables:
```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here  # Recommended for server-side
# OR
SUPABASE_ANON_KEY=your-anon-key-here  # Requires RLS policies to be configured
```

**Important:** For server-side operations like agent registry sync, use `SUPABASE_SERVICE_ROLE_KEY` instead of `SUPABASE_ANON_KEY`. The service role key bypasses Row Level Security (RLS), which is necessary for programmatic inserts/updates.

If you get RLS errors, see [Supabase RLS Setup Guide](./supabase-rls-setup.md) for configuration instructions.

The registry gracefully handles missing Supabase configuration - it will continue to work in-memory without syncing.

### 5. Adding a New Agent

To add a new agent:

1. **Create the agent folder structure:**
   ```bash
   mkdir -p agents/new_agent
   ```

2. **Create `definition.py`:**
   ```python
   from ..models import AgentDefinition

   AGENT_DEFINITION = AgentDefinition(
       name="new_agent",
       role="New Agent Role",
       description="Agent description",
       goal="Agent goal",
       requirements=["requirement1"],
       artifacts=["artifact1"],
       requires_approval=False
   )
   ```

3. **Create `main.py`:**
   ```python
   def process() -> dict:
       """Process function for New Agent"""
       return {
           "status": "completed",
           "message": "Completed the agent's goal."
       }
   ```

4. **Create `__init__.py`:**
   ```python
   from .main import process
   from .definition import AGENT_DEFINITION
   from ..registry import register_agent

   # Register this agent on import
   register_agent(AGENT_DEFINITION)

   __all__ = ["process", "AGENT_DEFINITION"]
   ```

5. **Add to `loader.py`:**
   ```python
   from .new_agent import AGENT_DEFINITION as _new_agent
   ```

6. **Restart the application** - The agent will be automatically registered and synced to Supabase!

## API Reference

### AgentRegistry Class

#### Methods

- `register_agent(agent: AgentDefinition) -> bool`
  - Registers or updates an agent
  - Automatically syncs to Supabase if configured
  - Returns `True` on success

- `get_agent(name: str) -> Optional[AgentDefinition]`
  - Retrieves an agent by name
  - Returns `None` if not found

- `get_all_agents() -> List[AgentDefinition]`
  - Returns all registered agents

- `delete_agent(name: str) -> bool`
  - Deletes an agent from registry and Supabase
  - Returns `True` if deleted, `False` if not found

- `update_agent(name: str, agent: AgentDefinition) -> bool`
  - Updates an existing agent
  - Handles name changes (deletes old, creates new)
  - Returns `True` on success

- `sync_all_to_supabase() -> dict`
  - Syncs all registered agents to Supabase
  - Returns sync results with counts and errors

### Convenience Functions

All registry methods are available as module-level functions:

```python
from agents import (
    register_agent,
    get_agent,
    get_all_agents,
    delete_agent,
    update_agent,
    sync_all_agents_to_supabase
)
```

## Error Handling

The registry is designed to be resilient:

- **Missing Supabase**: Works in-memory only, logs warnings
- **Supabase errors**: Logs warnings but continues operation
- **Import errors**: Individual agent failures don't break the system
- **Missing agents**: Returns `None` instead of raising exceptions

## Best Practices

1. **Agent Definitions**: Keep definitions in each agent's folder - don't centralize them
2. **Naming**: Use snake_case for agent names (e.g., `market_research`, not `marketResearch`)
3. **Requirements/Artifacts**: Use consistent naming for requirements and artifacts across agents
4. **Testing**: Test agent registration in isolation before adding to loader
5. **Supabase**: Always verify agents are synced after adding new ones

## Troubleshooting

### Agents not syncing to Supabase

1. Check environment variables are set:
   ```bash
   echo $SUPABASE_URL
   echo $SUPABASE_ANON_KEY
   ```

2. Verify Supabase table exists with correct schema

3. Check application logs for sync errors

4. Manually trigger sync:
   ```python
   from agents import sync_all_agents_to_supabase
   result = sync_all_agents_to_supabase()
   print(result)
   ```

### Agent not registering

1. Verify agent is imported in `loader.py`
2. Check `__init__.py` calls `register_agent()`
3. Ensure `AGENT_DEFINITION` is properly defined
4. Check for import errors in application logs

### Duplicate agents

The registry uses `upsert` operations, so duplicate names will update existing entries rather than create duplicates. If you see duplicates, check:
- Supabase table constraints
- Agent name consistency across definitions
