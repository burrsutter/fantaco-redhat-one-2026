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

# Get the vector store (use the most recent one with matching name)
vector_stores = list(client.vector_stores.list())
matching_stores = [vs for vs in vector_stores if vs.name == "hr-benefits-hybrid"]
if matching_stores:
    # Sort by created_at descending to get the most recent
    vector_store = max(matching_stores, key=lambda vs: vs.created_at)
else:
    vector_store = None

if not vector_store:
    print("Error: Vector store 'hr-benefits-hybrid' not found. Please run 1d_create_vector_store_clean_html.py first.")
    exit(1)

print(f"Using vector store: {vector_store.id}")
print(f"Using model: {INFERENCE_MODEL}")
print("-" * 80)

# Define the query
query = "What do I receive when I retire?"

print(f"Query: {query}\n")
print("Agent Response:")
print("-" * 80)

# Create agent with file_search tool for RAG
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

# Create a session and ask the question
session_id = agent.create_session("retirement-benefits-query")
response = agent.create_turn(
    messages=[{"role": "user", "content": query}],
    session_id=session_id,
    stream=True,
)

# Stream the response
for log in AgentEventLogger().log(response):
    print(log, end="")
