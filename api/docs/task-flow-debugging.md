# Task Flow Debugging Guide

## Exact Flow When a Task is Submitted

### Step 1: API Request (FastAPI Router)
**Location:** `api/routes/agent/router.py` - `POST /agent` endpoint

**What happens:**
1. Request received at `/agent` endpoint
2. **LOG:** `📥 API ENDPOINT CALLED: POST /agent`
3. Validates agent exists using `get_agent(agent.agent_name)`
4. **LOG:** `🔍 Validating agent exists: {agent_name}`
5. **LOG:** `✅ Agent found: {agent_name}` or `❌ Agent not found: {agent_name}`
6. Creates Celery task: `agent_initialization_task.delay(...)`
7. **LOG:** `📤 Creating Celery task and queuing to agent_initialization_queue...`
8. **LOG:** `✅ Celery task created with ID: {task_id}`
9. Saves task to database with "pending" status
10. Returns task_id to client

**Where logs appear:** 
- FastAPI application logs (wherever your API server logs go)
- Check: `stdout` of your API server process

---

### Step 2: Celery Worker Picks Up Task
**Location:** Celery worker process (separate from API server)

**What happens:**
1. Celery worker listening on `agent_initialization_queue` receives task
2. Worker executes `agent_initialization_task()` function
3. **LOG:** `🚀 TASK STARTED: agent_initialization_task` (with separator lines)
4. **LOG:** Task ID, Project ID, Agent Name, Context Length

**Where logs appear:**
- **Celery worker logs** (NOT API server logs!)
- Check: `stdout` of your Celery worker process
- If using Render: Check the worker service logs, not the API service logs

---

### Step 3: Task Execution Begins
**Location:** `api/worker/tasks.py` - `agent_initialization_task()` function

**What happens:**
1. **LOG:** `Starting agent initialization task: project_id={project_id}, agent_name={agent_name}, task_id={task_id}`
2. Updates Celery task state to "STARTED"
3. **LOG:** `Saving processing task status to database for task {task_id}`
4. Saves task to database with "processing" status
5. **LOG:** `✅ Successfully saved processing task status to database` or error

---

### Step 4: Session Manager Routing
**Location:** `api/worker/tasks.py` - After saving "processing" status

**What happens:**
1. **LOG:** `🎯 CALLING SESSION MANAGER: route_agent_task` (with separator lines)
2. Gets session manager instance
3. **LOG:** `✅ Session manager instance retrieved: {type}`
4. Calls `session_manager.route_agent_task(...)`
5. **LOG:** `🔀 Session Manager: Routing task - project_id={project_id}, agent_name={agent_name}, task_id={task_id}`
6. **LOG:** `📋 Session Manager: Agent definition found - name={name}, execution_type={type}`
7. **LOG:** `🔑 Session Manager: Created session_key={session_key}`
8. **LOG:** `🎯 Session Manager: Routing based on execution_type={type}`
9. Routes to either Celery (local) or Fly machine (remote)
10. **LOG:** `💾 Session Manager: Registering session...`
11. **LOG:** `✅ Session Manager: Session successfully registered in database` or error
12. **LOG:** `✅ Session manager returned routing_info: {routing_info}`

**Where logs appear:**
- **Celery worker logs** (same as Step 2)

---

### Step 5: Agent Execution
**Location:** `api/worker/tasks.py` - After routing

**What happens:**
- If local: Executes agent's `process()` function
- If remote: Returns placeholder result
- Updates session status throughout
- Saves final result to database

---

## Where to Check Logs

### If using Render:
1. **API Server Logs:** Check the `gia-api` service logs (for Step 1)
2. **Worker Logs:** Check the `gia-task-worker` service logs (for Steps 2-5)
   - **THIS IS WHERE SESSION MANAGER LOGS WILL APPEAR**

### If running locally:
1. **API Server:** Terminal where you run `uvicorn main:app`
2. **Celery Worker:** Terminal where you run `celery -A worker.celery_app worker`

---

## Common Issues

### Issue: No logs appearing at all
**Possible causes:**
- Celery worker is not running
- Worker is running old code (needs restart)
- Logs are going to a different location

**Solution:**
1. Verify worker is running: `ps aux | grep celery`
2. Restart worker to pick up new code
3. Check worker logs specifically (not API logs)

### Issue: API logs appear but no worker logs
**Possible causes:**
- Task is queued but worker isn't processing it
- Worker is listening to wrong queue
- RabbitMQ connection issue

**Solution:**
1. Check worker is listening to `agent_initialization_queue`
2. Check RabbitMQ connection
3. Verify task appears in queue

### Issue: Task starts but session manager logs don't appear
**Possible causes:**
- Exception before reaching session manager
- Session manager import failed
- Code path not reached

**Solution:**
1. Check for exceptions in worker logs
2. Verify `from worker.session_manager import get_session_manager` succeeds
3. Check if task reaches "Saving processing task status" log

---

## Debugging Checklist

- [ ] API endpoint receives request (check API logs)
- [ ] Celery task is created (check API logs for task ID)
- [ ] Worker picks up task (check worker logs for "TASK STARTED")
- [ ] Task saves "processing" status (check worker logs)
- [ ] Session manager is called (check worker logs for "CALLING SESSION MANAGER")
- [ ] Session manager routes task (check worker logs for routing info)
- [ ] Session is registered in database (check worker logs + Supabase)
