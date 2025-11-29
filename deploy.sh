#!/bin/bash
# Quick deployment script for Railway

set -e

echo "🚂 Deploying GIA API to Railway..."
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli || brew install railway
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway..."
    railway login
fi

# Check if project is linked
if [ ! -f ".railway/project.json" ]; then
    echo "🔗 Linking project to Railway..."
    railway init
fi

echo "📦 Setting environment variables..."
echo "   (Make sure to set these in Railway dashboard if not already set)"
echo "   - RABBITMQ_URL"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_KEY"
echo "   - WORKER_QUEUES"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

echo "🚀 Deploying..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Check status:"
echo "   railway status"
echo ""
echo "📝 View logs:"
echo "   railway logs --service web"
echo "   railway logs --service worker"
echo ""
echo "🌐 Your API should be available at:"
railway domain

