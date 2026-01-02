from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# Suppress noisy httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)

BASE_URL = os.getenv("LLAMA_STACK_BASE_URL")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL")
API_KEY = os.getenv("API_KEY")

print(f"Base URL: {BASE_URL}")
print(f"Model:    {INFERENCE_MODEL}")


llm = ChatOpenAI(
    model=INFERENCE_MODEL,
    openai_api_key=API_KEY,
    base_url=f"{BASE_URL}/v1",
    use_responses_api=True
)

print("Testing LLM connectivity...")
connectivity_response = llm.invoke("Hello")
print("LLM connectivity OK")

# MCP tool binding - both customer and finance MCP servers
llm_with_tools = llm.bind(
    tools=[
        {
            "type": "mcp",
            "server_label": "customer_mcp",
            "server_url": os.getenv("CUSTOMER_MCP_SERVER_URL"),
            "require_approval": "never",
        },
        {
            "type": "mcp",
            "server_label": "finance_mcp",
            "server_url": os.getenv("FINANCE_MCP_SERVER_URL"),
            "require_approval": "never",
        },
    ])


class State(TypedDict):
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    return {"messages": [message]}

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

print("\n" + "=" * 50)
print("Finding orders for: thomashardy@example.com")
print("=" * 50)

response = graph.invoke(
    {"messages": [{"role": "user", "content": "Find all orders for thomashardy@example.com"}]})

# Extract and display customer and order information
for m in response['messages']:
    if hasattr(m, 'content') and isinstance(m.content, list):
        for item in m.content:
            if isinstance(item, dict) and item.get('type') == 'mcp_call' and item.get('output'):
                try:
                    output_data = json.loads(item['output'])

                    # Customer search results
                    if 'results' in output_data and output_data.get('results'):
                        customer = output_data['results'][0]
                        print("\n" + "=" * 50)
                        print("CUSTOMER INFORMATION")
                        print("=" * 50)
                        print(f"\nCustomer ID:   {customer.get('customerId', 'N/A')}")
                        print(f"Company Name:  {customer.get('companyName', 'N/A')}")
                        print(f"Contact Name:  {customer.get('contactName', 'N/A')}")
                        print(f"Contact Email: {customer.get('contactEmail', 'N/A')}")
                        print("=" * 50)

                    # Order history data
                    if 'data' in output_data and output_data.get('data'):
                        orders = output_data['data']
                    elif 'orders' in output_data and output_data.get('orders'):
                        orders = output_data['orders']
                    else:
                        orders = None

                    if orders:
                        print("\n" + "=" * 50)
                        print("ORDER HISTORY")
                        print("=" * 50)

                        for idx, order in enumerate(orders, 1):
                            print(f"\nOrder #{idx}:")
                            print(f"  Order ID:     {order.get('id', order.get('orderId', 'N/A'))}")
                            print(f"  Order Number: {order.get('orderNumber', 'N/A')}")
                            print(f"  Order Date:   {order.get('orderDate', 'N/A')}")
                            print(f"  Status:       {order.get('status', 'N/A')}")
                            print(f"  Total Amount: ${order.get('totalAmount', order.get('freight', 'N/A'))}")

                        print("\n" + "=" * 50)
                        print(f"Total Orders: {len(orders)}")
                        print("=" * 50 + "\n")
                except json.JSONDecodeError:
                    print("Could not parse tool output")

            elif isinstance(item, dict) and item.get('type') == 'text':
                print(f"\nAssistant: {item.get('text', '')}\n")
