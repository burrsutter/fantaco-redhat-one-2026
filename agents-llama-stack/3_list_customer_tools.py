from llama_stack_client import Client
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Suppress noisy httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)

BASE_URL = os.getenv("LLAMA_STACK_BASE_URL")
API_KEY = os.getenv("LLAMA_STACK_API_KEY")
CUSTOMER_MCP_SERVER_URL = os.getenv("CUSTOMER_MCP_SERVER_URL")

client = Client(
    base_url=BASE_URL,
    api_key=API_KEY
)


def list_customer_tools():
    """List all tools available in the customer MCP server"""

    print("=" * 50)
    print("Customer MCP Server Tools")
    print("=" * 50)
    print(f"MCP Server URL: {CUSTOMER_MCP_SERVER_URL}\n")

    try:
        all_tools = client.tools.list()
        customer_tools = [tool for tool in all_tools if hasattr(tool, 'toolgroup_id') and tool.toolgroup_id == 'customer_mcp']

        if customer_tools:
            for tool in customer_tools:
                tool_dict = tool.model_dump() if hasattr(tool, 'model_dump') else vars(tool)
                tool_name = tool_dict.get('tool_name') or tool_dict.get('name') or tool_dict.get('identifier') or 'N/A'

                print(f"Tool Name:    {tool_name}")
                print(f"Description:  {tool.description if hasattr(tool, 'description') else 'N/A'}")

                params = getattr(tool, 'parameters', None) or getattr(tool, 'input_schema', None)
                if params and hasattr(params, 'properties'):
                    print("Parameters:")
                    for param_name, param_info in params.properties.items():
                        param_desc = param_info.get('description', '') if isinstance(param_info, dict) else getattr(param_info, 'description', '')
                        param_type = param_info.get('type', 'any') if isinstance(param_info, dict) else getattr(param_info, 'type', 'any')
                        param_required = param_name in getattr(params, 'required', [])
                        req_marker = ' [required]' if param_required else ''
                        print(f"  - {param_name} ({param_type}){req_marker}: {param_desc}")

                print("-" * 50)

            print(f"\nTotal tools: {len(customer_tools)}")
            print("=" * 50)
            return customer_tools
        else:
            print("No tools found for customer_mcp toolgroup")
            print("\nAll available tools:")
            for tool in all_tools:
                name = tool.tool_name if hasattr(tool, 'tool_name') else 'N/A'
                group = tool.toolgroup_id if hasattr(tool, 'toolgroup_id') else 'N/A'
                print(f"  - {name} (toolgroup: {group})")
            return []

    except Exception as e:
        print(f"\nError: {str(e)}")
        return []


if __name__ == "__main__":
    list_customer_tools()
