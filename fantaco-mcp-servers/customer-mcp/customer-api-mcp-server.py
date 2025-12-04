#!/usr/bin/env python3
"""
FastMCP server for Fantaco Customer API (Read-Only)
Provides read-only tools to query the Fantaco Customer Service API
Based on OpenAPI specification v0

Server Configuration:
    - Transport: streamable HTTP
    - Port: 9001
    - Host: 0.0.0.0 (all interfaces)
    - Mode: Read-only (search and get operations only)

Environment Variables:
    CUSTOMER_API_BASE_URL: Base URL for the Customer API (optional)
                          Default: http://fantaco-customer-service-fantaco.apps.cluster-5q8cb.5q8cb.sandbox1196.opentlc.com
"""

from fastmcp import FastMCP
import asyncio
import httpx
import os
from typing import Optional, Dict, Any

# Initialize FastMCP server
mcp = FastMCP("customer-api")

# Base URL for the Customer API (configurable via environment variable)
BASE_URL = os.getenv(
    "CUSTOMER_API_BASE_URL",
    "http://fantaco-customer-service-fantaco.apps.cluster-5q8cb.5q8cb.sandbox1196.opentlc.com"
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
async def search_customers(
    company_name: Optional[str] = None,
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for customers by various fields with partial matching

    Args:
        company_name: Filter by company name (partial matching, optional)
        contact_name: Filter by contact person name (partial matching, optional)
        contact_email: Filter by contact email address (partial matching, optional)
        phone: Filter by phone number (partial matching, optional)

    Returns:
        List of customers matching the search criteria
    """
    params = {}

    if company_name:
        params["companyName"] = company_name
    if contact_name:
        params["contactName"] = contact_name
    if contact_email:
        params["contactEmail"] = contact_email
    if phone:
        params["phone"] = phone

    client = await get_http_client()
    response = await client.get("/api/customers", params=params)
    return await handle_response(response)


@mcp.tool()
async def get_customer(customer_id: str) -> Dict[str, Any]:
    """
    Get customer by ID

    Retrieves a single customer record by its unique identifier

    Args:
        customer_id: The unique 5-character identifier of the customer

    Returns:
        Customer details including customerId, companyName, contactName, contactTitle,
        address, city, region, postalCode, country, phone, fax, contactEmail,
        createdAt, and updatedAt
    """
    client = await get_http_client()
    response = await client.get(f"/api/customers/{customer_id}")
    return await handle_response(response)


async def cleanup():
    """Cleanup resources."""
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None


if __name__ == "__main__":
    # Run the server using HTTP transport on port 9001
    try:
        mcp.run(transport="http", port=9001, host="0.0.0.0")
    finally:
        asyncio.run(cleanup())
