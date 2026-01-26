#!/bin/bash
# List all Langflow flows via REST API
# Requires: LANGFLOW_API_URL environment variable (backend-only API endpoint)
# Requires: LANGFLOW_API_KEY for authenticated access

if [ -z "$LANGFLOW_API_URL" ]; then
    echo "Error: LANGFLOW_API_URL is not set"
    echo "Usage: export LANGFLOW_API_URL=https://langflow-api-xxx.apps.example.com"
    exit 1
fi

if [ -z "$LANGFLOW_API_KEY" ]; then
    echo "Error: LANGFLOW_API_KEY is not set"
    echo "Usage: export LANGFLOW_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    exit 1
fi

echo "Fetching flows from: $LANGFLOW_API_URL"
echo "----------------------------------------"

# Fetch flows with required API key
RESPONSE=$(curl -sL --compressed -H "x-api-key:$LANGFLOW_API_KEY" "$LANGFLOW_API_URL/api/v1/flows")

# Check if response is valid JSON
if ! echo "$RESPONSE" | jq -e . >/dev/null 2>&1; then
    echo "Error: Invalid response from API"
    echo "$RESPONSE" | head -5
    exit 1
fi

# Check for API error response
if echo "$RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    echo "API Error: $(echo "$RESPONSE" | jq -r '.detail')"
    exit 1
fi

# Check if response is an array
if [ "$(echo "$RESPONSE" | jq 'type')" != '"array"' ]; then
    echo "Error: Unexpected response format"
    echo "$RESPONSE" | jq .
    exit 1
fi

# Count flows
FLOW_COUNT=$(echo "$RESPONSE" | jq 'length')
echo "Found $FLOW_COUNT flow(s)"
echo "----------------------------------------"

# Display flows
if [ "$FLOW_COUNT" -gt 0 ]; then
    echo "$RESPONSE" | jq -r '
        .[] |
        "ID: \(.id)\nName: \(.name)\nDescription: \(.description // "N/A")\n----------------------------------------"
    '
fi
