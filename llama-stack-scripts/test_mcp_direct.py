#!/usr/bin/env python3
"""Test MCP server directly to see if it exposes tools."""

import asyncio
import httpx
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession


async def test_mcp_server():
    endpoints = [
        "http://localhost:9001",
        "http://localhost:9001/sse",
        "http://localhost:9001/mcp",
    ]

    for endpoint in endpoints:
        print(f"\n{'='*60}")
        print(f"Testing endpoint: {endpoint}")
        print(f"{'='*60}")

        # Try streamable HTTP first
        print("\n[1] Trying STREAMABLE HTTP protocol...")
        try:
            async with streamablehttp_client(endpoint) as client_streams:
                async with ClientSession(
                    read_stream=client_streams[0],
                    write_stream=client_streams[1]
                ) as session:
                    print("Connected! Initializing session...")
                    await session.initialize()

                    print("Listing tools...")
                    tools_result = await session.list_tools()

                    print(f"\n✓ Found {len(tools_result.tools)} tools:")
                    for tool in tools_result.tools:
                        print(f"  - {tool.name}: {tool.description}")
                    return  # Success!
        except Exception as e:
            print(f"✗ STREAMABLE HTTP failed: {e}")

        # Try SSE protocol
        print("\n[2] Trying SSE protocol...")
        try:
            async with sse_client(endpoint) as client_streams:
                async with ClientSession(
                    read_stream=client_streams[0],
                    write_stream=client_streams[1]
                ) as session:
                    print("Connected! Initializing session...")
                    await session.initialize()

                    print("Listing tools...")
                    tools_result = await session.list_tools()

                    print(f"\n✓ Found {len(tools_result.tools)} tools:")
                    for tool in tools_result.tools:
                        print(f"  - {tool.name}: {tool.description}")
                    return  # Success!
        except Exception as e:
            print(f"✗ SSE failed: {e}")

    print("\n" + "="*60)
    print("All attempts failed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
