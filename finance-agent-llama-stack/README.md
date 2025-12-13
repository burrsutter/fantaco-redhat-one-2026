# Finance Agent MCP Server

An MCP (Model Context Protocol) server that wraps a Llama Stack finance agent, exposing it as MCP tools via SSE (Server-Sent Events) transport using the FastMCP library.

## Architecture

```
┌─────────────────────────────────────────────┐
│         MCP Client                          │
│         (Connects via SSE)                  │
└────────┬────────────────────────────────────┘
         │
         │ finance_agent(prompt)
         ▼
┌─────────────────────────────────────────────┐
│         FastMCP Server                      │
│         - SSE Transport                     │
│         - Tools: finance_agent              │
│                  finance_agent_detailed     │
└────────┬────────────────────────────────────┘
         │
         │ Uses Llama Stack SDK
         ▼
┌─────────────────────────────────────────────┐
│         Llama Stack Agent                   │
│         - Calls Finance MCP Server          │
│         - Tool Discovery & Execution        │
└─────────────────────────────────────────────┘
```

## Components

### Files

- **mcp_server.py**: The main MCP server implementation using FastMCP
- **lls_finance_agent.py**: The underlying Llama Stack agent implementation
- **test_mcp_server.py**: Comprehensive test suite for the MCP server
- **example_client.py**: Example client demonstrating how to use the MCP server
- **Containerfile**: Container definition for deploying the MCP server
- **requirements.txt**: Python dependencies

### Available Tools

#### 1. `finance_agent`

Execute the finance agent with a given prompt.

**Parameters:**
- `prompt` (string): The question or instruction for the finance agent

**Returns:** String response from the agent

**Examples:**
- "Get order history for customer TRADH"
- "Show me all invoices for customer LONEP"
- "Find orders with amount greater than 1000"
- "List all pending invoices"

#### 2. `finance_agent_detailed`

Execute the finance agent with detailed execution trace.

**Parameters:**
- `prompt` (string): The question or instruction for the finance agent

**Returns:** JSON string containing execution trace and final response

## Installation

### Prerequisites

- Python 3.11+
- Access to a Llama Stack instance
- Access to a Finance MCP Server

### Setup

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
MCP_FINANCE_SERVER_URL=http://localhost:9001/mcp
```

## Usage

### Running the MCP Server

Start the MCP server with SSE transport:

```bash
python mcp_server_llama_stack_agent.py
```

By default, the server runs on `http://localhost:8001/mcp`

### Using the Example Client

Run the example client to see how to interact with the MCP server:

```bash
python example_client.py
```

### Running Tests

Run the test suite:

```bash
# Run all tests with pytest
pytest test_mcp_server.py -v

# Run only direct function tests
python test_mcp_server.py
```

### Using with MCP Clients

The server can be used with any MCP-compatible client. For example, using the MCP SDK:

```python
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def use_finance_agent():
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "finance_agent",
                arguments={"prompt": "Get order history for customer TRADH"}
            )

            print(result.content[0].text)

asyncio.run(use_finance_agent())
```

## Container Deployment

### Building the Container

```bash
podman build -f Containerfile -t finance-agent-mcp-server .
```

### Running the Container

```bash
podman run -p 8000:8000 \
  -e LLAMA_STACK_BASE_URL=https://your-llama-stack-instance.com/ \
  -e MCP_FINANCE_SERVER_URL=https://your-finance-mcp-server.com/mcp \
  -e INFERENCE_MODEL=vllm-inference-1/llama-32-3b-instruct \
  finance-agent-mcp-server
```

## Development

### Project Structure

```
llamastack-agent-finance-mcp/
├── mcp_server.py              # Main MCP server
├── lls_finance_agent.py       # Llama Stack agent
├── test_mcp_server.py         # Test suite
├── example_client.py          # Example client
├── requirements.txt           # Dependencies
├── Containerfile              # Container definition
├── .env                       # Environment configuration
└── README.md                  # This file
```

### Adding New Tools

To add new tools to the MCP server, define them in `mcp_server.py`:

```python
@mcp.tool()
def my_custom_tool(param: str) -> str:
    """
    Description of your tool.

    Args:
        param: Description of parameter

    Returns:
        Description of return value
    """
    # Tool implementation
    return "result"
```

## Configuration Options

### FastMCP Server Options

The server can be configured by modifying the `mcp.run()` call in `mcp_server.py`:

```python
mcp.run(
    transport="sse",  # Transport type (sse, stdio)
    port=8000,        # Port number
    host="0.0.0.0"    # Host address
)
```

### Environment Variables

- `LLAMA_STACK_BASE_URL`: URL of the Llama Stack instance
- `LLAMA_STACK_OPENAI_ENDPOINT`: OpenAI-compatible endpoint (optional)
- `INFERENCE_MODEL`: Model identifier for inference
- `MCP_FINANCE_SERVER_URL`: URL of the finance MCP server
- `API_KEY`: API key for authentication (if required)

## Use Cases

The Finance Agent MCP Server can handle various financial queries:

### Order Management
- Retrieve order history for specific customers
- Search orders by amount, status, or date
- Track order fulfillment and shipping

### Invoice Management
- List all invoices for a customer
- Find pending or paid invoices
- Generate invoice summaries

### Financial Analytics
- Calculate total revenue by customer
- Analyze spending patterns
- Generate financial reports

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure Llama Stack is running and accessible
2. **MCP server not configured**: Check that `MCP_FINANCE_SERVER_URL` is set in `.env`
3. **Import errors**: Run `pip install -r requirements.txt` to install dependencies
4. **Port already in use**: Change the port in `mcp.run()` or stop the conflicting service

## License

This project is part of the BYO Agentic Framework.

## References

- [Llama Stack Documentation](https://llamastack.github.io/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Library](https://github.com/jlowin/fastmcp)
