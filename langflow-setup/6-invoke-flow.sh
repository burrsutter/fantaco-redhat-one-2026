#!/bin/bash
# Invoke a Langflow flow via REST API
# Requires: LANGFLOW_API_URL environment variable (backend-only API endpoint)
# Requires: LANGFLOW_API_KEY for authenticated access
# Required: First argument is the flow URL (e.g., https://langflow-xxx/flow/uuid)
#           OR use LANGFLOW_FLOW_ID env var and pass message as first arg
# Required: Second argument (or first if using env var) is the chat input message

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

if [ -z "$1" ]; then
    echo "Error: Arguments required"
    echo "Usage: $0 <flow-url> \"your message\""
    echo "   or: $0 \"your message\" (with LANGFLOW_FLOW_ID set)"
    echo "Example: $0 https://langflow-xxx/flow/uuid \"what model are you?\""
    exit 1
fi

# Determine if first arg is a URL or a message
if [[ "$1" == http* ]]; then
    # First arg is URL, second is message
    FLOW_ID=$(echo "$1" | sed 's|.*/flow/||' | sed 's|/.*||')
    INPUT_MESSAGE="$2"
    echo "Using flow ID from URL: $FLOW_ID"

    if [ -z "$INPUT_MESSAGE" ]; then
        echo "Error: Chat input message is required as second argument"
        exit 1
    fi
elif [ -n "$LANGFLOW_FLOW_ID" ]; then
    # First arg is the message when using env var
    FLOW_ID="$LANGFLOW_FLOW_ID"
    INPUT_MESSAGE="$1"
    echo "Using provided flow ID: $FLOW_ID"
else
    # First arg is the message, use most recent flow
    INPUT_MESSAGE="$1"
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
echo "Input: $INPUT_MESSAGE"
echo "----------------------------------------"

# Invoke the flow
RESPONSE=$(curl -sL --compressed -X POST \
    -H "x-api-key:$LANGFLOW_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"input_value\": \"$INPUT_MESSAGE\"}" \
    "$LANGFLOW_API_URL/api/v1/run/$FLOW_ID")

# Check for API error
if echo "$RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    echo "API Error: $(echo "$RESPONSE" | jq -r '.detail')"
    exit 1
fi

# Extract and display the output
OUTPUT=$(echo "$RESPONSE" | jq -r '.outputs[0].outputs[0].results.message.text // .outputs[0].outputs[0].messages[0].message // "No output found"')

echo ""
echo "Output:"
echo "----------------------------------------"
echo "$OUTPUT"
echo "----------------------------------------"
