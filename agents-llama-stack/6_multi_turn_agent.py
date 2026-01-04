import os
import logging
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient, Agent

# Suppress httpx and llama_stack_client INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("llama_stack_client").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Get configuration from environment
LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "vllm/qwen3-14b-gaudi")
CUSTOMER_MCP_SERVER_URL = os.getenv("CUSTOMER_MCP_SERVER_URL")
FINANCE_MCP_SERVER_URL = os.getenv("FINANCE_MCP_SERVER_URL")

print(f"Base URL:     {LLAMA_STACK_BASE_URL}")
print(f"Model:        {INFERENCE_MODEL}")
print(f"Customer MCP: {CUSTOMER_MCP_SERVER_URL}")
print(f"Finance MCP:  {FINANCE_MCP_SERVER_URL}")
print()

# Initialize client
client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

# Configure MCP tools - both customer and finance servers
mcp_tools = [
    {
        "type": "mcp",
        "server_url": CUSTOMER_MCP_SERVER_URL,
        "server_label": "customer",
    },
    {
        "type": "mcp",
        "server_url": FINANCE_MCP_SERVER_URL,
        "server_label": "finance",
    }
]

# Create an agent with both MCP tools
agent = Agent(
    client,
    model=INFERENCE_MODEL,
    instructions="You are a helpful assistant that can search for customer information and retrieve order/financial data using the available tools.",
    tools=mcp_tools,
)

# Create a session
session_id = agent.create_session(session_name="multi_turn_session")


def print_response(response):
    """Extract and print text from the response"""
    for output in response.output:
        if hasattr(output, 'content'):
            for content in output.content:
                if hasattr(content, 'text'):
                    print(content.text)


# Turn 1: Ask who Thomas Hardy works for
print("=" * 60)
print("Turn 1: who does Thomas Hardy work for?")
print("=" * 60)

response1 = agent.create_turn(
    session_id=session_id,
    messages=[{"role": "user", "content": "who does Thomas Hardy work for?"}],
    stream=False,
)
print_response(response1)

# Turn 2: Ask about their orders (referring to context from Turn 1)
print()
print("=" * 60)
print("Turn 2: what are their orders?")
print("=" * 60)

response2 = agent.create_turn(
    session_id=session_id,
    messages=[{"role": "user", "content": "what are their orders?"}],
    stream=False,
)
print_response(response2)
