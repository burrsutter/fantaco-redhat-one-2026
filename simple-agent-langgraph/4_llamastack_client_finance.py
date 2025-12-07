"""
Finance Order History using Llama Stack Client

This script fetches order history using the Llama Stack Client and MCP tools.

CURRENT STATUS:
- Successfully invokes the fetch_order_history MCP tool
- Correct tool_name format: use just "fetch_order_history" (not "finance_mcp::fetch_order_history")
- Returns order history data successfully from the finance MCP server
"""

from llama_stack_client import Client
from dotenv import load_dotenv
import os
import json
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = os.getenv("LLAMA_STACK_BASE_URL")
API_KEY = os.getenv("LLAMA_STACK_API_KEY")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL")

logger.info("Configuration loaded:")
logger.info("  Base URL: %s", BASE_URL)
logger.info("  Model: %s", INFERENCE_MODEL)
logger.info("  API Key: %s", "***" if API_KEY else "None")

client = Client(
    base_url=BASE_URL,
    api_key=API_KEY
)


def fetch_order_history_by_customer(customer_id="AROUT"):
    """Fetch order history using Llama Stack tool_runtime to invoke finance MCP tool directly"""

    try:
        # Execute tool invocation
        logger.info("=" * 80)
        logger.info("Fetching order history for customer: %s", customer_id)
        logger.info("=" * 80)

        # Invoke the fetch_order_history tool directly
        result = client.tool_runtime.invoke_tool(
            tool_name="fetch_order_history",
            kwargs={"customer_id": customer_id}
        )

        # Parse and display order history in a readable format
        if result and hasattr(result, 'content') and result.content:
            for content_item in result.content:
                if hasattr(content_item, 'text'):
                    try:
                        order_data = json.loads(content_item.text)

                        # Check for different response formats
                        if 'data' in order_data and order_data.get('data'):
                            orders = order_data['data']
                        elif 'orders' in order_data and order_data.get('orders'):
                            orders = order_data['orders']
                        else:
                            orders = None

                        if orders:
                            logger.info("")
                            logger.info("=" * 80)
                            logger.info("ORDER HISTORY FOR CUSTOMER: %s", customer_id)
                            logger.info("=" * 80)
                            logger.info("")

                            for idx, order in enumerate(orders, 1):
                                logger.info("Order #%d:", idx)
                                logger.info("  ┌─ Order ID: %s", order.get('id', order.get('orderId', 'N/A')))
                                logger.info("  ├─ Order Number: %s", order.get('orderNumber', 'N/A'))
                                logger.info("  ├─ Order Date: %s", order.get('orderDate', 'N/A'))
                                logger.info("  ├─ Status: %s", order.get('status', 'N/A'))
                                logger.info("  ├─ Total Amount: $%s", order.get('totalAmount', order.get('freight', 'N/A')))
                                logger.info("  ├─ Required Date: %s", order.get('requiredDate', 'N/A'))
                                logger.info("  ├─ Shipped Date: %s", order.get('shippedDate', 'N/A'))
                                logger.info("  ├─ Ship Via: %s", order.get('shipVia', 'N/A'))
                                logger.info("  ├─ Ship Name: %s", order.get('shipName', 'N/A'))
                                logger.info("  ├─ Ship Address: %s", order.get('shipAddress', 'N/A'))
                                logger.info("  ├─ Ship City: %s", order.get('shipCity', 'N/A'))
                                logger.info("  ├─ Ship Postal Code: %s", order.get('shipPostalCode', 'N/A'))
                                logger.info("  └─ Ship Country: %s", order.get('shipCountry', 'N/A'))
                                logger.info("")

                            logger.info("=" * 80)
                            logger.info("Total Orders Found: %d", len(orders))
                            logger.info("=" * 80)
                        else:
                            logger.info("No orders found for customer: %s", customer_id)

                    except json.JSONDecodeError:
                        logger.warning("Could not parse order history response as JSON")
                        logger.info("Raw response: %s", content_item.text)
        else:
            logger.warning("No content in tool invocation result")

        logger.info("")
        logger.info("Order history fetch completed")

        return result

    except Exception as e:
        logger.error("Error during order history fetch: %s", str(e))
        logger.exception("Stack trace:")
        return False


if __name__ == "__main__":
    fetch_order_history_by_customer()
