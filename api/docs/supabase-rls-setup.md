# Supabase RLS (Row Level Security) Setup

## Problem

If you're getting errors like:
```
new row violates row-level security policy for table "agents"
```

This means Row Level Security (RLS) is enabled on your `agents` table, and the current API key doesn't have permission to insert/update rows.

## Solution Options

### Option 1: Use Service Role Key (Recommended for Server-Side)

The service role key bypasses RLS and is perfect for server-side operations like agent registry sync.

1. **Get your Service Role Key:**
   - Go to your Supabase Dashboard
   - Navigate to **Settings** → **API**
   - Copy the **service_role key** (under "Project API keys" → "service_role secret")
   - ⚠️ **Keep this secret!** Never expose it in client-side code.

2. **Add to your `.env` file:**
   ```env
   SUPABASE_URL=https://your-project-ref.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   ```

3. **The registry will automatically use the service role key if available**, falling back to anon key if not.

### Option 2: Configure RLS Policies (For Anon Key)

If you want to use the anon key, you need to create RLS policies that allow inserts and updates.

#### Step 1: Create the Agents Table (if not exists)

```sql
CREATE TABLE IF NOT EXISTS agents (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  description TEXT NOT NULL,
  goal TEXT NOT NULL,
  requirements JSONB NOT NULL,
  artifacts JSONB NOT NULL,
  requires_approval BOOLEAN NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add unique constraint on name (recommended)
CREATE UNIQUE INDEX IF NOT EXISTS agents_name_unique ON agents(name);
```

#### Step 2: Enable RLS

```sql
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
```

#### Step 3: Create Policies

**Option A: Allow all operations for anon users (less secure, but works for internal APIs)**

```sql
-- Allow inserts
CREATE POLICY "Allow anon inserts on agents"
ON agents FOR INSERT
TO anon
WITH CHECK (true);

-- Allow updates
CREATE POLICY "Allow anon updates on agents"
ON agents FOR UPDATE
TO anon
USING (true)
WITH CHECK (true);

-- Allow selects
CREATE POLICY "Allow anon selects on agents"
ON agents FOR SELECT
TO anon
USING (true);
```

**Option B: More restrictive (recommended for production)**

```sql
-- Only allow inserts/updates from authenticated service role
-- This requires using service_role key
CREATE POLICY "Allow service role all operations on agents"
ON agents FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Allow public reads
CREATE POLICY "Allow public reads on agents"
ON agents FOR SELECT
TO anon
USING (true);
```

#### Step 4: Update Timestamp Trigger (Optional)

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agents_updated_at 
BEFORE UPDATE ON agents 
FOR EACH ROW 
EXECUTE FUNCTION update_updated_at_column();
```

## Recommended Approach

For server-side agent registry operations, **use the service role key** (Option 1). This is:
- ✅ More secure (key never exposed to clients)
- ✅ Simpler (no RLS policy management)
- ✅ Standard practice for backend operations
- ✅ Bypasses RLS automatically

The anon key should be reserved for client-side operations where you want RLS protection.

## Verification

After setting up, restart your application. You should see:
```
✓ Supabase client initialized successfully (service role key)
✓ Synced 20 of 20 agents to Supabase
```

Instead of RLS errors.
