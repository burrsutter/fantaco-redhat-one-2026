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

print(f"Base URL:     {LLAMA_STACK_BASE_URL}")
print(f"Model:        {INFERENCE_MODEL}")
print(f"Customer MCP: {CUSTOMER_MCP_SERVER_URL}")

# Initialize client
client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

# Configure MCP tools
mcp_tools = [
    {
        "type": "mcp",
        "server_url": CUSTOMER_MCP_SERVER_URL,
        "server_label": "customer",
    }
]

# Create an agent with MCP tools
agent = Agent(
    client,
    model=INFERENCE_MODEL,
    instructions="You are a helpful assistant that can search for customer information using the available tools.",
    tools=mcp_tools,
)

# Create a session
session_id = agent.create_session(session_name="customer_search_session")

# Create a turn to search for a customer by email
response = agent.create_turn(
    session_id=session_id,
    messages=[{"role": "user", "content": "tell me about the customer with the email address thomashardy@example.com"}],
    stream=False,
)

# Print the response - extract text from the final message
for output in response.output:
    if hasattr(output, 'content'):
        for content in output.content:
            if hasattr(content, 'text'):
                print(content.text)
