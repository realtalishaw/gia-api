# Quick Railway Deployment

## Fastest Way: CLI Deployment

### 1. Install Railway CLI
```bash
# Option A: npm
npm install -g @railway/cli

# Option B: Homebrew (macOS)
brew install railway
```

### 2. Login
```bash
railway login
```

### 3. Initialize Project
```bash
cd /path/to/gia-api
railway init
```
This will:
- Create a new Railway project (or link to existing)
- Ask you to name it
- Set up deployment config

### 4. Set Environment Variables
```bash
# RabbitMQ (use CloudAMQP free tier: https://cloudamqp.com)
railway variables set RABBITMQ_URL="amqp://user:pass@host.rmq.cloudamqp.com/vhost"

# Supabase (when ready)
railway variables set SUPABASE_URL="https://xxx.supabase.co"
railway variables set SUPABASE_KEY="your-key"

# Worker queues
railway variables set WORKER_QUEUES="discovery_tasks,build_tasks,agent_execution,deployment_tasks"
```

### 5. Deploy
```bash
railway up
```

That's it! Railway will:
- Build your app
- Deploy both `web` and `worker` services (from Procfile)
- Show you the URL

## Or Use the Script

```bash
./deploy.sh
```

## Verify It's Working

1. **Check services are running:**
   ```bash
   railway status
   ```

2. **View logs:**
   ```bash
   # API logs
   railway logs --service web
   
   # Worker logs
   railway logs --service worker
   ```

3. **Test the API:**
   ```bash
   # Get your domain
   railway domain
   
   # Test health endpoint
   curl https://your-app.railway.app/health
   ```

## What Gets Deployed

Railway reads your `Procfile` and creates two services:

1. **`web`**: FastAPI server
   - Runs: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Handles HTTP requests

2. **`worker`**: Background worker
   - Runs: `python agents/runner.py`
   - Consumes tasks from RabbitMQ

Both run continuously and restart automatically on failure.

## Next Steps

1. Set up RabbitMQ (CloudAMQP recommended)
2. Get your RabbitMQ URL
3. Set `RABBITMQ_URL` in Railway
4. Deploy!
5. Test by calling `/projects/start`

## Troubleshooting

**Worker not starting?**
- Check logs: `railway logs --service worker`
- Verify `RABBITMQ_URL` is correct
- Make sure RabbitMQ is accessible

**Can't connect to RabbitMQ?**
- Railway services can't access `localhost` RabbitMQ
- Use CloudAMQP or Railway's RabbitMQ addon
- Make sure URL includes credentials

**Services not showing?**
- Railway auto-detects `Procfile`
- Make sure `Procfile` is in root directory
- Check `railway status` to see all services

