# Customer Agent MCP Server

An MCP (Model Context Protocol) server that wraps a Llama Stack customer agent, exposing it as MCP tools via SSE (Server-Sent Events) transport using the FastMCP library.

## Architecture

```
┌─────────────────────────────────────────────┐
│         MCP Client                          │
│         (Connects via SSE)                  │
└────────┬────────────────────────────────────┘
         │
         │ customer_agent(prompt)
         ▼
┌─────────────────────────────────────────────┐
│         FastMCP Server                      │
│         - SSE Transport                     │
│         - Tools: customer_agent             │
│                  customer_agent_detailed    │
└────────┬────────────────────────────────────┘
         │
         │ Uses Llama Stack SDK
         ▼
┌─────────────────────────────────────────────┐
│         Llama Stack Agent                   │
│         - Calls Customer MCP Server         │
│         - Tool Discovery & Execution        │
└─────────────────────────────────────────────┘
```

## Components

### Files

- **mcp_server.py**: The main MCP server implementation using FastMCP
- **lls_customer_agent.py**: The underlying Llama Stack agent implementation
- **test_mcp_server.py**: Comprehensive test suite for the MCP server
- **example_client.py**: Example client demonstrating how to use the MCP server
- **Containerfile.mcp-server**: Container definition for deploying the MCP server
- **requirements.txt**: Python dependencies

### Available Tools

#### 1. `customer_agent`

Execute the customer agent with a given prompt.

**Parameters:**
- `prompt` (string): The question or instruction for the customer agent

**Returns:** String response from the agent

**Examples:**
- "Search customer with name Anabela Domingues"
- "Give me list of customers of Fantaco company"
- "Find customer with email john@example.com"

#### 2. `customer_agent_detailed`

Execute the customer agent with detailed execution trace.

**Parameters:**
- `prompt` (string): The question or instruction for the customer agent

**Returns:** JSON string containing execution trace and final response

## Installation

### Prerequisites

- Python 3.11+
- Access to a Llama Stack instance
- Access to a Customer MCP Server

### Setup

0. Have a Llama Stack Server

See main README.md 

1. Install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:

Edit the .env and/or create the env variables via the terminal

```bash
# Llama Stack Configuration
export LLAMA_STACK_BASE_URL=http://localhost:8321
export LLAMA_STACK_OPENAI_ENDPOINT=http://localhost:8321/v1
export API_KEY=fake
export INFERENCE_MODEL=ollama/llama3.2:3b
# export INFERENCE_MODEL=ollama/llama3.2:3b-instruct-fp16
# export INFERENCE_MODEL=ollama/qwen2.5-coder:14b-instruct-fp16

# MCP Server Configuration
MCP_CUSTOMER_SERVER_URL=http://localhost:9001/mcp
```

## Usage

### Running the MCP Server

Start the MCP server with HTTP transport:

```bash
python mcp_server_llama_stack_agent.py
```

By default, the server runs on `http://localhost:8000/mcp`

### Using the Example Client

Run the example client to see how to interact with the MCP server:

```bash
python test_mcp_client_langgraph.py
```

- [Llama Stack Documentation](https://llamastack.github.io/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Library](https://github.com/jlowin/fastmcp)
