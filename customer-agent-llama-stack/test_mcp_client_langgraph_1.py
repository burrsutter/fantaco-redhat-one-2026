#!/usr/bin/env python3
"""
LangGraph-based MCP client that creates a stateful agent workflow.

This client connects to the MCP server and uses LangGraph to create a
sophisticated agent that can:
- Maintain conversation state
- Use MCP tools through a LangGraph workflow
- Handle multi-turn conversations
"""

import os
import json
import logging
import requests
from typing import Annotated, TypedDict, Literal
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MCP Server Configuration
MCP_URL = "http://127.0.0.1:8000/mcp"
MCP_SESSION_ID = None


class MCPClient:
    """Wrapper for MCP server communication"""

    def __init__(self, url: str):
        self.url = url
        self.session_id = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        self.initialize_session()

    def initialize_session(self):
        """Initialize MCP session"""
        init_payload = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "langgraph-client", "version": "1.0"}
            },
            "id": 1
        }

        response = requests.post(self.url, headers=self.headers, json=init_payload)
        self.session_id = response.headers.get('mcp-session-id')

        if self.session_id:
            self.headers['mcp-session-id'] = self.session_id
            print(f"✅ MCP Session initialized: {self.session_id}\n")
        else:
            raise Exception("Failed to initialize MCP session")

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool"""
        call_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 3
        }

        logger.info(f"📤 Sending MCP request to tool '{tool_name}'")
        logger.info(f"📤 MCP Payload: {json.dumps(call_payload, indent=2)}")
        logger.info(f"📤 Tool Arguments: {json.dumps(arguments, indent=2)}")

        response = requests.post(self.url, headers=self.headers, json=call_payload)

        logger.info(f"📥 Received MCP response (status: {response.status_code})")

        # Parse SSE response
        text = response.text
        logger.info(f"📥 Raw response text (first 500 chars): {text[:500]}...")

        lines = text.split('\n')
        for line in lines:
            if line.startswith('data: '):
                data = json.loads(line[6:])
                logger.info(f"📥 Parsed MCP data: {json.dumps(data, indent=2)}")
                if 'result' in data:
                    if 'content' in data['result']:
                        result_text = data['result']['content'][0]['text']
                        logger.info(f"📥 Extracted result from 'content': {result_text[:200]}...")
                        return result_text
                    elif 'structuredContent' in data['result']:
                        result_text = data['result']['structuredContent']['result']
                        logger.info(f"📥 Extracted result from 'structuredContent': {result_text[:200]}...")
                        return result_text

        logger.error("❌ Error: Could not parse MCP response")
        return "Error: Could not parse MCP response"


# Initialize MCP client
mcp_client = MCPClient(MCP_URL)


# Create LangGraph tools that wrap MCP functionality
@tool
def search_customer(query: str) -> str:
    """
    Search for customer information using the customer agent.

    Args:
        query: The search query (customer name, email, company, etc.)

    Returns:
        Customer information or search results
    """
    print(f"\n🔍 Calling MCP customer_agent with query: {query}")
    result = mcp_client.call_tool("customer_agent", {"prompt": query})
    print(f"📥 MCP Response received\n")
    return result


@tool
def get_customer_detailed(query: str) -> str:
    """
    Get detailed customer information with execution trace.

    Args:
        query: The customer query

    Returns:
        Detailed customer information with trace
    """
    print(f"\n🔍 Calling MCP customer_agent_detailed with query: {query}")
    result = mcp_client.call_tool("customer_agent_detailed", {"prompt": query})
    print(f"📥 MCP Detailed Response received\n")
    return result


# Define the agent state
class AgentState(TypedDict):
    """State for the customer service agent"""
    messages: Annotated[list[BaseMessage], add_messages]


# Initialize the LLM
llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
    temperature=0
)

# Bind tools to the LLM
tools = [search_customer, get_customer_detailed]
llm_with_tools = llm.bind_tools(tools)


# Define agent node
def agent_node(state: AgentState) -> AgentState:
    """The main agent that decides what to do"""
    print("\n🤖 Agent thinking...")

    # Log the messages being sent to the LLM
    logger.info("=" * 80)
    logger.info("📤 SENDING TO LLM - Full conversation context:")
    logger.info("=" * 80)
    for i, msg in enumerate(state["messages"], 1):
        msg_type = type(msg).__name__
        logger.info(f"\nMessage {i} ({msg_type}):")
        logger.info(f"  Content: {msg.content}")
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            logger.info(f"  Tool Calls: {msg.tool_calls}")
        if hasattr(msg, 'tool_call_id'):
            logger.info(f"  Tool Call ID: {msg.tool_call_id}")
    logger.info("=" * 80)

    response = llm_with_tools.invoke(state["messages"])

    logger.info("\n📥 LLM Response:")
    logger.info(f"  Content: {response.content}")
    if hasattr(response, 'tool_calls') and response.tool_calls:
        logger.info(f"  Tool Calls Requested: {response.tool_calls}")

    return {"messages": [response]}


# Define tool execution node
def tool_node(state: AgentState) -> AgentState:
    """Execute tools requested by the agent"""
    messages = state["messages"]
    last_message = messages[-1]

    tool_calls = last_message.tool_calls
    if not tool_calls:
        return {"messages": []}

    logger.info(f"\n🔧 Executing {len(tool_calls)} tool call(s)")

    tool_messages = []
    for i, tool_call in enumerate(tool_calls, 1):
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        logger.info(f"\n🔧 Tool Call {i}:")
        logger.info(f"  Name: {tool_name}")
        logger.info(f"  Arguments: {json.dumps(tool_args, indent=4)}")

        # Execute the tool
        if tool_name == "search_customer":
            result = search_customer.invoke(tool_args)
        elif tool_name == "get_customer_detailed":
            result = get_customer_detailed.invoke(tool_args)
        else:
            result = f"Unknown tool: {tool_name}"

        logger.info(f"  ✅ Tool Result (first 200 chars): {str(result)[:200]}...")

        # Create tool message
        tool_message = ToolMessage(
            content=str(result),
            tool_call_id=tool_call["id"]
        )
        tool_messages.append(tool_message)

    return {"messages": tool_messages}


# Define routing logic
def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Determine if we should continue to tools or end"""
    messages = state["messages"]
    last_message = messages[-1]

    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "end"


# Build the graph
def create_agent_graph():
    """Create the LangGraph workflow"""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()


def run_conversation(agent_graph, queries: list[str]):
    """Run a conversation with the agent"""
    print("\n" + "="*80)
    print("🚀 Starting LangGraph Customer Service Agent")
    print("="*80)

    state = {"messages": []}

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"📝 Query {i}: {query}")
        print("="*80)

        # Add human message
        state["messages"].append(HumanMessage(content=query))

        # Run the agent
        result = agent_graph.invoke(state)
        state = result

        # Print the final response
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage):
            print(f"\n💬 Agent Response:")
            print(f"{last_message.content}\n")


def main():
    """Main function to run the LangGraph agent"""

    # Create the agent graph
    print("🔧 Building LangGraph agent workflow...")
    agent_graph = create_agent_graph()
    print("✅ Agent workflow ready!\n")

    # Example queries to test
    queries = [
        "Search for contact name Thomas Hardy"   
    ]

    # Run the conversation
    run_conversation(agent_graph, queries)

    print("\n" + "="*80)
    print("✨ Conversation Complete!")
    print("="*80)


if __name__ == "__main__":
    main()
