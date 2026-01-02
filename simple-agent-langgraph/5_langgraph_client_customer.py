from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# Suppress noisy httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)

BASE_URL = os.getenv("LLAMA_STACK_BASE_URL")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL")
API_KEY = os.getenv("API_KEY")

print(f"Base URL: {BASE_URL}")
print(f"Model:    {INFERENCE_MODEL}")


llm = ChatOpenAI(
    model=INFERENCE_MODEL,
    openai_api_key=API_KEY,
    base_url=f"{BASE_URL}/v1",
    use_responses_api=True
)

print("Testing LLM connectivity...")
connectivity_response = llm.invoke("Hello")
print("LLM connectivity OK")

# MCP tool binding using OpenAI Responses API format
llm_with_tools = llm.bind(
    tools=[
        {
            "type": "mcp",
            "server_label": "customer_mcp",
            "server_url": os.getenv("CUSTOMER_MCP_SERVER_URL"),
            "require_approval": "never",
        },
    ])



class State(TypedDict):
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    #print(message)
    return {"messages": [message]}

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

print("\n" + "=" * 50)
print("Searching for customer: thomashardy@example.com")
print("=" * 50)

response = graph.invoke(
    {"messages": [{"role": "user", "content": "Search for customer with email thomashardy@example.com"}]})

# Extract and display customer information
for m in response['messages']:
    if hasattr(m, 'content') and isinstance(m.content, list):
        for item in m.content:
            if isinstance(item, dict) and item.get('type') == 'mcp_call' and item.get('output'):
                try:
                    output_data = json.loads(item['output'])
                    if 'results' in output_data and output_data['results']:
                        print("\n" + "=" * 50)
                        print("CUSTOMER SEARCH RESULTS")
                        print("=" * 50)

                        for customer in output_data['results']:
                            print(f"\nCustomer ID:   {customer.get('customerId', 'N/A')}")
                            print(f"Company Name:  {customer.get('companyName', 'N/A')}")
                            print(f"Contact Name:  {customer.get('contactName', 'N/A')}")
                            print(f"Contact Email: {customer.get('contactEmail', 'N/A')}")

                        print("=" * 50 + "\n")
                except json.JSONDecodeError:
                    print("Could not parse tool output")

            elif isinstance(item, dict) and item.get('type') == 'text':
                print(f"\nAssistant: {item.get('text', '')}\n") 





