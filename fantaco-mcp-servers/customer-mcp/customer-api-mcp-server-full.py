#!/usr/bin/env python3
"""
FastMCP server for Fantaco Customer API
Provides tools to interact with the Fantaco Customer Service API
Based on OpenAPI specification v0

Server Configuration:
    - Transport: SSE (Server-Sent Events) over HTTP
    - Port: 9001
    - Host: 0.0.0.0 (all interfaces)

Environment Variables:
    CUSTOMER_API_BASE_URL: Base URL for the Customer API (optional)
                          Default: http://fantaco-customer-service-fantaco.apps.cluster-5q8cb.5q8cb.sandbox1196.opentlc.com
"""

from mcp.server.fastmcp import FastMCP
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

# Create a shared httpx client
http_client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


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

    response = await http_client.get("/api/customers", params=params)
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
    response = await http_client.get(f"/api/customers/{customer_id}")
    return await handle_response(response)


@mcp.tool()
async def create_customer(
    customer_id: str,
    company_name: str,
    contact_name: Optional[str] = None,
    contact_title: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    region: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: Optional[str] = None,
    phone: Optional[str] = None,
    fax: Optional[str] = None,
    contact_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new customer

    Creates a new customer record with the provided information

    Args:
        customer_id: Unique 5-character customer identifier (required, must be exactly 5 characters)
        company_name: Company name (required, max 40 characters)
        contact_name: Contact person name (optional, max 30 characters)
        contact_title: Contact person title (optional, max 30 characters)
        address: Street address (optional, max 60 characters)
        city: City name (optional, max 15 characters)
        region: State/Region/Province (optional, max 15 characters)
        postal_code: ZIP/Postal code (optional, max 10 characters)
        country: Country name (optional, max 15 characters)
        phone: Phone number (optional, max 24 characters)
        fax: Fax number (optional, max 24 characters)
        contact_email: Contact email address (optional, max 255 characters)

    Returns:
        Created customer details with timestamps
    """
    customer_data = {
        "customerId": customer_id,
        "companyName": company_name
    }

    # Add optional fields if provided
    if contact_name:
        customer_data["contactName"] = contact_name
    if contact_title:
        customer_data["contactTitle"] = contact_title
    if address:
        customer_data["address"] = address
    if city:
        customer_data["city"] = city
    if region:
        customer_data["region"] = region
    if postal_code:
        customer_data["postalCode"] = postal_code
    if country:
        customer_data["country"] = country
    if phone:
        customer_data["phone"] = phone
    if fax:
        customer_data["fax"] = fax
    if contact_email:
        customer_data["contactEmail"] = contact_email

    response = await http_client.post("/api/customers", json=customer_data)
    return await handle_response(response)


@mcp.tool()
async def update_customer(
    customer_id: str,
    company_name: str,
    contact_name: Optional[str] = None,
    contact_title: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    region: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: Optional[str] = None,
    phone: Optional[str] = None,
    fax: Optional[str] = None,
    contact_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing customer

    Updates an existing customer record. Note: company_name is required for updates.

    Args:
        customer_id: The unique 5-character identifier of the customer (required)
        company_name: Company name (required, max 40 characters)
        contact_name: Contact person name (optional, max 30 characters)
        contact_title: Contact person title (optional, max 30 characters)
        address: Street address (optional, max 60 characters)
        city: City name (optional, max 15 characters)
        region: State/Region/Province (optional, max 15 characters)
        postal_code: ZIP/Postal code (optional, max 10 characters)
        country: Country name (optional, max 15 characters)
        phone: Phone number (optional, max 24 characters)
        fax: Fax number (optional, max 24 characters)
        contact_email: Contact email address (optional, max 255 characters)

    Returns:
        Updated customer details
    """
    customer_data = {
        "companyName": company_name
    }

    # Add optional fields if provided
    if contact_name is not None:
        customer_data["contactName"] = contact_name
    if contact_title is not None:
        customer_data["contactTitle"] = contact_title
    if address is not None:
        customer_data["address"] = address
    if city is not None:
        customer_data["city"] = city
    if region is not None:
        customer_data["region"] = region
    if postal_code is not None:
        customer_data["postalCode"] = postal_code
    if country is not None:
        customer_data["country"] = country
    if phone is not None:
        customer_data["phone"] = phone
    if fax is not None:
        customer_data["fax"] = fax
    if contact_email is not None:
        customer_data["contactEmail"] = contact_email

    response = await http_client.put(f"/api/customers/{customer_id}", json=customer_data)
    return await handle_response(response)


@mcp.tool()
async def delete_customer(customer_id: str) -> Dict[str, Any]:
    """
    Delete customer

    Permanently deletes a customer record (hard delete)

    Args:
        customer_id: The unique 5-character identifier of the customer

    Returns:
        Deletion confirmation (HTTP 204 on success)
    """
    response = await http_client.delete(f"/api/customers/{customer_id}")
    return await handle_response(response)


# Cleanup handler
@mcp.on_shutdown
async def cleanup():
    """Close the HTTP client on shutdown"""
    await http_client.aclose()


if __name__ == "__main__":
    # Run the MCP server with SSE transport on port 9001
    import uvicorn
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=9001)
