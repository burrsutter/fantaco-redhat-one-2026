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

print(f"Base URL: {LLAMA_STACK_BASE_URL}")
print(f"Model:    {INFERENCE_MODEL}")

# Initialize client
client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

# Create an agent
agent = Agent(
    client,
    model=INFERENCE_MODEL,
    instructions="You are a helpful assistant that can answer questions and help with tasks.",
)

# Create a session
session_id = agent.create_session(session_name="hello_world_session_no_stream")

# Create a turn without streaming
response = agent.create_turn(
    session_id=session_id,
    messages=[{"role": "user", "content": "Explain what an AI agent is in one sentence."}],
    stream=False,
)

# Print the response
print(response.output[0].content[0].text)
