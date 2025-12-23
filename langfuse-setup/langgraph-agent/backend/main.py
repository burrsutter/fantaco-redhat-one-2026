# main.py
import os
import uuid
import logging
from typing import TypedDict, Annotated, Sequence, Any, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langfuse.langchain import CallbackHandler

# Configure logging
from pathlib import Path
from datetime import datetime

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Create log filename with timestamp
log_filename = logs_dir / f"langgraph_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to: {log_filename}")


# ============================================================================
# Configuration
# ============================================================================

# Load environment variables from .env file
load_dotenv()

# LLM Configuration
API_KEY = os.getenv("API_KEY")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "gpt-4o-mini")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

# MCP Server Configuration
CUSTOMER_MCP_SERVER_URL = os.getenv("CUSTOMER_MCP_SERVER_URL", "http://localhost:9001/mcp")
FINANCE_MCP_SERVER_URL = os.getenv("FINANCE_MCP_SERVER_URL", "http://localhost:9002/mcp")

# Application Configuration
PORT = int(os.getenv("PORT", "8002"))

# Set Langfuse environment variables for v3.x compatibility
os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = LANGFUSE_BASE_URL


# ============================================================================
# MCP Server Client Functions
# ============================================================================

async def call_customer_mcp(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Call the Customer MCP server."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                CUSTOMER_MCP_SERVER_URL,
                json={"method": method, "params": params or {}},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error calling Customer MCP server: {e}")
            return {"error": str(e)}


async def call_finance_mcp(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Call the Finance MCP server."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                FINANCE_MCP_SERVER_URL,
                json={"method": method, "params": params or {}},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error calling Finance MCP server: {e}")
            return {"error": str(e)}


@tool
async def search_customers(
    company_name: str = None,
    contact_name: str = None,
    contact_email: str = None,
    phone: str = None
) -> str:
    """Search for customers by various fields with partial matching.

    Args:
        company_name: Filter by company name (partial matching, optional)
        contact_name: Filter by contact person name (partial matching, optional)
        contact_email: Filter by contact email address (partial matching, optional)
        phone: Filter by phone number (partial matching, optional)

    Returns:
        List of customers matching the search criteria as a JSON string
    """
    params = {}
    if company_name:
        params["company_name"] = company_name
    if contact_name:
        params["contact_name"] = contact_name
    if contact_email:
        params["contact_email"] = contact_email
    if phone:
        params["phone"] = phone

    result = await call_customer_mcp("search_customers", params)
    return str(result)


@tool
async def get_customer_info(customer_id: str) -> str:
    """Get customer information from the Customer MCP server.

    Args:
        customer_id: The ID of the customer to retrieve information for

    Returns:
        Customer information as a JSON string
    """
    result = await call_customer_mcp("get_customer", {"customer_id": customer_id})
    return str(result)


@tool
async def get_finance_data(account_id: str) -> str:
    """Get financial data from the Finance MCP server.

    Args:
        account_id: The ID of the account to retrieve financial data for

    Returns:
        Financial data as a JSON string
    """
    result = await call_finance_mcp("get_account", {"account_id": account_id})
    return str(result)


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
        model=INFERENCE_MODEL,
        temperature=0.7,
        api_key=API_KEY,
        base_url=BASE_URL,
        callbacks=[langfuse_handler]
    )

    # Bind MCP tools to the LLM
    tools = [search_customers, get_customer_info, get_finance_data]
    llm_with_tools = llm.bind_tools(tools)

    # Call the LLM (this will be traced in Langfuse)
    # Pass session_id and user_id as metadata
    response = llm_with_tools.invoke(
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
# Tool Execution Node
# ============================================================================

# Map of tool names to tool functions
TOOL_MAP = {
    "search_customers": search_customers,
    "get_customer_info": get_customer_info,
    "get_finance_data": get_finance_data
}


def execute_tools(state: AgentState) -> AgentState:
    """Execute tools based on tool calls in the last message."""
    import asyncio
    import concurrent.futures

    messages = state["messages"]
    last_message = messages[-1]

    tool_messages = []

    if hasattr(last_message, 'tool_calls'):
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

            # Get the tool function
            tool_func = TOOL_MAP.get(tool_name)
            if tool_func:
                try:
                    # Run async tool in a thread pool to avoid event loop issues
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            tool_func.ainvoke(tool_args)
                        )
                        result = future.result(timeout=30)

                    tool_messages.append(
                        ToolMessage(
                            content=result,
                            tool_call_id=tool_call["id"]
                        )
                    )
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error: {str(e)}",
                            tool_call_id=tool_call["id"]
                        )
                    )

    return {"messages": tool_messages}


# ============================================================================
# Create Agent Graph
# ============================================================================

def should_continue(state: AgentState) -> str:
    """Determine if we should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, continue to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    # Otherwise, end
    return "end"


def create_agent_graph():
    """Create a LangGraph workflow with tool execution."""

    # Initialize the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", execute_tools)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")

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
    logger.info(f"BASE_URL: {BASE_URL}")
    logger.info(f"INFERENCE_MODEL: {INFERENCE_MODEL}")
    logger.info(f"LANGFUSE_BASE_URL: {LANGFUSE_BASE_URL}")
    logger.info(f"CUSTOMER_MCP_SERVER_URL: {CUSTOMER_MCP_SERVER_URL}")
    logger.info(f"FINANCE_MCP_SERVER_URL: {FINANCE_MCP_SERVER_URL}")
    logger.info(f"PORT: {PORT}")
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
    🚀 Starting server on http://localhost:{PORT}
    📊 Langfuse: {LANGFUSE_BASE_URL}
    🤖 Model: {INFERENCE_MODEL}
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
    )
