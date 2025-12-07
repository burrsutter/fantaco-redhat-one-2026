"""
Customer Search using Llama Stack Client

This script searches for customers using the Llama Stack Client and MCP tools.

CURRENT STATUS:
- Successfully invokes the search_customers MCP tool
- Correct tool_name format: use just "search_customers" (not "customer_mcp::search_customers")
- Returns customer data successfully from the customer MCP server
"""

from llama_stack_client import Client
from llama_stack_client.types import AgentConfig
from dotenv import load_dotenv
import os
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


def search_customer_by_email(email="thomashardy@example.com"):
    """Search for customer using Llama Stack tool_runtime to invoke customer MCP tool directly"""

    try:        
        # Execute tool invocation
        logger.info("=" * 50)
        logger.info("Searching for customer with email: %s", email)
        logger.info("=" * 50)

        # Invoke the search_customers tool directly
        result = client.tool_runtime.invoke_tool(
            tool_name="search_customers",
            kwargs={"contact_email": email}
        )

        logger.info("Tool invocation result:")
        logger.info("%s", result)

        logger.info("=" * 50)
        logger.info("Customer search completed")
        logger.info("=" * 50)

        return result

    except Exception as e:
        logger.error("Error during customer search: %s", str(e))
        logger.exception("Stack trace:")
        return False


if __name__ == "__main__":
    search_customer_by_email()
