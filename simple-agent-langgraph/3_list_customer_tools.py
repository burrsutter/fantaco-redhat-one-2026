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
CUSTOMER_MCP_SERVER_URL = os.getenv("CUSTOMER_MCP_SERVER_URL")

client = Client(
    base_url=BASE_URL,
    api_key=API_KEY
)


def list_customer_tools():
    """List all tools available in the customer MCP server"""

    logger.info("=" * 50)
    logger.info("Customer MCP Server Tools")
    logger.info("=" * 50)
    logger.info("MCP Server URL: %s", CUSTOMER_MCP_SERVER_URL)
    logger.info("")

    try:
        # List all tools and filter for customer_mcp toolgroup
        all_tools = client.tools.list()

        # Filter tools that belong to customer_mcp toolgroup
        customer_tools = [tool for tool in all_tools if hasattr(tool, 'toolgroup_id') and tool.toolgroup_id == 'customer_mcp']

        if customer_tools:
            for tool in customer_tools:
                # Get the full tool object to inspect
                tool_dict = tool.model_dump() if hasattr(tool, 'model_dump') else vars(tool)

                tool_name = tool_dict.get('tool_name') or tool_dict.get('name') or tool_dict.get('identifier') or 'N/A'

                logger.info("Tool Name: %s", tool_name)
                logger.info("Description: %s", tool.description if hasattr(tool, 'description') else 'N/A')
                logger.info("Toolgroup ID: %s", tool.toolgroup_id if hasattr(tool, 'toolgroup_id') else 'N/A')

                if hasattr(tool, 'parameters'):
                    logger.info("Parameters:")
                    params = tool.parameters
                    if hasattr(params, 'properties'):
                        for param_name, param_info in params.properties.items():
                            param_desc = param_info.get('description', 'No description') if isinstance(param_info, dict) else getattr(param_info, 'description', 'No description')
                            param_type = param_info.get('type', 'any') if isinstance(param_info, dict) else getattr(param_info, 'type', 'any')
                            param_required = param_name in getattr(params, 'required', [])
                            logger.info("  - %s (%s)%s: %s", param_name, param_type, ' [required]' if param_required else '', param_desc)
                elif hasattr(tool, 'input_schema'):
                    logger.info("Parameters:")
                    schema = tool.input_schema
                    if hasattr(schema, 'properties'):
                        for param_name, param_info in schema.properties.items():
                            param_desc = param_info.get('description', 'No description') if isinstance(param_info, dict) else getattr(param_info, 'description', 'No description')
                            param_type = param_info.get('type', 'any') if isinstance(param_info, dict) else getattr(param_info, 'type', 'any')
                            param_required = param_name in getattr(schema, 'required', [])
                            logger.info("  - %s (%s)%s: %s", param_name, param_type, ' [required]' if param_required else '', param_desc)

                logger.info("-" * 50)

            logger.info("=" * 50)
            logger.info("Total tools: %d", len(customer_tools))
            logger.info("=" * 50)

            return customer_tools
        else:
            logger.warning("No tools found for customer_mcp toolgroup")

            # Show all available tools for debugging
            logger.info("All available tools:")
            for tool in all_tools:
                logger.info("  - %s (toolgroup: %s)",
                           tool.tool_name if hasattr(tool, 'tool_name') else 'N/A',
                           tool.toolgroup_id if hasattr(tool, 'toolgroup_id') else 'N/A')

            return []

    except Exception as e:
        logger.error("Error fetching customer tools: %s", str(e))
        logger.exception("Stack trace:")
        return []


if __name__ == "__main__":
    list_customer_tools()
