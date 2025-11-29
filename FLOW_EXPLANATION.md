# Project Start Flow Explanation

## Current Flow

When `/projects/start` is called:

1. **Project Created** in Supabase
   - Status: `building`
   - Current Phase: `discovery`

2. **First Task Queued**: `conduct_market_research`
   - Queued to `discovery_tasks` RabbitMQ queue
   - Worker picks it up and executes

3. **Market Research Completes**
   - ✅ Does NOT require approval
   - Automatically moves to next task: `create_brand_identity`

4. **Brand Identity Completes**
   - ⏸️ REQUIRES approval
   - Status set to `pending_approval`
   - Waits for user approval via `/projects/{project_id}/approve_phase`

5. **After Brand Identity Approved**
   - Automatically moves to next task: `write_prd`

6. **PRD Completes**
   - ⏸️ REQUIRES approval
   - Status set to `pending_approval`
   - Waits for user approval

7. **After PRD Approved**
   - Discovery phase complete
   - Moves to Design phase: `create_ui_ux_mockups`

## Important Notes

- **Market Research** does NOT require approval - it completes automatically
- **Brand Identity** and **PRD** DO require approval - they wait for user approval
- Tasks that don't require approval automatically progress to the next task
- Tasks that require approval wait until user approves via the API

## Testing Without Supabase

Currently, the endpoint returns success but doesn't actually create tasks (Supabase is commented out). To test:

1. Uncomment Supabase initialization in `routes/projects/projects.py`
2. Set up Supabase database with required tables
3. Start RabbitMQ
4. Start worker: `python agents/runner.py`
5. Call `/projects/start` endpoint

## Next Steps

1. Set up Supabase database
2. Uncomment Supabase code
3. Test full flow end-to-end

