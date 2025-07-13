#!/bin/bash

set -e

echo "🚀 Deploying Agentable to Fly.io..."

# Deploy backend first
echo "📦 Deploying backend..."
cd backend
fly deploy
cd ..

# Deploy frontend
echo "🎨 Deploying frontend..."
cd frontend
fly deploy
cd ..

echo "✅ Deployment complete!"
echo "Backend: https://backend-holy-violet-2759.fly.dev"
echo "Frontend: https://agentable-frontend.fly.dev" 