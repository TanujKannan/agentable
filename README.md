# Agentable

**AI Crew Manager** - A real-time platform for orchestrating intelligent AI agent teams using CrewAI and modern web technologies.

![Project Status](https://img.shields.io/badge/Status-Active%20Development-green)
![License](https://img.shields.io/badge/License-MIT-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20CrewAI-orange)
![Frontend](https://img.shields.io/badge/Frontend-Next.js%20%2B%20TypeScript-blue)

## 🚀 Overview

Agentable is a full-stack application that transforms natural language prompts into coordinated AI agent workflows. Users describe their tasks in plain English, and the system automatically creates, configures, and executes specialized AI agents to complete complex multi-step operations.

### Key Features

- **🤖 Dynamic Agent Creation**: Converts prompts into structured CrewAI agent specifications
- **⚡ Real-time Execution**: Live WebSocket updates of agent status and progress
- **🌐 Web Browser Automation**: Integrated Browserbase for web scraping and interaction
- **🔍 Advanced Search**: Multiple search engines including Serper API and EXA semantic search
- **📊 Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS
- **🔧 Tool Ecosystem**: Extensible tool registry for adding new agent capabilities

## 🏗️ Architecture

```
agentable/
├── 🌐 frontend/           # Next.js React application
│   ├── src/app/           # App router pages
│   ├── src/components/    # UI components (shadcn/ui)
│   └── src/lib/           # API client and utilities
├── 🔧 backend/            # FastAPI Python service
│   ├── agents/            # AI agent implementations
│   ├── services/          # Core orchestration logic
│   └── tools/             # Tool registry and integrations
└── 📁 docs/               # Project documentation
```

### Technology Stack

**Backend:**
- **FastAPI** - High-performance async web framework
- **CrewAI** - Multi-agent orchestration framework
- **OpenAI GPT** - LLM for prompt-to-specification conversion
- **Browserbase** - Browser automation and web scraping
- **Serper** - Web search API integration
- **EXA** - Semantic search for high-quality research
- **DALL-E** - AI image generation capabilities
- **WebSockets** - Real-time communication

**Frontend:**
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Modern component library
- **Native WebSocket** - Real-time updates

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** - Backend runtime
- **Node.js 18+** - Frontend development
- **API Keys** - OpenAI, Browserbase, Serper, EXA accounts

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp env.template .env
# Edit .env with your API keys:
# OPENAI_API_KEY=your_openai_key_here
# BROWSERBASE_API_KEY=your_browserbase_key_here
# BROWSERBASE_PROJECT_ID=your_project_id_here
# SERPER_API_KEY=your_serper_key_here
# EXA_API_KEY=your_exa_key_here

# Start the development server
uvicorn main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Test the Integration

1. Open `http://localhost:3000` in your browser
2. Enter a test prompt: `"Research why Felix Lebrun is the best table tennis player"`
3. Click "Create AI Crew" and watch real-time execution

## 📋 API Reference

### REST Endpoints

#### `POST /api/run`
Start a new agent crew execution.

**Request:**
```json
{
  "prompt": "Research the latest AI trends using semantic search and create a summary report"
}
```

**Response:**
```json
{
  "runId": "uuid-string"
}
```

### WebSocket Events

#### Connection: `ws://localhost:8000/api/ws/{runId}`

**Event Types:**
- `agent-update` - Agent status changes and progress
- `log` - Execution logs and debugging information  
- `complete` - Final results with output data
- `error` - Error messages and failure notifications

**Example Event:**
```json
{
  "type": "agent-update",
  "message": "Agent researcher is analyzing web search results",
  "data": {}
}
```

## 🔧 Configuration

### Environment Variables

Create `.env` files in both directories:

**Backend (.env):**
```bash
# LLM Configuration
OPENAI_API_KEY=sk-proj-...

# Browser Automation
BROWSERBASE_API_KEY=bb_live_...
BROWSERBASE_PROJECT_ID=1841f00d-...

# Web Search
SERPER_API_KEY=97f540382...

# Semantic Search
EXA_API_KEY=your_exa_key_here

# Optional: Other LLM providers
ANTHROPIC_API_KEY=sk-ant-...
COHERE_API_KEY=...
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Tool Configuration

The system supports multiple AI tools through the tool registry:

```python
# backend/tools/tool_registry.py
TOOL_REGISTRY = {
    "browserbase_tool": BrowserbaseLoadTool,
    "website_search_tool": WebsiteSearchTool, 
    "serper_dev_tool": SerperDevTool,
    "exa_search_tool": EXASearchTool,
    "dalle_tool": create_dalle_tool,
    "code_docs_search_tool": CodeDocsSearchTool,
}
```

## 🎯 Usage Examples

### Simple Web Research
```
"Find the current stock price of Tesla and summarize recent news about the company"
```

### Semantic Search & Research
```
"Find high-quality research papers about machine learning interpretability"
"Conduct semantic search for recent developments in quantum computing"
```

### Image Generation
```
"Create an image of a futuristic city at sunset"
"Generate a logo for a tech startup"
```

### Data Collection & Analysis
```
"Visit the top 5 tech news websites, collect headlines about AI, and identify trending topics"
```

### Complex Multi-step Tasks
```
"Research competitors in the electric vehicle market, compare their market share, and create a competitive analysis report"
```

### Browser Automation
```
"Navigate to Amazon, search for wireless headphones under $100, and extract the top 10 product names with ratings"
```

## 🔍 Agent Types

The system automatically creates specialized agents based on task requirements:

- **🔍 Research Agent** - Web search, data gathering, fact-checking
- **🧠 Semantic Research Agent** - High-quality semantic search using EXA
- **🌐 Browser Agent** - Web automation, form filling, navigation
- **🎨 Image Creation Agent** - AI image generation using DALL-E
- **📊 Analysis Agent** - Data processing, pattern recognition, summarization
- **✍️ Writing Agent** - Content generation, report creation, documentation
- **🧠 Coordination Agent** - Task delegation, workflow management

## 🛠️ Development

### Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── services/
│   └── orchestrator.py     # Core crew orchestration logic
├── agents/
│   └── spec_agent.py       # Prompt-to-specification converter
├── tools/
│   └── tool_registry.py    # Tool management and instantiation
└── requirements.txt        # Python dependencies

frontend/
├── src/app/
│   ├── page.tsx            # Main application interface
│   └── layout.tsx          # Root layout component
├── src/components/ui/      # Reusable UI components
├── src/lib/
│   └── api.ts              # Backend API client
└── package.json            # Node.js dependencies
```

### Adding New Tools

1. **Install the tool package:**
```bash
pip install new-tool-package
```

2. **Register in tool registry:**
```python
# backend/tools/tool_registry.py
from new_tool_package import NewTool

TOOL_REGISTRY = {
    # ... existing tools
    "new_tool": NewTool,
}
```

3. **Update SpecAgent awareness:**
```python
# backend/agents/spec_agent.py
# Add tool description in system prompt
```

### Running Tests

**Backend:**
```bash
cd backend
pytest  # Add tests as needed
```

**Frontend:**
```bash
cd frontend  
npm test    # Add tests as needed
npm run lint
npm run build  # Verify production build
```

## 🚀 Deployment

### Backend Deployment

```bash
# Production server
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker (optional)
docker build -t agentable-backend .
docker run -p 8000:8000 agentable-backend
```

### Frontend Deployment

```bash
# Build for production
npm run build

# Deploy to Vercel (recommended)
npx vercel

# Or serve statically
npm start
```

### Environment Configuration

**Production Environment Variables:**
- Update CORS origins in `main.py`
- Use production API URLs in frontend
- Configure secure WebSocket connections (WSS)
- Set up proper logging and monitoring

## 📊 Monitoring & Debugging

### Real-time Monitoring

- **WebSocket Events** - Monitor live execution progress
- **Agent Status** - Track individual agent states
- **Error Handling** - Graceful failure recovery
- **Execution Logs** - Detailed debugging information

### Common Issues

**WebSocket Connection Failures:**
- Verify backend is running on port 8000
- Check CORS configuration
- Ensure environment variables are set

**Tool Execution Errors:**
- Validate API keys in `.env` file
- Check tool-specific error messages
- Review agent specification generation

**Agent Creation Issues:**
- Monitor SpecAgent logs for LLM failures
- Verify OpenAI API key and quota
- Check fallback mechanism activation

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Commit changes:** `git commit -m 'Add amazing feature'`
4. **Push to branch:** `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- Follow existing code style and patterns
- Add type hints for Python functions
- Use TypeScript for all frontend code
- Update documentation for new features
- Test WebSocket functionality thoroughly

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **CrewAI** - Multi-agent orchestration framework
- **Browserbase** - Browser automation platform
- **OpenAI** - Language model and image generation services
- **EXA** - High-quality semantic search platform
- **FastAPI** - High-performance web framework
- **Next.js** - React production framework
- **shadcn/ui** - Beautiful component library

---

**Built with ❤️ for the AI automation community**

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/your-username/agentable).