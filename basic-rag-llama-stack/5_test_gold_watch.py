import os
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient, Agent, AgentEventLogger

# Load environment variables
load_dotenv()

# Get configuration from environment
LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "vllm/qwen3-14b-gaudi")

# Initialize client
client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

# Get the vector store
vector_stores = list(client.vector_stores.list())
matching_stores = [vs for vs in vector_stores if vs.name == "hr-benefits-hybrid"]
if matching_stores:
    vector_store = max(matching_stores, key=lambda vs: vs.created_at)
else:
    print("Error: Vector store 'hr-benefits-hybrid' not found.")
    exit(1)

print(f"Using vector store: {vector_store.id}")
print(f"Using model: {INFERENCE_MODEL}")
print("-" * 80)

# Try multiple queries
queries = [
    "When do I get my gold watch?",
]

for query in queries:
    print(f"\nQuery: {query}")
    print("Agent Response:")
    print("-" * 80)

    agent = Agent(
        client,
        model=INFERENCE_MODEL,
        instructions="You MUST use the file_search tool to answer ALL questions by searching the provided documents.",
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [vector_store.id],
            }
        ],
    )

    session_id = agent.create_session(f"query-{queries.index(query)}")
    response = agent.create_turn(
        messages=[{"role": "user", "content": query}],
        session_id=session_id,
        stream=True,
    )

    for log in AgentEventLogger().log(response):
        print(log, end="")
    print("\n")
