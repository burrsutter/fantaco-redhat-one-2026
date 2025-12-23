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
                "url": os.getenv("CUSTOMER_MCP_SERVER_URL", "http://localhost:9001/mcp"),
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
        # The search_customers tool expects optional parameters like contact_name, company_name, etc.
        # For "find company Lonesome Pine Restaurant" we search by company_name
        result = await tool.ainvoke({"company_name": "Lonesome Pine Restaurant"})
        return {"tool_result": result}

    g = StateGraph(State)
    g.add_node("call_tool", call_tool)
    g.set_entry_point("call_tool")
    g.add_edge("call_tool", END)
    graph = g.compile()

    out = await graph.ainvoke({"user_input": "find company Lonesome Pine Restaurant"})
    print("\nRaw Result:\n", out["tool_result"])

    # Parse and display the company ID and name
    if out["tool_result"]:
        result_text = out["tool_result"][0]['text']
        data = json.loads(result_text)
        if data['results']:
            customer = data['results'][0]
            print(f"\n--- Parsed Result ---")
            print(f"Company ID: {customer['customerId']}")
            print(f"Company Name: {customer['companyName']}")
            print(f"Contact Name: {customer['contactName']}")
            print(f"Contact Title: {customer['contactTitle']}")
        else:
            print("\nNo results found")


if __name__ == "__main__":
    asyncio.run(main())