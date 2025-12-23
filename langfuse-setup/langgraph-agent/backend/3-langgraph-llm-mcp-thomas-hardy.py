import asyncio
import os
import json
from typing import TypedDict, Any, List
from typing_extensions import Annotated

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()


class State(TypedDict):
    messages: List[Any]
    customer_data: dict
    order_data: dict
    customer_id: str


async def main():
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

    print("Customer MCP Tools:", [t.name for t in customer_tools])
    print("Finance MCP Tools:", [t.name for t in finance_tools])

    # Get specific tools
    search_customers_tool = next((t for t in customer_tools if t.name == "search_customers"), customer_tools[0])
    fetch_orders_tool = next((t for t in finance_tools if t.name == "fetch_order_history"), finance_tools[0])

    # Initialize LLM
    llm = ChatOpenAI(
        model=os.getenv("INFERENCE_MODEL", "qwen3:14b-q8_0"),
        base_url=os.getenv("BASE_URL", "http://localhost:11434/v1"),
        api_key=os.getenv("API_KEY", "not-needed"),
        temperature=0.7
    )

    # Define workflow nodes
    async def search_customer(state: State) -> State:
        """Search for customer by contact name"""
        print("\n[Step 1] Searching for customer: Thomas Hardy")
        result = await search_customers_tool.ainvoke({"contact_name": "Thomas Hardy"})
        result_text = result[0]['text'] if isinstance(result, list) else result
        customer_data = json.loads(result_text) if isinstance(result_text, str) else result_text

        customer_id = ""
        if customer_data.get('results') and len(customer_data['results']) > 0:
            customer_id = customer_data['results'][0]['customerId']
            print(f"Found customer: {customer_data['results'][0]['contactName']} - {customer_data['results'][0]['companyName']} (ID: {customer_id})")

        return {
            **state,
            "customer_data": customer_data,
            "customer_id": customer_id
        }

    async def fetch_orders(state: State) -> State:
        """Fetch orders for the customer"""
        customer_id = state.get("customer_id", "")
        if not customer_id:
            print("\n[Step 2] No customer ID found, skipping order fetch")
            return state

        print(f"\n[Step 2] Fetching orders for customer ID: {customer_id}")
        result = await fetch_orders_tool.ainvoke({"customer_id": customer_id})
        result_text = result[0]['text'] if isinstance(result, list) else result
        order_data = json.loads(result_text) if isinstance(result_text, str) else result_text

        if order_data.get('success') and order_data.get('data'):
            print(f"Found {order_data.get('count', 0)} order(s)")

        return {
            **state,
            "order_data": order_data
        }

    async def generate_response(state: State) -> State:
        """Use LLM to generate a natural language response"""
        print("\n[Step 3] Generating LLM response...")

        # Prepare context for LLM
        customer_info = ""
        if state.get("customer_data") and state["customer_data"].get('results'):
            customer = state["customer_data"]['results'][0]
            customer_info = f"""
Customer Information:
- Name: {customer.get('contactName')}
- Title: {customer.get('contactTitle')}
- Company: {customer.get('companyName')}
- Company ID: {customer.get('customerId')}
- Email: {customer.get('contactEmail')}
- Location: {customer.get('city')}, {customer.get('country')}
"""

        order_info = ""
        if state.get("order_data") and state["order_data"].get('success'):
            orders = state["order_data"].get('data', [])
            order_info = f"\nOrder History ({len(orders)} orders):\n"
            for order in orders:
                order_info += f"""
- Order {order.get('orderNumber')}: ${order.get('totalAmount'):.2f} - {order.get('status')} (Date: {order.get('orderDate')})
"""

        # Create prompt for LLM
        prompt = f"""Based on the following data, provide a comprehensive summary about Thomas Hardy:

{customer_info}
{order_info}

Please provide a friendly, informative summary that includes the customer's role, company, and order history."""

        messages = [
            SystemMessage(content="You are a helpful assistant that provides clear summaries of customer and order information."),
            HumanMessage(content=prompt)
        ]

        response = await llm.ainvoke(messages)

        return {
            **state,
            "messages": state.get("messages", []) + [response]
        }

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("search_customer", search_customer)
    workflow.add_node("fetch_orders", fetch_orders)
    workflow.add_node("generate_response", generate_response)

    workflow.set_entry_point("search_customer")
    workflow.add_edge("search_customer", "fetch_orders")
    workflow.add_edge("fetch_orders", "generate_response")
    workflow.add_edge("generate_response", END)

    graph = workflow.compile()

    # Run the workflow
    print("="*70)
    print("Starting workflow: Find Thomas Hardy and his orders")
    print("="*70)

    result = await graph.ainvoke({
        "messages": [HumanMessage(content="Tell me about Thomas Hardy and his orders")],
        "customer_data": {},
        "order_data": {},
        "customer_id": ""
    })

    # Display final LLM response
    print("\n" + "="*70)
    print("LLM SUMMARY:")
    print("="*70)
    if result.get("messages"):
        final_message = result["messages"][-1]
        print(final_message.content)
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
