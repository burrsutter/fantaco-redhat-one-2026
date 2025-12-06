import asyncio
from typing import Annotated, TypedDict, Optional
import json

import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel

from config import settings

app = FastAPI(title="Super Agent", version="1.0.0")


# State definition for LangGraph
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    mcp_result: Optional[dict]


# Request/Response models
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


# MCP Tool calling function
async def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Call an MCP tool via HTTP request"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            async with session.post(
                settings.mcp_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                return result
    except Exception as e:
        return {"error": str(e)}


# Initialize the LLM with environment-configured model server
def get_llm():
    return ChatOpenAI(
        base_url=settings.model_server_url,
        model=settings.model_name,
        api_key=settings.api_key,
        streaming=True,
        use_responses_api=True,
    )


# MCP Tool node function
async def mcp_tool_node(state: AgentState) -> AgentState:
    """Node that calls MCP tools to find customer information"""
    # Extract email from the user's message if present
    user_message = state["messages"][-1].content if state["messages"] else ""

    # For demo purposes, we'll extract email or use a default
    # In production, you'd parse the message more intelligently
    import re
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', user_message)

    if email_match:
        email = email_match.group(0)
        # Call the MCP tool
        result = await call_mcp_tool("find_customer_by_email", {"email": email})
        return {"mcp_result": result}

    return {"mcp_result": None}


# Agent node function
async def agent_node(state: AgentState) -> AgentState:
    llm = get_llm()

    # Include MCP results in the context if available
    messages = state["messages"].copy()
    if state.get("mcp_result"):
        mcp_context = f"\n\nCustomer Information from Database:\n{json.dumps(state['mcp_result'], indent=2)}"
        # Add MCP result as system context
        messages.append(("system", mcp_context))

    response = await llm.ainvoke(messages)
    return {"messages": [response]}


# Build the LangGraph
def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("mcp_tool", mcp_tool_node)
    graph.add_node("agent", agent_node)
    graph.add_edge(START, "mcp_tool")
    graph.add_edge("mcp_tool", "agent")
    graph.add_edge("agent", END)
    return graph.compile()


# Create the compiled graph
agent_graph = build_graph()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        initial_state = {"messages": [("user", request.message)], "mcp_result": None}
        result = await agent_graph.ainvoke(initial_state)
        response_content = result["messages"][-1].content
        return ChatResponse(response=response_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        try:
            initial_state = {"messages": [("user", request.message)], "mcp_result": None}
            async for event in agent_graph.astream_events(initial_state, version="v2"):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        yield f"data: {chunk.content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "super_agent:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
