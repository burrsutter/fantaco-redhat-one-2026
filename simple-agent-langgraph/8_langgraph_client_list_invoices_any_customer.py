from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

import os
import sys
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

# Parse command line argument for customer email
if len(sys.argv) < 2:
    print("Usage: python 8_langgraph_client_list_invoices_any_customer.py <customer_email>")
    print("Example: python 8_langgraph_client_list_invoices_any_customer.py thomashardy@example.com")
    sys.exit(1)

customer_email = sys.argv[1]

print("\n" + "=" * 50)
print(f"Finding invoices for: {customer_email}")
print("=" * 50)

response = graph.invoke(
    {"messages": [{"role": "user", "content": f"Find all invoices for {customer_email}"}]})

# Extract and display customer and invoice information
customer_info = None

for m in response['messages']:
    if hasattr(m, 'content') and isinstance(m.content, list):
        for item in m.content:
            if isinstance(item, dict) and item.get('type') == 'mcp_call' and item.get('output'):
                try:
                    output_data = json.loads(item['output'])

                    # Customer search results
                    if 'results' in output_data and output_data.get('results'):
                        customer_info = output_data['results'][0]
                        print("\n" + "=" * 50)
                        print("CUSTOMER INFORMATION")
                        print("=" * 50)
                        print(f"\nCustomer ID:   {customer_info.get('customerId', 'N/A')}")
                        print(f"Company Name:  {customer_info.get('companyName', 'N/A')}")
                        print(f"Contact Name:  {customer_info.get('contactName', 'N/A')}")
                        print(f"Contact Email: {customer_info.get('contactEmail', 'N/A')}")
                        print("=" * 50)

                    # Invoice data
                    if 'data' in output_data and output_data.get('data'):
                        invoices = output_data['data']
                    elif 'invoices' in output_data and output_data.get('invoices'):
                        invoices = output_data['invoices']
                    else:
                        invoices = None

                    if invoices:
                        print("\n" + "=" * 50)
                        print("INVOICE HISTORY")
                        print("=" * 50)

                        for idx, invoice in enumerate(invoices, 1):
                            print(f"\nInvoice #{idx}:")
                            print(f"  Invoice ID:     {invoice.get('id', invoice.get('invoiceId', 'N/A'))}")
                            print(f"  Invoice Number: {invoice.get('invoiceNumber', 'N/A')}")
                            print(f"  Invoice Date:   {invoice.get('invoiceDate', 'N/A')}")
                            print(f"  Status:         {invoice.get('status', 'N/A')}")
                            print(f"  Total Amount:   ${invoice.get('totalAmount', invoice.get('amount', 'N/A'))}")

                        print("\n" + "=" * 50)
                        print(f"Total Invoices: {len(invoices)}")
                        print("=" * 50 + "\n")
                except json.JSONDecodeError:
                    print("Could not parse tool output")

            elif isinstance(item, dict) and item.get('type') == 'text':
                print(f"\nAssistant: {item.get('text', '')}\n")
