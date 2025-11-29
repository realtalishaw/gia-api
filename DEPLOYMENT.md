# Railway Deployment Guide

This guide shows how to deploy GIA API to Railway with both the API server and worker running.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Railway CLI**: Install the Railway CLI
   ```bash
   npm install -g @railway/cli
   # OR
   brew install railway
   ```

## Deployment Options

### Option 1: Deploy via Railway Dashboard (Recommended for First Time)

1. **Create New Project**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `gia-api` repository

2. **Configure Services**
   Railway will automatically detect the `Procfile` and create two services:
   - `web`: API server (FastAPI)
   - `worker`: Background worker (RabbitMQ consumer)

3. **Add Environment Variables**
   In Railway dashboard, go to Variables tab and add:
   ```
   RABBITMQ_URL=amqp://guest:guest@your-rabbitmq-host:5672/
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   WORKER_QUEUES=discovery_tasks,build_tasks,agent_execution,deployment_tasks
   PORT=8000  # Railway sets this automatically, but you can override
   ```

4. **Add RabbitMQ Service**
   - In Railway dashboard, click "New" → "Database"
   - Select "RabbitMQ" (or use Railway's RabbitMQ addon)
   - Railway will provide connection URL automatically
   - Update `RABBITMQ_URL` environment variable

5. **Deploy**
   - Railway will automatically deploy on git push
   - Or click "Deploy" in dashboard

### Option 2: Deploy via CLI

1. **Login to Railway**
   ```bash
   railway login
   ```

2. **Initialize Project**
   ```bash
   cd /path/to/gia-api
   railway init
   ```
   This will:
   - Link your local project to Railway
   - Create a new Railway project (or link to existing)
   - Set up deployment configuration

3. **Set Environment Variables**
   ```bash
   # Set RabbitMQ URL (if using Railway's RabbitMQ)
   railway variables set RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/"
   
   # Set Supabase credentials
   railway variables set SUPABASE_URL="https://your-project.supabase.co"
   railway variables set SUPABASE_KEY="your-supabase-anon-key"
   
   # Set worker queues
   railway variables set WORKER_QUEUES="discovery_tasks,build_tasks,agent_execution,deployment_tasks"
   ```

4. **Deploy**
   ```bash
   railway up
   ```
   This will:
   - Build your application
   - Deploy both `web` and `worker` services
   - Show deployment logs

5. **Check Status**
   ```bash
   railway status
   railway logs
   ```

## Service Configuration

Railway will automatically detect your `Procfile` and create:

### Web Service (API)
- **Process**: `web`
- **Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Port**: Railway sets `$PORT` automatically
- **Health Check**: Railway will check `/health` endpoint

### Worker Service
- **Process**: `worker`
- **Command**: `python agents/runner.py`
- **Runs**: Continuously, consuming from RabbitMQ queues

## Environment Variables

Required environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `RABBITMQ_URL` | RabbitMQ connection string | `amqp://guest:guest@localhost:5672/` |
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJhbGc...` |
| `WORKER_QUEUES` | Comma-separated queue names | `discovery_tasks,build_tasks` |
| `PORT` | API server port (auto-set by Railway) | `8000` |

## Adding RabbitMQ to Railway

Railway doesn't have a built-in RabbitMQ service, but you can:

### Option A: Use Railway's RabbitMQ Addon (if available)
1. In Railway dashboard: "New" → "Database" → "RabbitMQ"
2. Railway provides connection URL automatically

### Option B: Use CloudAMQP (Recommended)
1. Sign up at [cloudamqp.com](https://cloudamqp.com) (free tier available)
2. Create a RabbitMQ instance
3. Copy connection URL
4. Set as `RABBITMQ_URL` in Railway variables

### Option C: Use Railway's PostgreSQL + pg_amqp (Advanced)
- More complex setup
- Not recommended for production

## Verifying Deployment

1. **Check API is running**
   ```bash
   curl https://your-app.railway.app/health
   ```

2. **Check Worker is running**
   ```bash
   railway logs --service worker
   ```
   You should see: `🚀 Worker started and waiting for tasks on queue: discovery_tasks...`

3. **Test Task Queuing**
   ```bash
   curl -X POST https://your-app.railway.app/projects/start \
     -H "Content-Type: application/json" \
     -d '{"project_id": "test-123", "project_brief": "Test project"}'
   ```

4. **Check Worker Logs**
   ```bash
   railway logs --service worker
   ```
   Should show task being processed

## Troubleshooting

### Worker Not Starting
- Check `railway logs --service worker`
- Verify `RABBITMQ_URL` is set correctly
- Ensure RabbitMQ is accessible from Railway

### Tasks Not Processing
- Verify worker service is running: `railway status`
- Check RabbitMQ connection in worker logs
- Verify queue names match in `WORKER_QUEUES`

### API Not Responding
- Check `railway logs --service web`
- Verify port is set correctly
- Check health endpoint: `/health`

## Updating Deployment

After making code changes:

```bash
# Commit changes
git add .
git commit -m "Update code"

# Push to trigger deployment
git push origin main

# Or deploy manually
railway up
```

## Monitoring

- **Logs**: `railway logs` (all services) or `railway logs --service worker` (specific service)
- **Metrics**: Railway dashboard shows CPU, memory, network usage
- **Status**: `railway status` shows service health

## Cost Considerations

Railway pricing:
- **Free tier**: $5 credit/month
- **Pay-as-you-go**: ~$0.000463/GB RAM-hour, ~$0.000231/GB storage-hour

For both services running 24/7:
- Web service: ~$5-10/month
- Worker service: ~$5-10/month
- Total: ~$10-20/month (depending on usage)

## Next Steps

1. Set up Supabase database
2. Configure RabbitMQ (CloudAMQP recommended)
3. Deploy to Railway
4. Test end-to-end flow
5. Set up monitoring and alerts

