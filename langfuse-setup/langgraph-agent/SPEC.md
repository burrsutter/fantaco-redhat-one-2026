# LangGraph Agent with Langfuse Tracing - Simple Teaching Demo

## Overview

This is a simplified implementation for **teaching purposes** focused on demonstrating:
- **LangGraph** agent workflow
- **Langfuse** observability and tracing
- **FastAPI** backend with simple chat endpoint
- **React** frontend with minimal UI

The goal is to show how traces appear in Langfuse with minimal complexity.

## Architecture

```
┌─────────────────────────────────────────┐
│         React Frontend (Port 3002)      │
│         - Simple chat interface         │
│         - HTTP requests only            │
└─────────────────────────────────────────┘
                   │ HTTP POST
                   ▼
┌─────────────────────────────────────────┐
│      FastAPI Backend (Port 8002)        │
│  ┌───────────────────────────────────┐  │
│  │      LangGraph Agent              │  │
│  │      - Simple conversation        │  │
│  │      - Langfuse callbacks         │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  - LLM Provider (OpenAI/vLLM)           │
│  - Langfuse Server (tracing)            │
└─────────────────────────────────────────┘
```

## Technology Stack

### Backend
- Python 3.12
- FastAPI 0.115.5
- LangGraph 0.2.59
- LangChain Core 0.3.28
- LangChain OpenAI 0.2.14
- Langfuse 3.11.0+
- Uvicorn 0.34.0

### Frontend
- Node.js 18+
- React 18.2.0
- Vite 5.0.0
- Axios 1.6.0
- Tailwind CSS 3.4.0

## Backend Implementation

### 1. Simplified Project Structure

```
backend/
├── main.py              # All code in one file for simplicity
├── requirements.txt
├── .env.example
└── .env                 # Your actual credentials
```

### 2. Dependencies

```txt
# requirements.txt
fastapi==0.115.5
uvicorn==0.34.0
langgraph==0.2.59
langchain-core==0.3.28
langchain-openai==0.2.14
langfuse==3.11.0
pydantic==2.10.3
pydantic-settings==2.7.0
python-dotenv==1.0.1
httpx==0.27.0
```

### 3. Environment Configuration

```bash
# .env.example
# LLM Configuration
API_KEY=your_api_key_here
INFERENCE_MODEL=gpt-4o-mini
BASE_URL=https://api.openai.com/v1

# For vLLM instead of OpenAI, use:
# BASE_URL=http://localhost:8000/v1
# INFERENCE_MODEL=meta-llama/Llama-3.1-8B-Instruct

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_BASE_URL=https://cloud.langfuse.com

# MCP Server Configuration
CUSTOMER_MCP_SERVER_URL=http://localhost:9001/mcp
FINANCE_MCP_SERVER_URL=http://localhost:9002/mcp

# Application Configuration
PORT=8002
```

### 4. Complete Backend Implementation (main.py)

