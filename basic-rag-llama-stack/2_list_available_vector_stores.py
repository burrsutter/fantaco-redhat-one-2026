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

# Initialize client
client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

# List all vector stores
vector_stores = client.vector_stores.list()

print("Available Vector Stores:")
print("-" * 80)

for vs in vector_stores:
    print(f"ID: {vs.id}")
    print(f"Name: {vs.name}")
    print(f"Created: {vs.created_at}")

    # List files in this vector store
    files = client.vector_stores.files.list(vector_store_id=vs.id)
    file_count = len(list(files))
    print(f"Files: {file_count}")
    print("-" * 80)

if not list(vector_stores):
    print("No vector stores found.")
