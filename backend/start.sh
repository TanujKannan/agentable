#!/bin/bash

# Start script for Agentable backend
echo "🚀 Starting Agentable backend..."

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set. Please set it for full functionality:"
    echo "   export OPENAI_API_KEY='your-api-key'"
    echo "   Note: Required for SpecAgent and Dall-E image generation"
    echo ""
fi

# Check if SERPER_API_KEY is set for search functionality
if [ -z "$SERPER_API_KEY" ]; then
    echo "⚠️  Warning: SERPER_API_KEY not set. Search tools may not work properly."
    echo "   Get a free key at https://serper.dev and set:"
    echo "   export SERPER_API_KEY='your-serper-key'"
    echo ""
fi

echo "✅ Tools available:"
python -c "from tools.tool_registry import get_tool_names; print('  -', '\n  - '.join(get_tool_names()))"

echo ""
echo "🎨 New: Dall-E image generation tool added!"
echo "   - Model: dall-e-3 (more reliable)"
echo "   - Size: 1024x1024"
echo "   - Quality: standard"
echo "   - Usage: Include image generation requests in your prompts"
echo ""
echo "🌐 Starting server on http://localhost:8000"
echo "📱 Frontend should run on http://localhost:3000"
echo ""

uvicorn main:app --reload --port 8000