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
QUESTION = os.getenv("QUESTION", "Who is the current F1 World Champion?")

print(f"Base URL:   {LLAMA_STACK_BASE_URL}")
print(f"Model:      {INFERENCE_MODEL}")
print(f"Tavily Key: {'Set' if TAVILY_SEARCH_API_KEY else 'NOT SET'}")
print(f"Question:   {QUESTION}")

# Initialize client with Tavily API key
client = LlamaStackClient(
    base_url=LLAMA_STACK_BASE_URL,
    provider_data={"tavily_search_api_key": TAVILY_SEARCH_API_KEY} if TAVILY_SEARCH_API_KEY else None,
)

# Create response with web search (non-streaming)
response = client.responses.create(
    model=INFERENCE_MODEL,
    input=QUESTION,
    tools=[{"type": "web_search"}],
    stream=False,
)

# Process non-streaming response
for item in response.output:
    if item.type == "message":
        for content in item.content:
            if hasattr(content, 'text'):
                print(content.text)
