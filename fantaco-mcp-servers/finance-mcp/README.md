## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with the following variables:

```env
FINANCE_API_BASE_URL=http://localhost:8082
PORT_FOR_FINANCE_MCP=9002
HOST_FOR_FINANCE_MCP=0.0.0.0
```

## Running the Server

```bash
python finance-api-mcp-server.py
```

The server will start on the configured host and port (default: http://0.0.0.0:9002).

## Tests

### Check Server is Running

```bash
set -a
source .env
set +a
echo $PORT_FOR_FINANCE_MCP
echo $HOST_FOR_FINANCE_MCP

# Check if server is listening
lsof -i :$PORT_FOR_FINANCE_MCP
```

```bash
brew install mcp-inspector
mcp-inspector
```
