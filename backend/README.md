# Agentable Backend

FastAPI backend service for the AI Agent-Team Builder project. This service orchestrates AI agent teams using CrewAI and provides real-time updates via WebSockets.

## Backend Status

### ✅ **Completed Components**

- **POST /api/run endpoint**: Accepts prompt, returns runId, starts background processing
- **WebSocket /api/ws/{run_id} endpoint**: Real-time event broadcasting to frontend
- **SpecAgent**: Converts user prompts to CrewAI specifications using OpenAI GPT-3.5
- **Orchestrator service**: Manages full execution flow from prompt to completion
- **CrewAI integration**: Dynamic agent/task creation from generated specifications
- **WebSocket connection management**: Handles multiple concurrent connections
- **CORS configuration**: Ready for frontend integration at localhost:3000
- **Requirements.txt**: All Python dependencies specified
- **Error handling**: Fallbacks for LLM failures and connection issues

### ⚠️ **Known Limitations**

- **Tool Implementation Gap**: SpecAgent references tools (`search`, `llm`) but actual tool implementations are pending (Tools Team responsibility)
- **Environment Setup**: No `.env` template provided yet
- **Health Check**: No dedicated health endpoint for monitoring
- **Testing**: Limited testing examples provided

### 🔧 **Ready for Integration**

- **Frontend**: Can immediately connect to `/api/run` and `/api/ws/{run_id}`
- **Real-time Events**: Broadcasting `agent-update`, `log`, `complete`, `error` events
- **Non-blocking**: Background processing doesn't block API responses
- **Spec Generation**: SpecAgent produces valid CrewAI task specifications

### 📋 **Next Steps for Other Teams**

- **Tools Team**: Implement actual search/LLM tools referenced in agent specifications
- **Frontend Team**: Connect to WebSocket events and handle real-time updates
- **DevOps**: Set up environment configuration and deployment

## Features

- **Dynamic Agent Orchestration**: Converts user prompts into executable agent workflows
- **Real-time Updates**: WebSocket broadcasting of agent status and logs
- **SpecAgent Integration**: LLM-powered conversion of natural language to structured tasks
- **CrewAI Framework**: Leverages CrewAI for robust multi-agent execution

## Architecture

```
/backend/
├── main.py                 # FastAPI app with endpoints
├── services/
│   └── orchestrator.py     # Main orchestration logic
├── agents/
│   └── spec_agent.py       # Prompt-to-spec conversion agent
└── requirements.txt        # Python dependencies
```

## API Endpoints

### POST /api/run
Accepts a user prompt and starts agent execution.

**Request:**
```json
{
  "prompt": "List the provinces of Afghanistan and analyze sentiment"
}
```

**Response:**
```json
{
  "runId": "uuid-string"
}
```

### WebSocket /api/ws/{run_id}
Real-time event streaming for a specific run.

**Event Types:**
- `agent-update`: Agent status changes (pending, running, done, error)
- `log`: Execution logs and messages
- `complete`: Final results with outputRef
- `error`: Error messages

## Flow

1. **Prompt Submission**: User submits prompt via POST /api/run
2. **SpecAgent Processing**: Converts prompt to CrewAI task specification
3. **Crew Creation**: Dynamically creates agents and tasks from specification
4. **Execution**: Runs CrewAI crew with real-time status updates
5. **Completion**: Returns final results via WebSocket

## Setup

### Prerequisites
- Python 3.8+
- OpenAI API key (for SpecAgent)
- Fly.io account and API token (for cloud execution)

### Installation

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
# Copy the template and fill in your values
cp env.template .env

# Or set manually:
export OPENAI_API_KEY="your-openai-api-key"
export FLY_API_TOKEN="your-fly-api-token"
export FLY_APP_NAME="your-app-name"
export FLY_ORG_SLUG="your-org-slug"
```

3. **Run the server:**
```bash
uvicorn main:app --reload --port 8000
```

The server will start at `http://localhost:8000`

