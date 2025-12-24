import os
import logging
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient, Agent, AgentEventLogger

# Suppress httpx and llama_stack_client INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("llama_stack_client").setLevel(logging.WARNING)

load_dotenv()

LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "ollama/qwen3:14b-q8_0")

client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

vector_stores = list(client.vector_stores.list())
matching_stores = [vs for vs in vector_stores if vs.name == "hr-benefits-hybrid"]
vector_store = max(matching_stores, key=lambda vs: vs.created_at) if matching_stores else None

if not vector_store:
    print("Error: Vector store not found.")
    exit(1)

print(f"Using vector store: {vector_store.id}\n")

# Try queries with unique terms from the retirement section
queries = [
    "Tell me about the chocolate statue and personal bard",
    "Tell me about the 401k and astrological alignment",
    "where might I try a marathon?",
    "What does the office griffin eat?",
    "What languages must employees learn?",
]

for query in queries:
    print(f"Query: {query}")
    print("-" * 80)

    agent = Agent(
        client,
        model=INFERENCE_MODEL,
        instructions="You MUST use the file_search tool. Provide ALL details found in the documents.",
        tools=[{"type": "file_search", "vector_store_ids": [vector_store.id]}],
    )

    response = agent.create_turn(
        messages=[{"role": "user", "content": query}],
        session_id=agent.create_session(f"query-{queries.index(query)}"),
        stream=True,
    )

    for log in AgentEventLogger().log(response):
        print(log, end="")
    print("\n")
