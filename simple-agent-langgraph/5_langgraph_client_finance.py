from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

import os
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

# MCP tool binding using OpenAI Responses API format
llm_with_tools = llm.bind(
    tools=[
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

logger.info("=" * 80)
logger.info("Starting order history fetch...")
logger.info("=" * 80)

response = graph.invoke(
    {"messages": [{"role": "user", "content": "Use the fetch_order_history tool to get orders for customer_id AROUT"}]})

# Extract and display order information
for m in response['messages']:
    if hasattr(m, 'content') and isinstance(m.content, list):
        for item in m.content:
            # Look for MCP tool call results
            if isinstance(item, dict) and item.get('type') == 'mcp_call' and item.get('output'):
                try:
                    output_data = json.loads(item['output'])

                    # Check for different response formats
                    if 'data' in output_data and output_data.get('data'):
                        orders = output_data['data']
                    elif 'orders' in output_data and output_data.get('orders'):
                        orders = output_data['orders']
                    else:
                        orders = None

                    if orders:
                        logger.info("")
                        logger.info("=" * 80)
                        logger.info("ORDER HISTORY RESULTS")
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
logger.info("Order history fetch completed")
logger.info("=" * 80)
