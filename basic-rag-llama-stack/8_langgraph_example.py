"""
LangGraph + Llama Stack Responses API RAG Example

This demonstrates how to build a sophisticated RAG workflow using LangGraph
with Llama Stack's Responses API for automatic tool calling.
"""

import io
import os
from typing import TypedDict, List, Annotated, Literal
import operator
import requests
from openai import OpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment
LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "vllm/qwen3-14b-gaudi")
API_KEY = os.getenv("API_KEY", "none")

# ============================================================================
# State Definition
# ============================================================================

class RAGState(TypedDict):
    """State for our RAG workflow"""
    messages: Annotated[List[dict], operator.add]  # Conversation history
    question: str                                   # Current question
    vector_store_id: str                           # Vector store ID
    answer: str                                     # Generated answer
    search_results: List[dict]                     # Retrieved chunks
    metadata: dict                                  # Additional metadata


# ============================================================================
# Setup: Initialize Llama Stack Client & Vector Store
# ============================================================================

def setup_vector_store(client: OpenAI) -> str:
    """
    Create vector store and upload documents.
    Based on: docs/docs/getting_started/demo_script.py:27-44
    """
    print("Creating vector store and uploading documents...")

    # Create vector store
    vs = client.vector_stores.create()
    print(f"✓ Vector store created: {vs.id}")

    # Upload Paul Graham's essay on great work
    url = "https://www.paulgraham.com/greatwork.html"
    response = requests.get(url)
    pseudo_file = io.BytesIO(str(response.content).encode("utf-8"))

    uploaded_file = client.files.create(
        file=(url, pseudo_file, "text/html"),
        purpose="assistants"
    )

    # Add file to vector store
    client.vector_stores.files.create(
        vector_store_id=vs.id,
        file_id=uploaded_file.id
    )
    print(f"✓ File uploaded: {uploaded_file.id}\n")

    return vs.id


# ============================================================================
# LangGraph Nodes - Using Responses API
# ============================================================================

def rag_query_node(state: RAGState) -> RAGState:
    """
    Node that performs RAG using Responses API with automatic tool calling.
    Based on: docs/docs/building_applications/rag.mdx:88-112
    """
    client = OpenAI(base_url=f"{LLAMA_STACK_BASE_URL}/v1/", api_key="none")

    print(f"📝 Question: {state['question']}")
    print("🔍 Querying with Responses API (automatic tool calling)...")

    # Use Responses API with file_search tool
    # The model automatically decides when to search the vector store
    resp = client.responses.create(
        model=INFERENCE_MODEL,
        input=state["question"],
        tools=[{
            "type": "file_search",
            "vector_store_ids": [state["vector_store_id"]]
        }],
        # Include search results in the response
        include=["file_search_call.results"],
        stream=False
    )

    # Extract the final answer
    answer = resp.output[-1].content[-1].text

    # Extract search results if available
    search_results = []
    for output in resp.output:
        if output.type == "file_search_call" and hasattr(output, 'results'):
            search_results = [
                {
                    "text": result.text,
                    "score": getattr(result, 'score', None)
                }
                for result in output.results
            ]

    print(f"✓ Retrieved {len(search_results)} chunks")
    print(f"✓ Generated answer\n")

    return {
        **state,
        "answer": answer,
        "search_results": search_results,
        "messages": [
            {"role": "user", "content": state["question"]},
            {"role": "assistant", "content": answer}
        ]
    }


def rag_query_with_filters_node(state: RAGState) -> RAGState:
    """
    Advanced RAG node with filtering capabilities.
    Based on: tests/integration/responses/test_file_search.py:132-161
    """
    client = OpenAI(base_url=f"{LLAMA_STACK_BASE_URL}/v1/", api_key="none")

    print(f"📝 Question: {state['question']}")
    print("🔍 Querying with filters...")

    # Example: Filter by region and category
    tools = [{
        "type": "file_search",
        "vector_store_ids": [state["vector_store_id"]],
        "filters": {
            "type": "and",
            "filters": [
                {"type": "eq", "key": "category", "value": "technical"},
                {"type": "gte", "key": "date", "value": 1672531200}
            ]
        }
    }]

    resp = client.responses.create(
        model=INFERENCE_MODEL,
        input=state["question"],
        tools=tools,
        include=["file_search_call.results"],
        stream=False
    )

    answer = resp.output[-1].content[-1].text

    return {
        **state,
        "answer": answer,
        "messages": [
            {"role": "user", "content": state["question"]},
            {"role": "assistant", "content": answer}
        ]
    }


