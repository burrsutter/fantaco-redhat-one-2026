import os
import logging
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient

# Suppress httpx and llama_stack_client INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("llama_stack_client").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Get configuration from environment
LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "vllm/qwen3-14b")
TAVILY_SEARCH_API_KEY = os.getenv("TAVILY_SEARCH_API_KEY")

print(f"Base URL:   {LLAMA_STACK_BASE_URL}")
print(f"Model:      {INFERENCE_MODEL}")
print(f"Tavily Key: {'Set' if TAVILY_SEARCH_API_KEY else 'NOT SET'}")

# Initialize client with Tavily API key
client = LlamaStackClient(
    base_url=LLAMA_STACK_BASE_URL,
    provider_data={"tavily_search_api_key": TAVILY_SEARCH_API_KEY} if TAVILY_SEARCH_API_KEY else None,
)

# Create response with web search (streaming)
response = client.responses.create(
    model=INFERENCE_MODEL,
    input="Who is the current US President?",
    tools=[{"type": "web_search"}],
    stream=True,
)

# Process streaming response
for chunk in response:
    if hasattr(chunk, 'output_text') and chunk.output_text:
        print(chunk.output_text, end="", flush=True)
    elif hasattr(chunk, 'delta') and chunk.delta:
        print(chunk.delta, end="", flush=True)

print()  # Final newline
