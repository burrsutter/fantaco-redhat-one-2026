import os
import logging
from typing import TypedDict, Any, List, Literal, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langgraph.graph import StateGraph, END
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langfuse.callback import CallbackHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None   # for your UI to pass a stable chat/session id
    user_id: Optional[str] = None      # optional: if your UI has auth/user info


class ChatResponse(BaseModel):
    reply: str
    tool_result: Any = None
    trace_id: Optional[str] = None


# LangGraph State
class State(TypedDict):
    messages: List[Any]


# Global variables for MCP clients and tools
mcp_clients = {}
all_tools = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MCP clients on startup and cleanup on shutdown"""
    global mcp_clients, all_tools

    logger.info("Initializing MCP clients...")

    # Connect to both MCP servers
    customer_mcp = MultiServerMCPClient(
        {
            "customer_mcp": {
                "transport": "http",
                "url": os.getenv("CUSTOMER_MCP_SERVER_URL", "http://localhost:9001/mcp"),
            }
        }
    )

    finance_mcp = MultiServerMCPClient(
        {
            "finance_mcp": {
                "transport": "http",
                "url": os.getenv("FINANCE_MCP_SERVER_URL", "http://localhost:9002/mcp"),
            }
        }
    )

    # Store clients
    mcp_clients = {
        "customer": customer_mcp,
        "finance": finance_mcp
    }

    # Get tools from both servers
    customer_tools = await customer_mcp.get_tools()
    finance_tools = await finance_mcp.get_tools()
    all_tools = customer_tools + finance_tools

    logger.info(f"MCP clients initialized. Available tools: {[t.name for t in all_tools]}")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down MCP clients...")


# Create FastAPI app
app = FastAPI(
    title="LangGraph MCP Customer Service API",
    description="Customer service chatbot with MCP tools and Langfuse tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def process_chat(message: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> tuple[str, Optional[str]]:
    """Process a chat message and return the response with trace ID"""

    # Initialize Langfuse CallbackHandler
    langfuse_handler = CallbackHandler(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_BASE_URL"),
        session_id=session_id or f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        user_id=user_id or "api_user",
        tags=["mcp", "langgraph", "customer-service", "fastapi"],
        metadata={
            "query": message,
            "session_id": session_id,
            "user_id": user_id
        }
    )

    logger.info(f"Processing message: {message[:50]}... (Session: {session_id}, User: {user_id})")

    # Initialize LLM with tools and Langfuse callback
    llm = ChatOpenAI(
        model=os.getenv("INFERENCE_MODEL", "qwen3:14b-q8_0"),
        base_url=os.getenv("BASE_URL", "http://localhost:11434/v1"),
        api_key=os.getenv("API_KEY", "not-needed"),
        temperature=0.7,
        callbacks=[langfuse_handler]
    )

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(all_tools)

    # Counter for tracking node executions
    node_counter = {"llm": 0, "tools": 0}

    # Define workflow nodes
    async def call_llm(state: State) -> State:
        """Call LLM with available tools"""
        messages = state["messages"]
        node_counter["llm"] += 1

        logger.debug(f"[LLM Call #{node_counter['llm']}] Invoking LLM with {len(messages)} messages")
        response = await llm_with_tools.ainvoke(messages, config={"callbacks": [langfuse_handler]})

        has_tool_calls = hasattr(response, 'tool_calls') and bool(response.tool_calls)
        logger.debug(f"[LLM Call #{node_counter['llm']}] Response received. Has tool calls: {has_tool_calls}")

        return {"messages": messages + [response]}

    async def call_tools(state: State) -> State:
        """Execute any tool calls requested by the LLM"""
        messages = state["messages"]
        last_message = messages[-1]
        node_counter["tools"] += 1

        tool_messages = []
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.info(f"[Tool Execution] LLM requested {len(last_message.tool_calls)} tool call(s)")

            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(f"  Calling tool: {tool_name} with args: {tool_args}")

                # Find the tool
                tool = next((t for t in all_tools if t.name == tool_name), None)
                if tool:
                    try:
                        # Tool calls are automatically tracked by CallbackHandler
                        result = await tool.ainvoke(tool_args, config={"callbacks": [langfuse_handler]})
                        result_text = result[0]['text'] if isinstance(result, list) else str(result)

                        if len(result_text) > 100:
                            logger.debug(f"  Tool result (truncated): {result_text[:100]}...")
                        else:
                            logger.debug(f"  Tool result: {result_text}")

                        tool_messages.append(
                            ToolMessage(
                                content=result_text,
                                tool_call_id=tool_call["id"],
                                name=tool_name
                            )
                        )
                    except Exception as e:
                        logger.error(f"  Tool execution error: {str(e)}")
                        tool_messages.append(
                            ToolMessage(
                                content=f"Error: {str(e)}",
                                tool_call_id=tool_call["id"],
                                name=tool_name
                            )
                        )

        return {"messages": messages + tool_messages}

    def should_continue(state: State) -> Literal["tools", "end"]:
        """Determine if we should call tools or end"""
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return "end"

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("llm", call_llm)
    workflow.add_node("tools", call_tools)

    workflow.set_entry_point("llm")
    workflow.add_conditional_edges("llm", should_continue, {"tools": "tools", "end": END})
    workflow.add_edge("tools", "llm")  # After tools, go back to LLM

    graph = workflow.compile()

    # Run the workflow
    system_message = SystemMessage(content="""You are a helpful customer service assistant with access to customer and order information.

Available tools:
- search_customers: Search for customers by name, company, email, or phone
- get_customer: Get customer details by customer ID
- fetch_order_history: Get order history for a customer by customer ID
- fetch_invoice_history: Get invoice history for a customer by customer ID

When a user asks about a customer:
1. First search for the customer to get their customer ID
2. Then fetch their orders if needed
3. Provide a clear, friendly summary

Be concise and helpful.""")

    result = await graph.ainvoke(
        {
            "messages": [
                system_message,
                HumanMessage(content=message)
            ]
        },
        config={"callbacks": [langfuse_handler]}
    )

    # Extract final response
    final_response = ""
    if result.get("messages"):
        # Find the last AI message
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                final_response = msg.content
                break

    # Flush Langfuse to ensure all data is sent
    langfuse_handler.flush()

    trace_id = langfuse_handler.get_trace_id()
    logger.info(f"Request processed. Trace ID: {trace_id}")

    return final_response, trace_id


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LangGraph MCP Customer Service API",
        "version": "1.0.0",
        "status": "running",
        "available_tools": [t.name for t in all_tools]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mcp_clients": list(mcp_clients.keys()),
        "tools_count": len(all_tools)
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that processes user messages using LangGraph workflow

    Args:
        request: ChatRequest with message, optional session_id and user_id

    Returns:
        ChatResponse with reply, tool_result, and trace_id
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")

        # Process the chat message
        reply, trace_id = await process_chat(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id
        )

        return ChatResponse(
            reply=reply,
            trace_id=trace_id
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8002))

    logger.info(f"Starting FastAPI server on port {port}...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