### Cloud Execution with Fly Machines

The backend automatically detects if Fly Machines API credentials are configured:

- **With Fly credentials**: Tasks execute on temporary Fly Machines with real-time log streaming
- **Without Fly credentials**: Tasks execute using the local CrewAI orchestrator

To enable cloud execution:
1. Get your Fly API token from https://fly.io/user/personal_access_tokens
2. Set the required environment variables (see `env.template`)
3. Restart the server

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for SpecAgent LLM functionality and DALL-E image generation
- `SERPER_API_KEY`: Required for web search functionality (get free key at https://serper.dev)
- `PORT`: Server port (default: 8000)

### CORS Settings
Configured to allow requests from `http://localhost:3000` (Next.js frontend).

## SpecAgent

The SpecAgent converts natural language prompts into structured CrewAI specifications:

**Input:** "Research AI trends and create a summary report"

**Output:**
```json
{
  "tasks": [
    {
      "id": "researchTask",
      "agent": "DataAgent", 
      "description": "Research AI trends",
      "expected_output": "List of current AI trends",
      "params": {
        "tool": "search",
        "limit": 10
      }
    },
    {
      "id": "analysisTask",
      "agent": "AnalysisAgent",
      "description": "Create summary report",
      "expected_output": "Comprehensive summary report", 
      "params": {
        "method": "summarize"
      }
    }
  ]
}
```

## Agent Types

The system supports various agent types:
- **DataAgent**: Data fetching and search operations
- **AnalysisAgent**: Data analysis and processing
- **ResearchAgent**: Research and investigation tasks
- **WritingAgent**: Content generation and writing
- **ImageAgent**: Image generation using DALL-E AI

## Available Tools

The system includes the following tools that agents can use:

### Search Tools
- **serper_dev_tool**: Web search and research using Serper API
- **website_search_tool**: Website content search and analysis
- **code_docs_search_tool**: Code documentation search

### Image Generation Tools
- **dalle_tool**: AI image generation using DALL-E
  - Model: `dall-e-3` (more reliable)
  - Size: `1024x1024`
  - Quality: `standard`
  - Images per request: 1
  - Usage: Include image generation requests in prompts

### Usage Examples

**Text-based tasks:**
```
"Research the latest AI trends and create a summary report"
```

**Image generation tasks:**
```
"Create an image of a futuristic city at sunset"
"Generate a logo for a tech startup"
"Design a landscape with mountains and a lake"
```

**Combined tasks:**
```
"Research renewable energy and create an infographic about solar power"
```

## Error Handling

- **SpecAgent Fallback**: If LLM fails, uses default task specification
- **WebSocket Resilience**: Automatic connection cleanup on disconnect
- **Graceful Degradation**: Continues operation even if individual agents fail

## Development

### Project Structure
```
backend/
├── main.py              # FastAPI application
├── services/
│   ├── __init__.py
│   └── orchestrator.py  # Main orchestration logic
├── agents/
│   ├── __init__.py
│   └── spec_agent.py    # LLM-powered spec generation
├── requirements.txt     # Dependencies
└── README.md           # This file
```

### Adding New Agents
1. Create agent class in `agents/` directory
2. Update SpecAgent to recognize new agent type
3. Add appropriate tool integrations

### Testing
```bash
# Test the API endpoints
curl -X POST http://localhost:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test prompt"}'
```

## Integration

This backend integrates with:
- **Frontend**: Next.js application at `http://localhost:3000`
- **CrewAI**: Multi-agent framework for task execution
- **OpenAI**: LLM services for prompt processing

## Deployment

For production deployment:
1. Set production environment variables
2. Configure reverse proxy (nginx/Apache)
3. Use production WSGI server (gunicorn)
4. Set appropriate CORS origins

## Contributing

1. Follow existing code structure
2. Add type hints for new functions
3. Update this README for significant changes
4. Test WebSocket functionality thoroughly 