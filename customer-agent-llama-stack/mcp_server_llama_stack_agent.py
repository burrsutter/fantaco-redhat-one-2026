#!/usr/bin/env python3
"""
MCP Server wrapping Llama Stack Customer Agent

This MCP server exposes the Llama Stack customer agent as an MCP tool.
It uses FastMCP with SSE transport to provide a customer_agent tool that
accepts prompts and returns responses from the underlying agent.

Architecture:
┌─────────────────────────────────────────────┐
│         MCP Client                          │
│         (Connects via SSE)                  │
└────────┬────────────────────────────────────┘
         │
         │ customer_agent(prompt)
         ▼
┌─────────────────────────────────────────────┐
│         FastMCP Server (This File)          │
│         - SSE Transport                     │
│         - Tool: customer_agent              │
└────────┬────────────────────────────────────┘
         │
         │ Uses Llama Stack SDK
         ▼
┌─────────────────────────────────────────────┐
│         Llama Stack Agent                   │
│         (lls_customer_agent.py)             │
│         - Calls Customer MCP Server         │
└─────────────────────────────────────────────┘
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from llama_stack_client import LlamaStackClient
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_server_llama_stack.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = find_dotenv(usecwd=True)
if env_path:
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from: {env_path}")
else:
    logger.warning("No .env file found, using system environment variables")

# Get port configuration
CUSTOMER_AGENT_PORT = int(os.getenv("CUSTOMER_AGENT_PORT", "8000"))
logger.info(f"CUSTOMER_AGENT_PORT: {CUSTOMER_AGENT_PORT}")

# Initialize FastMCP server with port configuration
logger.info("Initializing FastMCP server: Customer Agent MCP Server")
mcp = FastMCP("Customer Agent MCP Server", port=CUSTOMER_AGENT_PORT)

# Global Llama Stack client
llama_client = None


def get_llama_client():
    """Get or create Llama Stack client."""
    global llama_client
    if llama_client is None:
        LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")
        logger.info(f"Creating new Llama Stack client with base_url: {LLAMA_STACK_BASE_URL}")
        llama_client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)
        logger.info("Llama Stack client created successfully")
    return llama_client


@mcp.tool()
def customer_agent(prompt: str) -> str:
    """
    Execute the customer agent with the given prompt.

    This tool wraps the Llama Stack customer agent, which uses MCP tools
    from the customer microservice to answer questions about customers.

    Args:
        prompt: The question or instruction for the customer agent

    Returns:
        The agent's response as a string

    Examples:
        - "Search customer with name Anabela Domingues"
        - "Give me list of customers of Fantaco company"
        - "Find customer with email john@example.com"
    """
    logger.info(f"customer_agent called with prompt: {prompt[:100]}...")
    try:
        client = get_llama_client()

        INFERENCE_MODEL = os.getenv("INFERENCE_MODEL")
        MCP_CUSTOMER_SERVER_URL = os.getenv("MCP_CUSTOMER_SERVER_URL")

        logger.info(f"INFERENCE_MODEL: {INFERENCE_MODEL}")
        logger.info(f"MCP_CUSTOMER_SERVER_URL: {MCP_CUSTOMER_SERVER_URL}")

        if not MCP_CUSTOMER_SERVER_URL:
            logger.error("MCP_CUSTOMER_SERVER_URL not configured in environment")
            return "Error: MCP_CUSTOMER_SERVER_URL not configured in environment"

        # Use Llama Stack's Responses API with MCP tools
        logger.info("Calling Llama Stack responses API...")
        agent_responses = client.responses.create(
            model=INFERENCE_MODEL,
            input=prompt,
            tools=[
                {
                    "type": "mcp",
                    "server_url": MCP_CUSTOMER_SERVER_URL,
                    "server_label": "customer",
                }
            ],
        )

        # Return the final text response
        logger.info(f"Agent response received: {agent_responses.output_text[:100]}...")
        return agent_responses.output_text

    except Exception as e:
        logger.error(f"Error executing customer agent: {str(e)}", exc_info=True)
        return f"Error executing customer agent: {str(e)}"


@mcp.tool()
def customer_agent_detailed(prompt: str) -> str:
    """
    Execute the customer agent with detailed execution trace.

    This tool provides the same functionality as customer_agent but includes
    detailed information about tool discovery, tool calls, and execution steps.

    Args:
        prompt: The question or instruction for the customer agent

    Returns:
        A detailed JSON string containing the execution trace and final response
    """
    logger.info(f"customer_agent_detailed called with prompt: {prompt[:100]}...")
    try:
        client = get_llama_client()

        INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "ollama/llama3.2:3b")
        MCP_CUSTOMER_SERVER_URL = os.getenv("MCP_CUSTOMER_SERVER_URL")

        logger.info(f"Using inference model: {INFERENCE_MODEL}")
        logger.info(f"MCP Customer Server URL: {MCP_CUSTOMER_SERVER_URL}")

        if not MCP_CUSTOMER_SERVER_URL:
            logger.error("MCP_CUSTOMER_SERVER_URL not configured in environment")
            return json.dumps({"error": "MCP_CUSTOMER_SERVER_URL not configured"})

        # Use Llama Stack's Responses API with MCP tools
        logger.info("Calling Llama Stack responses API with detailed trace...")
        agent_responses = client.responses.create(
            model=INFERENCE_MODEL,
            input=prompt,
            tools=[
                {
                    "type": "mcp",
                    "server_url": MCP_CUSTOMER_SERVER_URL,
                    "server_label": "customer",
                }
            ],
        )

        # Build detailed trace
        logger.info("Building detailed execution trace...")
        trace = []
        for i, output in enumerate(agent_responses.output):
            trace_item = {
                "step": i + 1,
                "type": output.type
            }

            if output.type == "mcp_list_tools":
                trace_item["server"] = output.server_label
                trace_item["tools"] = [t.name for t in output.tools]
                logger.debug(f"Step {i+1}: Listed {len(output.tools)} tools from {output.server_label}")

            elif output.type == "mcp_call":
                trace_item["tool_name"] = output.name
                trace_item["arguments"] = output.arguments
                if output.error:
                    trace_item["error"] = output.error
                    logger.warning(f"Step {i+1}: Tool call to {output.name} failed: {output.error}")
                else:
                    logger.debug(f"Step {i+1}: Called tool {output.name}")

            elif output.type == "message":
                trace_item["role"] = output.role
                if hasattr(output.content[0], 'text'):
                    trace_item["content"] = output.content[0].text
                logger.debug(f"Step {i+1}: Message from {output.role}")

            trace.append(trace_item)

        result = {
            "trace": trace,
            "final_response": agent_responses.output_text
        }

        logger.info(f"Detailed trace completed with {len(trace)} steps")
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error executing customer agent (detailed): {str(e)}", exc_info=True)
        return json.dumps({"error": f"Error executing customer agent: {str(e)}"})


if __name__ == "__main__":
    # Run the MCP server with streamable HTTP transport
    # The server will be available for HTTP streaming connections
    logger.info("Starting MCP server with streamable-http transport...")

    # Log all environment variables used by this server
    LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")
    INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "ollama/llama3.2:3b")
    MCP_CUSTOMER_SERVER_URL = os.getenv("MCP_CUSTOMER_SERVER_URL")

    logger.info("=" * 60)
    logger.info("Environment Configuration:")
    logger.info(f"  LLAMA_STACK_BASE_URL: {LLAMA_STACK_BASE_URL}")
    logger.info(f"  INFERENCE_MODEL: {INFERENCE_MODEL}")
    logger.info(f"  MCP_CUSTOMER_SERVER_URL: {MCP_CUSTOMER_SERVER_URL}")
    logger.info(f"  CUSTOMER_AGENT_PORT: {CUSTOMER_AGENT_PORT}")
    logger.info("=" * 60)

    mcp.run(transport="streamable-http")