```python
# main.py
import os
import uuid
import logging
from typing import TypedDict, Annotated, Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langfuse.langchain import CallbackHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class Settings(BaseSettings):
    """Application settings from environment variables."""

    # LLM Configuration
    API_KEY: str
    INFERENCE_MODEL: str = "gpt-4o-mini"
    BASE_URL: str = "https://api.openai.com/v1"

    # Langfuse Configuration
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"

    # Application Configuration
    PORT: int = 8002

    class Config:
        env_file = ".env"


settings = Settings()

# Set Langfuse environment variables for v3.x compatibility
os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_BASE_URL


# ============================================================================
# LangGraph Agent State
# ============================================================================

class AgentState(TypedDict):
    """Simple agent state - just messages and metadata."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: str
    session_id: str


# ============================================================================
# Agent Node
# ============================================================================

def agent_node(state: AgentState) -> AgentState:
    """
    Main agent node - calls LLM with Langfuse tracing.
    This is where the magic happens for observability!
    """

    # Create Langfuse callback handler for this conversation
    # In Langfuse 3.x, credentials are read from environment variables
    # session_id and user_id are set via metadata
    langfuse_handler = CallbackHandler()

    # Initialize LLM with Langfuse callbacks
    llm = ChatOpenAI(
        model=settings.INFERENCE_MODEL,
        temperature=0.7,
        api_key=settings.API_KEY,
        base_url=settings.BASE_URL,
        callbacks=[langfuse_handler]
    )

    # Call the LLM (this will be traced in Langfuse)
    # Pass session_id and user_id as metadata
    response = llm.invoke(
        state["messages"],
        config={
            "callbacks": [langfuse_handler],
            "metadata": {
                "session_id": state["session_id"],
                "user_id": state["user_id"],
            }
        }
    )

    return {"messages": [response]}


# ============================================================================
# Create Agent Graph
# ============================================================================

def create_agent_graph():
    """Create a simple LangGraph workflow."""

    # Initialize the graph
    workflow = StateGraph(AgentState)

    # Add single node (keep it simple for teaching)
    workflow.add_node("agent", agent_node)

    # Set entry point and end
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)

    # Compile the graph
    return workflow.compile()


# ============================================================================
# FastAPI Application
# ============================================================================

# Global agent graph instance
agent_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent graph on startup."""
    global agent_graph

    # Log configuration at startup
    logger.info("=" * 60)
    logger.info("🚀 Starting LangGraph + Langfuse Demo")
    logger.info("=" * 60)
    logger.info(f"BASE_URL: {settings.BASE_URL}")
    logger.info(f"INFERENCE_MODEL: {settings.INFERENCE_MODEL}")
    logger.info(f"LANGFUSE_BASE_URL: {settings.LANGFUSE_BASE_URL}")
    logger.info(f"PORT: {settings.PORT}")
    logger.info("=" * 60)

    agent_graph = create_agent_graph()
    logger.info("✅ Agent graph initialized")
    yield
    logger.info("🛑 Shutting down")


app = FastAPI(
    title="LangGraph + Langfuse Demo",
    description="Simple demo for teaching Langfuse tracing",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Models
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request from frontend."""
    message: str
    session_id: str | None = None
    user_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response to frontend."""
    message: str
    session_id: str
    user_id: str


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Simple chat endpoint.
    Sends message to agent and returns response.
    All interactions are traced in Langfuse!
    """

    try:
        # Generate IDs if not provided
        session_id = request.session_id or str(uuid.uuid4())
        user_id = request.user_id or "anonymous"

        # Log chat invocation
        logger.info("=" * 60)
        logger.info("💬 Chat invocation")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Message: {request.message[:100]}...")  # Log first 100 chars
        logger.info("=" * 60)

        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "session_id": session_id,
            "user_id": user_id,
        }

        # Run the agent (this creates the Langfuse trace)
        logger.info("🤖 Invoking agent...")
        result = agent_graph.invoke(initial_state)

        # Extract AI response
        ai_message = result["messages"][-1]
        logger.info(f"✅ Agent response received (length: {len(ai_message.content)} chars)")
        logger.info(f"Response preview: {ai_message.content[:100]}...")

        return ChatResponse(
            message=ai_message.content,
            session_id=session_id,
            user_id=user_id
        )

    except Exception as e:
        logger.error(f"❌ Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print(f"""
    🚀 Starting server on http://localhost:{settings.PORT}
    📊 Langfuse: {settings.LANGFUSE_BASE_URL}
    🤖 Model: {settings.INFERENCE_MODEL}
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
    )
```

## Frontend Implementation

### 1. Simplified Project Structure

```
frontend/
├── src/
│   ├── App.jsx          # Single component with everything
│   ├── main.jsx         # Entry point
│   └── index.css        # Tailwind styles
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env.example
└── .env
```

### 2. Dependencies

