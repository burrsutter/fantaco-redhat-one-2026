from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from typing import Annotated, Optional, Union
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.getenv("LLAMA_STACK_BASE_URL")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL")
API_KEY = os.getenv("API_KEY")
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8001"))

logger.info("Configuration loaded:")
logger.info("  Base URL: %s", BASE_URL)
logger.info("  Model: %s", INFERENCE_MODEL)
logger.info("  API Key: %s", "***" if API_KEY else "None")
logger.info("  FastAPI Host: %s", FASTAPI_HOST)
logger.info("  FastAPI Port: %s", FASTAPI_PORT)

# Initialize LLM
llm = ChatOpenAI(
    model=INFERENCE_MODEL,
    openai_api_key=API_KEY,
    base_url=f"{BASE_URL}/v1/openai/v1",
    use_responses_api=True
)

logger.info("Testing LLM connectivity...")
connectivity_response = llm.invoke("Hello")
logger.info("LLM connectivity test successful")

# MCP tool binding - both customer and finance MCP servers
llm_with_tools = llm.bind(
    tools=[
        {
            "type": "mcp",
            "server_label": "customer_mcp",
            "server_url": os.getenv("CUSTOMER_MCP_SERVER_URL"),
            "require_approval": "never",
        },
        {
            "type": "mcp",
            "server_label": "finance_mcp",
            "server_url": os.getenv("FINANCE_MCP_SERVER_URL"),
            "require_approval": "never",
        },
    ])


class State(TypedDict):
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    return {"messages": [message]}


# Build the graph
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

# FastAPI app
app = FastAPI(title="Customer Orders and Invoices API")


# Response models
class Customer(BaseModel):
    customerId: str
    companyName: Optional[str] = None
    contactName: Optional[str] = None
    contactEmail: Optional[str] = None


class Order(BaseModel):
    id: Optional[Union[str, int]] = None
    orderId: Optional[Union[str, int]] = None
    orderNumber: Optional[str] = None
    orderDate: Optional[str] = None
    status: Optional[str] = None
    totalAmount: Optional[Union[str, int, float]] = None
    freight: Optional[Union[str, int, float]] = None


class Invoice(BaseModel):
    id: Optional[Union[str, int]] = None
    invoiceId: Optional[Union[str, int]] = None
    invoiceNumber: Optional[str] = None
    invoiceDate: Optional[str] = None
    status: Optional[str] = None
    totalAmount: Optional[Union[str, int, float]] = None
    amount: Optional[Union[str, int, float]] = None
    customerId: Optional[str] = None
    customerEmail: Optional[str] = None
    contactName: Optional[str] = None


class OrdersResponse(BaseModel):
    customer: Optional[Customer] = None
    orders: list[Order] = []
    total_orders: int = 0


class InvoicesResponse(BaseModel):
    customer: Optional[Customer] = None
    invoices: list[Invoice] = []
    total_invoices: int = 0


def extract_customer_and_data(response, data_type="orders"):
    """Extract customer info and orders/invoices from graph response"""
    customer_info = None
    data_list = []

    for m in response['messages']:
        if hasattr(m, 'content') and isinstance(m.content, list):
            for item in m.content:
                if isinstance(item, dict) and item.get('type') == 'mcp_call' and item.get('output'):
                    try:
                        output_data = json.loads(item['output'])

                        # Check if this is customer search results
                        if 'results' in output_data and output_data.get('results'):
                            customer_info = output_data['results'][0] if output_data['results'] else None

                        # Check if this is data (orders or invoices)
                        if 'data' in output_data and output_data.get('data'):
                            data_list = output_data['data']
                        elif data_type in output_data and output_data.get(data_type):
                            data_list = output_data[data_type]

                    except json.JSONDecodeError:
                        logger.warning("Could not parse tool output")

    return customer_info, data_list


@app.get("/")
def read_root():
    return {
        "message": "Customer Orders and Invoices API",
        "endpoints": {
            "find_orders": "/find_orders?email=<customer_email>",
            "find_invoices": "/find_invoices?email=<customer_email>",
            "question": "/question?q=<your_question>"
        }
    }


@app.get("/find_orders", response_model=OrdersResponse)
def find_orders(email: EmailStr):
    """Find all orders for a customer by email address"""
    logger.info("=" * 80)
    logger.info("API: Finding orders for: %s", email)
    logger.info("=" * 80)

    try:
        response = graph.invoke(
            {"messages": [{"role": "user", "content": f"Find all orders for {email}"}]})

        customer_info, orders = extract_customer_and_data(response, "orders")

        return OrdersResponse(
            customer=Customer(**customer_info) if customer_info else None,
            orders=[Order(**order) for order in orders],
            total_orders=len(orders)
        )

    except Exception as e:
        logger.error("Error finding orders: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error finding orders: {str(e)}")


@app.get("/find_invoices", response_model=InvoicesResponse)
def find_invoices(email: EmailStr):
    """Find all invoices for a customer by email address"""
    logger.info("=" * 80)
    logger.info("API: Finding invoices for: %s", email)
    logger.info("=" * 80)

    try:
        response = graph.invoke(
            {"messages": [{"role": "user", "content": f"Find all invoices for {email}"}]})

        customer_info, invoices = extract_customer_and_data(response, "invoices")

        # Enrich invoices with customer info
        enriched_invoices = []
        for invoice in invoices:
            if customer_info:
                invoice['customerId'] = invoice.get('customerId', customer_info.get('customerId'))
                invoice['customerEmail'] = invoice.get('customerEmail', customer_info.get('contactEmail'))
                invoice['contactName'] = customer_info.get('contactName')
            enriched_invoices.append(Invoice(**invoice))

        return InvoicesResponse(
            customer=Customer(**customer_info) if customer_info else None,
            invoices=enriched_invoices,
            total_invoices=len(invoices)
        )

    except Exception as e:
        logger.error("Error finding invoices: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error finding invoices: {str(e)}")


@app.get("/question")
def ask_question(q: str):
    """Answer a natural language question using the LangGraph chatbot"""
    logger.info("=" * 80)
    logger.info("API: Processing question: %s", q)
    logger.info("=" * 80)

    try:
        response = graph.invoke(
            {"messages": [{"role": "user", "content": q}]})

        # Extract the AI's response from the messages
        if response and 'messages' in response and len(response['messages']) > 0:
            last_message = response['messages'][-1]
            if hasattr(last_message, 'content'):
                # Handle both string content and list content
                if isinstance(last_message.content, str):
                    return {"question": q, "answer": last_message.content}
                elif isinstance(last_message.content, list):
                    # Extract text from list content
                    text_parts = []
                    for item in last_message.content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    return {"question": q, "answer": " ".join(text_parts)}

        return {"question": q, "answer": "No response generated"}

    except Exception as e:
        logger.error("Error processing question: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=FASTAPI_HOST, port=FASTAPI_PORT)
