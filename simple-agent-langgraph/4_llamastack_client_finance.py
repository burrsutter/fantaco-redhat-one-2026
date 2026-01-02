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

# Suppress noisy httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)

BASE_URL = os.getenv("LLAMA_STACK_BASE_URL")
API_KEY = os.getenv("LLAMA_STACK_API_KEY")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL")

print(f"Base URL: {BASE_URL}")
print(f"Model:    {INFERENCE_MODEL}")

client = Client(
    base_url=BASE_URL,
    api_key=API_KEY
)


def fetch_order_history_by_customer(customer_id="AROUT"):
    """Fetch order history using Llama Stack tool_runtime to invoke finance MCP tool directly"""

    try:
        print("\n" + "=" * 50)
        print(f"Fetching order history for customer: {customer_id}")
        print("=" * 50)

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
                            print("\n" + "=" * 50)
                            print(f"ORDER HISTORY FOR CUSTOMER: {customer_id}")
                            print("=" * 50)

                            for idx, order in enumerate(orders, 1):
                                print(f"\nOrder #{idx}:")
                                print(f"  Order ID:     {order.get('id', order.get('orderId', 'N/A'))}")
                                print(f"  Order Number: {order.get('orderNumber', 'N/A')}")
                                print(f"  Order Date:   {order.get('orderDate', 'N/A')}")
                                print(f"  Status:       {order.get('status', 'N/A')}")
                                print(f"  Total Amount: ${order.get('totalAmount', order.get('freight', 'N/A'))}")

                            print("\n" + "=" * 50)
                            print(f"Total Orders Found: {len(orders)}")
                            print("=" * 50 + "\n")
                        else:
                            print(f"No orders found for customer: {customer_id}")

                    except json.JSONDecodeError:
                        print("Could not parse response as JSON")
                        print(f"Raw response: {content_item.text}")
        else:
            print("No content in result")

        return result

    except Exception as e:
        print(f"\nError: {str(e)}")
        return False


if __name__ == "__main__":
    fetch_order_history_by_customer()
