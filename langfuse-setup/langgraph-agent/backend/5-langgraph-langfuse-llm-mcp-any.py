import asyncio
import os
import sys
import json
import logging
from typing import TypedDict, Any, List, Literal
from datetime import datetime

from dotenv import load_dotenv
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class State(TypedDict):
    messages: List[Any]


async def main(user_query: str):
    # Initialize Langfuse CallbackHandler
    langfuse_handler = CallbackHandler(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_BASE_URL"),
        session_id=f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        user_id="cli_user",
        tags=["mcp", "langgraph", "customer-service"],
        metadata={
            "query": user_query
        }
    )

    logger.info(f"Langfuse enabled: {os.getenv('LANGFUSE_BASE_URL')}")
    logger.info(f"Session ID: {langfuse_handler.get_trace_id()}")

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

    # Get tools from both servers
    customer_tools = await customer_mcp.get_tools()
    finance_tools = await finance_mcp.get_tools()

    all_tools = customer_tools + finance_tools

    logger.info(f"Available Tools: {[t.name for t in all_tools]}")
    logger.info(f"User Query: {user_query}")
    logger.info("="*70)

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
                HumanMessage(content=user_query)
            ]
        },
        config={"callbacks": [langfuse_handler]}
    )

    # Display final response
    logger.info("="*70)
    logger.info("FINAL RESPONSE:")
    logger.info("="*70)
    final_response = ""
    if result.get("messages"):
        # Find the last AI message
        for message in reversed(result["messages"]):
            if isinstance(message, AIMessage) and message.content:
                final_response = message.content
                print(final_response)  # Print final response to user (not logger)
                break
    logger.info("="*70)

    # Flush Langfuse to ensure all data is sent
    langfuse_handler.flush()

    trace_url = f"{os.getenv('LANGFUSE_BASE_URL')}/trace/{langfuse_handler.get_trace_id()}"
    logger.info(f"✓ Trace logged to Langfuse: {trace_url}")


if __name__ == "__main__":
    # Get user query from command line argument
    if len(sys.argv) < 2:
        logger.error("No query provided")
        print("Usage: python 5-langgraph-langfuse-llm-mcp-any.py '<your query>'")
        print("\nExample queries:")
        print('  python 5-langgraph-langfuse-llm-mcp-any.py "Who is Thomas Hardy and what are his orders?"')
        print('  python 5-langgraph-langfuse-llm-mcp-any.py "Find orders for Lonesome Pine Restaurant"')
        print('  python 5-langgraph-langfuse-llm-mcp-any.py "Search for customers in London"')
        sys.exit(1)

    user_query = " ".join(sys.argv[1:])

    try:
        asyncio.run(main(user_query))
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)
