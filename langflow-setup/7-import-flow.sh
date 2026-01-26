#!/bin/bash
# Import the vLLM Agent with Customer and Finance MCP flow
# Replaces localhost URLs with actual MCP server URLs
# Requires: LANGFLOW_API_URL, LANGFLOW_API_KEY, CUSTOMER_MCP_SERVER_URL, FINANCE_MCP_SERVER_URL

set -e

# Check required environment variables
if [ -z "$LANGFLOW_API_URL" ]; then
    echo "Error: LANGFLOW_API_URL is not set"
    echo "Usage: source 2-view-langflow-urls.sh"
    exit 1
fi

if [ -z "$LANGFLOW_API_KEY" ]; then
    echo "Error: LANGFLOW_API_KEY is not set"
    echo "Usage: export LANGFLOW_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    exit 1
fi

if [ -z "$CUSTOMER_MCP_SERVER_URL" ]; then
    echo "Error: CUSTOMER_MCP_SERVER_URL is not set"
    echo "Usage: source export_customer_finance_mcp_urls.sh"
    exit 1
fi

if [ -z "$FINANCE_MCP_SERVER_URL" ]; then
    echo "Error: FINANCE_MCP_SERVER_URL is not set"
    echo "Usage: source export_customer_finance_mcp_urls.sh"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLOW_FILE="$SCRIPT_DIR/flow_examples/vLLM_MaaS_Agent_MCP_Customer_Finance.json"

if [ ! -f "$FLOW_FILE" ]; then
    echo "Error: Flow file not found: $FLOW_FILE"
    exit 1
fi

echo "Importing flow with MCP URLs:"
echo "  LANGFLOW_API_URL: $LANGFLOW_API_URL"
echo "  CUSTOMER_MCP_SERVER_URL: $CUSTOMER_MCP_SERVER_URL"
echo "  FINANCE_MCP_SERVER_URL: $FINANCE_MCP_SERVER_URL"
echo "----------------------------------------"

# Read flow JSON and replace localhost URLs with actual MCP server URLs
FLOW_JSON=$(cat "$FLOW_FILE" | \
    sed "s|http://localhost:9001/mcp|$CUSTOMER_MCP_SERVER_URL|g" | \
    sed "s|http://localhost:9002/mcp|$FINANCE_MCP_SERVER_URL|g")

# POST to Langflow API
RESPONSE=$(echo "$FLOW_JSON" | curl -sL --compressed -X POST \
    -H "Content-Type: application/json" \
    -H "x-api-key: $LANGFLOW_API_KEY" \
    -d @- \
    "$LANGFLOW_API_URL/api/v1/flows/")

# Check for API error
if echo "$RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    echo "API Error: $(echo "$RESPONSE" | jq -r '.detail')"
    exit 1
fi

# Extract flow ID and name
FLOW_ID=$(echo "$RESPONSE" | jq -r '.id')
FLOW_NAME=$(echo "$RESPONSE" | jq -r '.name')

if [ "$FLOW_ID" == "null" ] || [ -z "$FLOW_ID" ]; then
    echo "Error: Failed to import flow"
    echo "Response: $RESPONSE"
    exit 1
fi

echo "Flow imported successfully!"
echo "  Flow Name: $FLOW_NAME"
echo "  Flow ID: $FLOW_ID"
echo "----------------------------------------"
echo "To test this flow:"
echo "  export LANGFLOW_FLOW_ID=$FLOW_ID"
echo "  ./8-smoke-test-flow.sh"
echo ""
echo "Or invoke with a custom query:"
echo "  ./6-invoke-flow.sh \"Who is Thomas Hardy?\""
