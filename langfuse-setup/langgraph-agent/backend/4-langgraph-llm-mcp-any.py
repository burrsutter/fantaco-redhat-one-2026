import asyncio
import os
import sys
import json
from typing import TypedDict, Any, List, Literal

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

load_dotenv()


class State(TypedDict):
    messages: List[Any]


async def main(user_query: str):
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

    print("Available Tools:", [t.name for t in all_tools])
    print(f"\nUser Query: {user_query}")
    print("="*70)

    # Initialize LLM with tools
    llm = ChatOpenAI(
        model=os.getenv("INFERENCE_MODEL", "qwen3:14b-q8_0"),
        base_url=os.getenv("BASE_URL", "http://localhost:11434/v1"),
        api_key=os.getenv("API_KEY", "not-needed"),
        temperature=0.7
    )

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(all_tools)

    # Define workflow nodes
    async def call_llm(state: State) -> State:
        """Call LLM with available tools"""
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": messages + [response]}

    async def call_tools(state: State) -> State:
        """Execute any tool calls requested by the LLM"""
        messages = state["messages"]
        last_message = messages[-1]

        tool_messages = []
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            print(f"\n[Tool Execution] LLM requested {len(last_message.tool_calls)} tool call(s)")

            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                print(f"  - Calling {tool_name} with args: {tool_args}")

                # Find the tool
                tool = next((t for t in all_tools if t.name == tool_name), None)
                if tool:
                    try:
                        result = await tool.ainvoke(tool_args)
                        result_text = result[0]['text'] if isinstance(result, list) else str(result)
                        print(f"    Result: {result_text[:100]}..." if len(result_text) > 100 else f"    Result: {result_text}")

                        tool_messages.append(
                            ToolMessage(
                                content=result_text,
                                tool_call_id=tool_call["id"],
                                name=tool_name
                            )
                        )
                    except Exception as e:
                        print(f"    Error: {str(e)}")
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

    result = await graph.ainvoke({
        "messages": [
            system_message,
            HumanMessage(content=user_query)
        ]
    })

    # Display final response
    print("\n" + "="*70)
    print("FINAL RESPONSE:")
    print("="*70)
    if result.get("messages"):
        # Find the last AI message
        for message in reversed(result["messages"]):
            if isinstance(message, AIMessage) and message.content:
                print(message.content)
                break
    print("="*70)


if __name__ == "__main__":
    # Get user query from command line argument
    if len(sys.argv) < 2:
        print("Usage: python 4-langgraph-llm-mcp-any.py '<your query>'")
        print("\nExample queries:")
        print('  python 4-langgraph-llm-mcp-any.py "Who is Thomas Hardy and what are his orders?"')
        print('  python 4-langgraph-llm-mcp-any.py "Find orders for Lonesome Pine Restaurant"')
        print('  python 4-langgraph-llm-mcp-any.py "Search for customers in London"')
        sys.exit(1)

    user_query = " ".join(sys.argv[1:])
    asyncio.run(main(user_query))
