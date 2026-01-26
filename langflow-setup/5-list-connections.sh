#!/bin/bash
# List connections between components in a Langflow flow via REST API
# Requires: LANGFLOW_API_URL environment variable (backend-only API endpoint)
# Requires: LANGFLOW_API_KEY for authenticated access
# Optional: LANGFLOW_FLOW_ID - if not set, uses the most recent flow
# Optional: Pass full flow URL as argument (e.g., https://langflow-xxx/flow/uuid)

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

# Get flow ID - check command line arg first, then env var, then fetch most recent
if [ -n "$1" ]; then
    # Extract flow ID from URL (last path segment)
    FLOW_ID=$(echo "$1" | sed 's|.*/flow/||' | sed 's|/.*||')
    echo "Using flow ID from URL: $FLOW_ID"
elif [ -n "$LANGFLOW_FLOW_ID" ]; then
    FLOW_ID="$LANGFLOW_FLOW_ID"
    echo "Using provided flow ID: $FLOW_ID"
else
    echo "LANGFLOW_FLOW_ID not set, fetching most recent flow..."
    FLOWS_RESPONSE=$(curl -sL --compressed -H "x-api-key:$LANGFLOW_API_KEY" "$LANGFLOW_API_URL/api/v1/flows")

    # Check for API error
    if echo "$FLOWS_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
        echo "API Error: $(echo "$FLOWS_RESPONSE" | jq -r '.detail')"
        exit 1
    fi

    # Get the most recent flow (sorted by updated_at)
    FLOW_ID=$(echo "$FLOWS_RESPONSE" | jq -r 'sort_by(.updated_at) | last | .id')
    FLOW_NAME=$(echo "$FLOWS_RESPONSE" | jq -r 'sort_by(.updated_at) | last | .name')

    if [ "$FLOW_ID" == "null" ] || [ -z "$FLOW_ID" ]; then
        echo "Error: No flows found"
        exit 1
    fi

    echo "Using most recent flow: $FLOW_NAME ($FLOW_ID)"
fi

echo "----------------------------------------"

# Fetch the flow details
RESPONSE=$(curl -sL --compressed -H "x-api-key:$LANGFLOW_API_KEY" "$LANGFLOW_API_URL/api/v1/flows/$FLOW_ID")

# Check for API error
if echo "$RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    echo "API Error: $(echo "$RESPONSE" | jq -r '.detail')"
    exit 1
fi

# Extract and display flow info
FLOW_NAME=$(echo "$RESPONSE" | jq -r '.name')
FLOW_DESC=$(echo "$RESPONSE" | jq -r '.description // "N/A"')

echo "Flow: $FLOW_NAME"
echo "Description: $FLOW_DESC"
echo "----------------------------------------"
echo ""

# List connections (edges) in the flow
echo "Connections in flow:"
echo ""

echo "$RESPONSE" | jq -r '
    .data.edges[] |
    "  \(.source) --> \(.target)
   Source Output: \(.data.sourceHandle.name // "N/A")
   Target Input: \(.data.targetHandle.fieldName // "N/A")
   ---"
'

# Count connections
CONNECTION_COUNT=$(echo "$RESPONSE" | jq '.data.edges | length')
echo ""
echo "Total connections: $CONNECTION_COUNT"