def rag_streaming_node(state: RAGState) -> RAGState:
    """
    RAG node with streaming support.
    Based on: tests/integration/responses/test_file_search.py:315-358
    """
    client = OpenAI(base_url=f"{LLAMA_STACK_BASE_URL}/v1/", api_key="none")

    print(f"📝 Question: {state['question']}")
    print("🔍 Streaming response...")

    # Create streaming response
    stream = client.responses.create(
        model=INFERENCE_MODEL,
        input=state["question"],
        tools=[{
            "type": "file_search",
            "vector_store_ids": [state["vector_store_id"]]
        }],
        stream=True  # Enable streaming
    )

    # Collect streaming events
    chunks = []
    answer_chunks = []

    for chunk in stream:
        chunks.append(chunk)

        # Track different event types
        if chunk.type == "response.file_search_call.in_progress":
            print("  ⏳ File search in progress...")
        elif chunk.type == "response.file_search_call.searching":
            print("  🔎 Searching vector store...")
        elif chunk.type == "response.file_search_call.completed":
            print("  ✓ File search completed")
        elif chunk.type == "response.content_block.delta":
            # Collect answer chunks as they stream
            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                answer_chunks.append(chunk.delta.text)
                print(chunk.delta.text, end="", flush=True)

    print("\n")

    # Combine answer chunks
    answer = "".join(answer_chunks)

    return {
        **state,
        "answer": answer,
        "metadata": {"streaming_chunks": len(chunks)},
        "messages": [
            {"role": "user", "content": state["question"]},
            {"role": "assistant", "content": answer}
        ]
    }


def multi_turn_conversation_node(state: RAGState) -> RAGState:
    """
    Multi-turn conversation with context from previous messages.
    """
    client = OpenAI(base_url=f"{LLAMA_STACK_BASE_URL}/v1/", api_key="none")

    print(f"📝 Follow-up question: {state['question']}")
    print(f"📚 Conversation history: {len(state['messages'])} messages")

    # Build conversation context
    conversation_context = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in state['messages'][-4:]  # Last 4 messages for context
    ])

    # Combine conversation context with new question
    enriched_input = f"""Previous conversation:
{conversation_context}

Current question: {state['question']}
"""

    resp = client.responses.create(
        model=INFERENCE_MODEL,
        input=enriched_input,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [state["vector_store_id"]]
        }],
        include=["file_search_call.results"],
        stream=False
    )

    answer = resp.output[-1].content[-1].text

    return {
        **state,
        "answer": answer,
        "messages": [
            {"role": "user", "content": state["question"]},
            {"role": "assistant", "content": answer}
        ]
    }


# ============================================================================
# Build LangGraph Workflows
# ============================================================================

def build_simple_rag_graph():
    """Simple single-turn RAG workflow"""
    workflow = StateGraph(RAGState)

    workflow.add_node("rag_query", rag_query_node)
    workflow.set_entry_point("rag_query")
    workflow.add_edge("rag_query", END)

    return workflow.compile()


def build_streaming_rag_graph():
    """RAG workflow with streaming support"""
    workflow = StateGraph(RAGState)

    workflow.add_node("rag_streaming", rag_streaming_node)
    workflow.set_entry_point("rag_streaming")
    workflow.add_edge("rag_streaming", END)

    return workflow.compile()


def build_multi_turn_graph():
    """Multi-turn conversational RAG workflow"""
    workflow = StateGraph(RAGState)

    workflow.add_node("conversation", multi_turn_conversation_node)
    workflow.set_entry_point("conversation")
    workflow.add_edge("conversation", END)

    return workflow.compile()


# ============================================================================
# Example Usage
# ============================================================================

def main():
    # Initialize client
    client = OpenAI(base_url=f"{LLAMA_STACK_BASE_URL}/v1/", api_key="none")

    # Setup vector store
    vector_store_id = setup_vector_store(client)

    print("=" * 80)
    print("EXAMPLE 1: Simple RAG Query")
    print("=" * 80)

    # Build and run simple RAG graph
    app = build_simple_rag_graph()
    result = app.invoke({
        "messages": [],
        "question": "How do you do great work?",
        "vector_store_id": vector_store_id,
        "answer": "",
        "search_results": [],
        "metadata": {}
    })

    print(f"Answer: {result['answer'][:200]}...\n")

    print("=" * 80)
    print("EXAMPLE 2: Streaming RAG")
    print("=" * 80)

    # Build and run streaming graph
    streaming_app = build_streaming_rag_graph()
    result = streaming_app.invoke({
        "messages": [],
        "question": "What are the key principles of great work?",
        "vector_store_id": vector_store_id,
        "answer": "",
        "search_results": [],
        "metadata": {}
    })

    print(f"Metadata: {result['metadata']}\n")

    print("=" * 80)
    print("EXAMPLE 3: Multi-Turn Conversation")
    print("=" * 80)

    # Build multi-turn graph
    conversation_app = build_multi_turn_graph()

    # First turn
    state = {
        "messages": [],
        "question": "What does Paul Graham say about finding work you love?",
        "vector_store_id": vector_store_id,
        "answer": "",
        "search_results": [],
        "metadata": {}
    }

    result = conversation_app.invoke(state)

    # Second turn (follow-up question with context)
    result = conversation_app.invoke({
        **result,
        "question": "Can you give specific examples from the text?"
    })

    print(f"Final conversation length: {len(result['messages'])} messages\n")


if __name__ == "__main__":
    main()