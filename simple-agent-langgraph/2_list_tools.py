from llama_stack_client import Client
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

client = Client(
    base_url=BASE_URL,
    api_key=API_KEY
)


def list_mcp_servers():
    """List all registered MCP servers"""
    logger.info("Fetching list of registered toolgroups")
    toolgroups = client.toolgroups.list()
    logger.info("Registered Toolgroups:")
    logger.info("-" * 50)
    for tg in toolgroups:
        logger.info("Toolgroup ID: %s", tg.identifier)
        logger.info("Provider ID: %s", tg.provider_id)
        if hasattr(tg, 'mcp_endpoint') and tg.mcp_endpoint:
            logger.info("MCP Endpoint URI: %s", tg.mcp_endpoint.get('uri') if isinstance(tg.mcp_endpoint, dict) else getattr(tg.mcp_endpoint, 'uri', None))
        logger.info("-" * 50)
    return toolgroups


if __name__ == "__main__":
    list_mcp_servers()
