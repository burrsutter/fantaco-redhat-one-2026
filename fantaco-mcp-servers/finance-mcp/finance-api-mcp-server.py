#!/usr/bin/env python3
"""
FastMCP server for Fantaco Finance API 
Provides tools to use the Fantaco Finance Service API
Based on OpenAPI specification v0

Server Configuration:
    - Transport: streamable HTTP
    - Port: 9002
    - Host: 0.0.0.0 (all interfaces)
    - Mode: Read-write (search, get, create, update, delete operations)

Environment Variables:
    FINANCE_API_BASE_URL: Base URL for the Finance API (optional)
                          Default: http://fantaco-finance-service-fantaco.apps.cluster-5q8cb.5q8cb.sandbox1196.opentlc.com
"""

from fastmcp import FastMCP
import asyncio
import httpx
import os
from typing import Optional, Dict, Any

# Initialize FastMCP server
mcp = FastMCP("finance-api")

# Base URL for the Finance API (configurable via environment variable)
BASE_URL = os.getenv(
    "FINANCE_API_BASE_URL",
    "http://fantaco-finance-service-fantaco.apps.cluster-5q8cb.5q8cb.sandbox1196.opentlc.com"
)

# HTTP client for API calls
http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client."""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    return http_client


async def handle_response(response: httpx.Response) -> Dict[str, Any]:
    """Handle HTTP response and return JSON or error message"""
    try:
        response.raise_for_status()
        if response.content:
            data = response.json()
            # MCP requires dict responses, so wrap lists in a dict
            if isinstance(data, list):
                return {"results": data}
            return data
        return {"status": "success", "status_code": response.status_code}
    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text
        return {
            "error": f"HTTP {e.response.status_code}",
            "detail": error_detail,
            "status_code": e.response.status_code
        }
    except Exception as e:
        return {"error": str(e)}



@mcp.tool()
async def fetch_order_history(
    customer_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get order history for a customer.

    Retrieves the order history for a specific customer with optional date filtering and pagination.

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST-12345")
        start_date: Start date for filtering orders in ISO 8601 format (e.g., "2024-01-15T10:30:00")
        end_date: End date for filtering orders in ISO 8601 format (e.g., "2024-01-31T23:59:59")
        limit: Maximum number of orders to return (default: 50)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if the request was successful
        - message: Description of the result
        - data: List of order objects with details (id, orderNumber, customerId, totalAmount, status, orderDate, etc.)
        - count: Number of orders returned
    """
    client = await get_http_client()

    # Build request payload
    payload = {
        "customerId": customer_id,
        "limit": limit
    }

    if start_date:
        payload["startDate"] = start_date
    if end_date:
        payload["endDate"] = end_date

    # Make POST request
    response = await client.post("/api/finance/orders/history", json=payload)

    return await handle_response(response)


@mcp.tool()
async def fetch_invoice_history(
    customer_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get invoice history for a customer.

    Retrieves the invoice history for a specific customer with optional date filtering and pagination.

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST-12345")
        start_date: Start date for filtering invoices in ISO 8601 format (e.g., "2024-01-15T10:30:00")
        end_date: End date for filtering invoices in ISO 8601 format (e.g., "2024-01-31T23:59:59")
        limit: Maximum number of invoices to return (default: 50)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if the request was successful
        - message: Description of the result
        - data: List of invoice objects with details (id, invoiceNumber, orderId, customerId, amount, status, invoiceDate, dueDate, paidDate, etc.)
        - count: Number of invoices returned
    """
    client = await get_http_client()

    # Build request payload
    payload = {
        "customerId": customer_id,
        "limit": limit
    }

    if start_date:
        payload["startDate"] = start_date
    if end_date:
        payload["endDate"] = end_date

    # Make POST request
    response = await client.post("/api/finance/invoices/history", json=payload)

    return await handle_response(response)


@mcp.tool()
async def start_duplicate_charge_dispute(
    customer_id: str,
    order_id: int,
    description: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Start a duplicate charge dispute.

    Creates a new dispute for a duplicate charge issue reported by a customer.

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST-12345")
        order_id: Unique identifier for the order (e.g., 12345)
        description: Detailed description of the duplicate charge issue (e.g., "I was charged twice for the same order on 2024-01-15")
        reason: Optional reason code for the dispute (e.g., "DUPLICATE_PAYMENT")

    Returns:
        Dictionary containing:
        - success: Boolean indicating if the request was successful
        - message: Description of the result
        - data: Dispute object with details (id, disputeNumber, orderId, customerId, disputeType, status, description, reason, disputeDate, createdAt, updatedAt)
    """
    client = await get_http_client()

    # Build request payload
    payload = {
        "customerId": customer_id,
        "orderId": order_id,
        "description": description
    }

    if reason:
        payload["reason"] = reason

    # Make POST request
    response = await client.post("/api/finance/disputes/duplicate-charge", json=payload)

    return await handle_response(response)


@mcp.tool()
async def find_lost_receipt(
    customer_id: str,
    order_id: int
) -> Dict[str, Any]:
    """
    Find or regenerate a lost receipt.

    Attempts to find an existing receipt or creates a new one for a lost receipt request.

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST-12345")
        order_id: Unique identifier for the order (e.g., 12345)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if the request was successful
        - message: Description of the result
        - data: Receipt object with details (id, receiptNumber, orderId, customerId, status, filePath, fileName, fileSize, mimeType, receiptDate, createdAt, updatedAt)
    """
    client = await get_http_client()

    # Build request payload
    payload = {
        "customerId": customer_id,
        "orderId": order_id
    }

    # Make POST request
    response = await client.post("/api/finance/receipts/find-lost", json=payload)

    return await handle_response(response)


async def cleanup():
    """Cleanup resources."""
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None


if __name__ == "__main__":
    # Run the server using HTTP transport on port 9002
    try:
        mcp.run(transport="http", port=9002, host="0.0.0.0")
    finally:
        asyncio.run(cleanup())
