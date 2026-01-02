"""
Customer Search using Llama Stack Client

This script searches for customers using the Llama Stack Client and MCP tools.

CURRENT STATUS:
- Successfully invokes the search_customers MCP tool
- Correct tool_name format: use just "search_customers" (not "customer_mcp::search_customers")
- Returns customer data successfully from the customer MCP server
"""

from llama_stack_client import Client
from dotenv import load_dotenv
import os
import logging
import json

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


def search_customer_by_email(email="thomashardy@example.com"):
    """Search for customer using Llama Stack tool_runtime to invoke customer MCP tool directly"""

    try:
        print("\n" + "=" * 50)
        print(f"Searching for customer: {email}")
        print("=" * 50)

        # Invoke the search_customers tool directly
        result = client.tool_runtime.invoke_tool(
            tool_name="search_customers",
            kwargs={"contact_email": email}
        )

        # Parse and display result in readable format
        print("\n" + "=" * 50)
        print("CUSTOMER SEARCH RESULT")
        print("=" * 50)

        if hasattr(result, 'content') and result.content:
            # result.content is a list of TextContentItem objects
            for item in result.content:
                if hasattr(item, 'text'):
                    # Parse JSON from the text field
                    data = json.loads(item.text)
                    if isinstance(data, list):
                        for customer in data:
                            print(f"\nCustomer ID: {customer.get('customer_id', 'N/A')}")
                            print(f"Name:        {customer.get('customer_name', 'N/A')}")
                            print(f"Email:       {customer.get('contact_email', 'N/A')}")
                            print(f"Status:      {customer.get('status', 'N/A')}")
                            print(f"Country:     {customer.get('country', 'N/A')}")
                    else:
                        print(json.dumps(data, indent=2))
        else:
            print(result)

        print("=" * 50 + "\n")

        return result

    except Exception as e:
        print(f"\nError: {str(e)}")
        return False


if __name__ == "__main__":
    search_customer_by_email()
