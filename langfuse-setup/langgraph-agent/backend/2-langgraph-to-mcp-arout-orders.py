import asyncio
import os
import json
from typing import TypedDict, Any

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()


class State(TypedDict):
    user_input: str
    tool_result: Any


async def main():
    # Streamable HTTP (a.k.a. "http" transport in LangChain docs)
    mcp = MultiServerMCPClient(
        {
            "my_mcp": {
                "transport": "http",           # streamable-http
                "url": os.getenv("FINANCE_MCP_SERVER_URL", "http://localhost:9002/mcp"),
            }
        }
    )

    tools = await mcp.get_tools()
    if not tools:
        raise RuntimeError("No MCP tools discovered. Check the server URL/route.")

    print("Tools found:", [t.name for t in tools])
    tool = tools[0]  # simplest possible: pick the first tool

    # Print tool schema to understand expected parameters
    print(f"\nTool name: {tool.name}")
    print(f"Tool description: {tool.description}")

    async def call_tool(state: State) -> State:
        # Search for orders by customer_id (AROUT = Around the Horn)
        result = await tool.ainvoke({"customer_id": "AROUT"})
        return {"tool_result": result}

    g = StateGraph(State)
    g.add_node("call_tool", call_tool)
    g.set_entry_point("call_tool")
    g.add_edge("call_tool", END)
    graph = g.compile()

    out = await graph.ainvoke({"user_input": "find orders for AROUT"})
    print("\nRaw Result:\n", out["tool_result"])

    # Parse and display the order information
    if out["tool_result"]:
        result_text = out["tool_result"][0]['text']
        response = json.loads(result_text)
        if response.get('success') and response.get('data'):
            print(f"\n--- Parsed Results ---")
            print(f"Message: {response.get('message')}")
            print(f"Found {response.get('count')} order(s)\n")
            for order in response['data']:
                print(f"Order Number: {order.get('orderNumber', 'N/A')}")
                print(f"Order ID: {order.get('id', 'N/A')}")
                print(f"Customer ID: {order.get('customerId', 'N/A')}")
                print(f"Status: {order.get('status', 'N/A')}")
                print(f"Order Date: {order.get('orderDate', 'N/A')}")
                print(f"Total Amount: ${order.get('totalAmount', 0):.2f}")
                print("-" * 50)
        else:
            print("\nNo results found")


if __name__ == "__main__":
    asyncio.run(main())
