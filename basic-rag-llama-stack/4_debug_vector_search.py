import os
import logging
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient

# Suppress httpx and llama_stack_client INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("llama_stack_client").setLevel(logging.WARNING)

load_dotenv()

LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")
client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

# Get the latest hybrid vector store
vector_stores = list(client.vector_stores.list())
matching_stores = [vs for vs in vector_stores if vs.name == "hr-benefits-hybrid"]
vector_store = max(matching_stores, key=lambda vs: vs.created_at) if matching_stores else None

if not vector_store:
    print("Error: No hybrid vector store found.")
    exit(1)

print(f"Vector Store: {vector_store.id}")
print(f"Name: {vector_store.name}")
print(f"Created: {vector_store.created_at}")

# Check file status
print("\nChecking files in vector store...")
files = list(client.vector_stores.files.list(vector_store_id=vector_store.id))
print(f"Total files: {len(files)}")
for f in files:
    print(f"  File ID: {f.id}")
    print(f"  Status: {f.status}")
    if hasattr(f, 'last_error') and f.last_error:
        print(f"  Error: {f.last_error}")

print("-" * 80)

# Test different queries and see what gets retrieved
queries = [
    "gold watch retirement",
    "chocolate statue",
    "401k astrological alignment",
    "personal bard",
    "retirement benefits",
]

for query in queries:
    print(f"\nQuery: '{query}'")
    print("-" * 80)

    try:
        # Direct vector store search
        results = client.vector_stores.search(
            vector_store_id=vector_store.id,
            query=query
        )

        print(f"Search results type: {type(results)}")
        print(f"Results: {results}")

        # Try to access data if available
        if hasattr(results, 'data'):
            if results.data:
                print(f"Found {len(results.data)} results")
                for i, result in enumerate(results.data[:3], 1):  # Show top 3
                    print(f"\n  Result {i}:")
                    if hasattr(result, 'score'):
                        print(f"    Score: {result.score}")
                    if hasattr(result, 'content'):
                        content = result.content[:200] if len(result.content) > 200 else result.content
                        print(f"    Content: {content}...")
                    else:
                        print(f"    Data: {result}")
            else:
                print("  No results returned")
        else:
            print(f"  Response attributes: {dir(results)}")

    except Exception as e:
        print(f"  Error: {e}")

    print()
