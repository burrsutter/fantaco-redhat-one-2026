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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = os.getenv("LLAMA_STACK_BASE_URL")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL")
API_KEY = os.getenv("API_KEY")

logger.info("Configuration loaded:")
logger.info("  Base URL: %s", BASE_URL)
logger.info("  Model: %s", INFERENCE_MODEL)
logger.info("  API Key: %s", "***" if API_KEY else "None")


llm = ChatOpenAI(
    model=INFERENCE_MODEL,
    openai_api_key=API_KEY,
    base_url=f"{BASE_URL}/v1",
    use_responses_api=True
)

logger.info("Testing LLM connectivity...")
connectivity_response = llm.invoke("Hello")
logger.info("LLM connectivity test successful")

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
    logger.error("Usage: python 7_langgraph_client_list_orders_any_customer.py <customer_email>")
    logger.error("Example: python 7_langgraph_client_list_orders_any_customer.py thomashardy@example.com")
    sys.exit(1)

customer_email = sys.argv[1]

logger.info("=" * 80)
logger.info("Starting customer order lookup for: %s", customer_email)
logger.info("=" * 80)

response = graph.invoke(
    {"messages": [{"role": "user", "content": f"Find all orders for {customer_email}"}]})

# Extract and display customer and order information
customer_info = None
order_info = None

for m in response['messages']:
    if hasattr(m, 'content') and isinstance(m.content, list):
        for item in m.content:
            # Look for MCP tool call results
            if isinstance(item, dict) and item.get('type') == 'mcp_call' and item.get('output'):
                try:
                    output_data = json.loads(item['output'])

                    # Check if this is customer search results
                    if 'results' in output_data and output_data.get('results'):
                        customer_info = output_data['results'][0] if output_data['results'] else None
                        if customer_info:
                            logger.info("")
                            logger.info("=" * 80)
                            logger.info("CUSTOMER INFORMATION")
                            logger.info("=" * 80)
                            logger.info("")
                            logger.info("┌─ Customer ID: %s", customer_info.get('customerId', 'N/A'))
                            logger.info("├─ Company Name: %s", customer_info.get('companyName', 'N/A'))
                            logger.info("├─ Contact Name: %s", customer_info.get('contactName', 'N/A'))
                            logger.info("└─ Contact Email: %s", customer_info.get('contactEmail', 'N/A'))
                            logger.info("")
                            logger.info("=" * 80)

                    # Check if this is order history data
                    if 'data' in output_data and output_data.get('data'):
                        orders = output_data['data']
                    elif 'orders' in output_data and output_data.get('orders'):
                        orders = output_data['orders']
                    else:
                        orders = None

                    if orders:
                        logger.info("")
                        logger.info("=" * 80)
                        logger.info("ORDER HISTORY")
                        logger.info("=" * 80)

                        for idx, order in enumerate(orders, 1):
                            logger.info("")
                            logger.info("Order #%d:", idx)
                            logger.info("  ┌─ Order ID: %s", order.get('id', order.get('orderId', 'N/A')))
                            logger.info("  ├─ Order Number: %s", order.get('orderNumber', 'N/A'))
                            logger.info("  ├─ Order Date: %s", order.get('orderDate', 'N/A'))
                            logger.info("  ├─ Status: %s", order.get('status', 'N/A'))
                            logger.info("  └─ Total Amount: $%s", order.get('totalAmount', order.get('freight', 'N/A')))
                            logger.info("")

                        logger.info("=" * 80)
                        logger.info("Total Orders: %d", len(orders))
                        logger.info("=" * 80)
                except json.JSONDecodeError:
                    logger.warning("Could not parse tool output")

            # Display final text response
            elif isinstance(item, dict) and item.get('type') == 'text':
                logger.info("")
                logger.info("Assistant Response:")
                logger.info("  %s", item.get('text', ''))
                logger.info("")

logger.info("=" * 80)
logger.info("Customer order lookup completed")
logger.info("=" * 80)
