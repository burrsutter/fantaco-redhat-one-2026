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

print(f"Base URL: {LLAMA_STACK_BASE_URL}")
print(f"Model:    {INFERENCE_MODEL}")

# Initialize client
client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

# Create response without web search (streaming)
response = client.responses.create(
    model=INFERENCE_MODEL,
    input="Who is the current US President?",
    stream=True,
)

# Process streaming response
for chunk in response:
    if hasattr(chunk, 'output_text') and chunk.output_text:
        print(chunk.output_text, end="", flush=True)
    elif hasattr(chunk, 'delta') and chunk.delta:
        print(chunk.delta, end="", flush=True)

print()  # Final newline