```json
{
  "name": "langgraph-langfuse-demo",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

### 3. Environment Configuration

```bash
# .env.example
VITE_API_URL=http://localhost:8002
VITE_PORT=3002
```

### 4. Complete Frontend Implementation

#### index.html

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>LangGraph + Langfuse Demo</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

#### src/main.jsx

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

#### src/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

#### src/App.jsx

```jsx
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/v1/chat`, {
        message: input,
        session_id: sessionId,
        user_id: 'demo-user',
      });

      const aiMessage = {
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        role: 'error',
        content: 'Failed to get response. Check console and backend logs.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            LangGraph + Langfuse Demo
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Session ID: <code className="bg-gray-100 px-2 py-1 rounded text-xs">{sessionId}</code>
          </p>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-12">
              <p className="text-lg">Send a message to start chatting!</p>
              <p className="text-sm mt-2">All interactions are traced in Langfuse</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : msg.role === 'error'
                    ? 'bg-red-100 text-red-800 border border-red-300'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <p className="text-xs opacity-70 mt-2">
                  {msg.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input */}
      <footer className="bg-white border-t shadow-lg">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form onSubmit={sendMessage} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={loading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
            >
              Send
            </button>
          </form>
        </div>
      </footer>
    </div>
  );
}

export default App;
```

#### vite.config.js

```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: parseInt(process.env.VITE_PORT) || 3002,
  },
});
```

#### tailwind.config.js

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        'bounce': 'bounce 1s infinite',
      },
      keyframes: {
        bounce: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-0.5rem)' },
        },
      },
    },
  },
  plugins: [],
};
```

#### postcss.config.js

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

## Quick Start Guide

### 1. Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env with your credentials
# - Add your API_KEY
# - Add your Langfuse keys
# - Configure LANGFUSE_BASE_URL

# Run the server
python main.py
```

Backend will be available at `http://localhost:8002`

### 2. Setup Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file from example
cp .env.example .env

# Run the development server
npm run dev
```

Frontend will be available at `http://localhost:3002`

### 3. Test the Application

1. Open `http://localhost:3002` in your browser
2. Send a message in the chat
3. Check the Langfuse dashboard to see the trace

## What You'll See in Langfuse

When you send messages through the chat, Langfuse will capture:

1. **Traces**: Complete conversation flows
   - Session ID
   - User ID
   - Timestamp

2. **Spans**: Individual LLM calls
   - Input messages
   - Output messages
   - Model used
   - Token counts
   - Latency

3. **Metrics**:
   - Response times
   - Token usage
   - Cost tracking

## Teaching Points

### Key Concepts Demonstrated:

1. **Langfuse Integration**:
   - Simple `CallbackHandler` setup
   - Automatic trace creation
   - Session and user tracking

2. **LangGraph Workflow**:
   - State definition with `TypedDict`
   - Simple graph with one node
   - Message handling with `add_messages`

3. **FastAPI Backend**:
   - Environment-based configuration
   - CORS setup for local development
   - Simple REST API

4. **React Frontend**:
   - Single-component simplicity
   - Axios for HTTP requests
   - Session ID management

## Customization

### Use Different LLM Provider

For vLLM instead of OpenAI, update `.env`:

```bash
BASE_URL=http://your-vllm-server:8000/v1
INFERENCE_MODEL=meta-llama/Llama-3.1-8B-Instruct
API_KEY=not-needed-for-vllm
```

### Add More Agent Functionality

To add tools or more complex workflows, modify the `agent_node` function and graph structure in `main.py`.

## Troubleshooting

### Common Issues:

1. **CORS errors**: Make sure backend CORS allows `http://localhost:3002`
2. **Langfuse not showing traces**: Verify your Langfuse keys and BASE_URL
3. **LLM errors**: Check your API_KEY and BASE_URL are correct
4. **Port conflicts**: Change PORT in backend `.env` and VITE_API_URL in frontend `.env`

## Next Steps for Students

After understanding this basic setup:

1. Add a simple tool (e.g., current time lookup)
2. Implement conversation memory/history
3. Add user authentication
4. Explore different LLM models
5. Analyze traces in Langfuse dashboard
6. Try different prompt engineering techniques

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Langfuse Documentation](https://langfuse.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
