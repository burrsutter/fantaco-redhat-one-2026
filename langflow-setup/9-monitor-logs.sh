#!/bin/bash
# Monitor logs, messages, and debug information for a Langflow flow
# Useful for debugging when a flow will not execute correctly
# Requires: LANGFLOW_API_URL, LANGFLOW_API_KEY

set -e

# Check required environment variables
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

# Determine flow ID
if [ -n "$1" ]; then
    FLOW_ID="$1"
    echo "Using flow ID from argument: $FLOW_ID"
elif [ -n "$LANGFLOW_FLOW_ID" ]; then
    FLOW_ID="$LANGFLOW_FLOW_ID"
    echo "Using flow ID from env: $FLOW_ID"
else
    echo "Fetching most recent flow..."
    FLOWS_RESPONSE=$(curl -sL --compressed -H "x-api-key:$LANGFLOW_API_KEY" "$LANGFLOW_API_URL/api/v1/flows")

    if echo "$FLOWS_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
        echo "API Error: $(echo "$FLOWS_RESPONSE" | jq -r '.detail')"
        exit 1
    fi

    FLOW_ID=$(echo "$FLOWS_RESPONSE" | jq -r 'sort_by(.updated_at) | last | .id')
    FLOW_NAME=$(echo "$FLOWS_RESPONSE" | jq -r 'sort_by(.updated_at) | last | .name')

    if [ "$FLOW_ID" == "null" ] || [ -z "$FLOW_ID" ]; then
        echo "Error: No flows found"
        exit 1
    fi

    echo "Using most recent flow: $FLOW_NAME ($FLOW_ID)"
fi

echo ""
echo "========================================"
echo "LANGFLOW FLOW MONITOR & DEBUG"
echo "========================================"
echo "API URL: $LANGFLOW_API_URL"
echo "Flow ID: $FLOW_ID"
echo "========================================"

# Get flow details
echo ""
echo ">>> FLOW DETAILS"
echo "----------------------------------------"
FLOW_RESPONSE=$(curl -sL --compressed -H "x-api-key:$LANGFLOW_API_KEY" "$LANGFLOW_API_URL/api/v1/flows/$FLOW_ID")

if echo "$FLOW_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    echo "Error fetching flow: $(echo "$FLOW_RESPONSE" | jq -r '.detail')"
else
    echo "Name: $(echo "$FLOW_RESPONSE" | jq -r '.name')"
    echo "Description: $(echo "$FLOW_RESPONSE" | jq -r '.description // "None"')"
    echo "Updated: $(echo "$FLOW_RESPONSE" | jq -r '.updated_at')"
    echo ""
    echo "Components:"
    echo "$FLOW_RESPONSE" | jq -r '.data.nodes[] | "  - \(.data.node.display_name // .data.type) (\(.id))"' 2>/dev/null || echo "  Could not parse components"
fi

# Get sessions for this flow
echo ""
echo ">>> SESSIONS"
echo "----------------------------------------"
SESSIONS_RESPONSE=$(curl -sL --compressed -H "x-api-key:$LANGFLOW_API_KEY" "$LANGFLOW_API_URL/api/v1/monitor/messages/sessions?flow_id=$FLOW_ID")

if echo "$SESSIONS_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    echo "Error fetching sessions: $(echo "$SESSIONS_RESPONSE" | jq -r '.detail')"
else
    SESSION_COUNT=$(echo "$SESSIONS_RESPONSE" | jq 'length')
    echo "Total sessions: $SESSION_COUNT"

    if [ "$SESSION_COUNT" != "0" ]; then
        echo "Session IDs:"
        echo "$SESSIONS_RESPONSE" | jq -r '.[] | "  - \(.)"' 2>/dev/null | head -10
        if [ "$SESSION_COUNT" -gt 10 ]; then
            echo "  ... and $((SESSION_COUNT - 10)) more"
        fi
    fi
fi

# Get recent messages for this flow
echo ""
echo ">>> RECENT MESSAGES"
echo "----------------------------------------"
MESSAGES_RESPONSE=$(curl -sL --compressed -H "x-api-key:$LANGFLOW_API_KEY" "$LANGFLOW_API_URL/api/v1/monitor/messages?flow_id=$FLOW_ID")

if echo "$MESSAGES_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    echo "Error fetching messages: $(echo "$MESSAGES_RESPONSE" | jq -r '.detail')"
else
    MSG_COUNT=$(echo "$MESSAGES_RESPONSE" | jq 'length')
    echo "Total messages: $MSG_COUNT"

    if [ "$MSG_COUNT" != "0" ]; then
        echo ""
        echo "Last 5 messages:"
        echo "$MESSAGES_RESPONSE" | jq -r '
            sort_by(.timestamp) |
            reverse |
            .[0:5] |
            .[] |
            "[\(.timestamp)] \(.sender_name // .sender): \(.text[0:100])..."
        ' 2>/dev/null || echo "Could not parse messages"
    fi
fi

# Get builds/vertex builds (if available)
echo ""
echo ">>> BUILD STATUS"
echo "----------------------------------------"
BUILD_RESPONSE=$(curl -sL --compressed -H "x-api-key:$LANGFLOW_API_KEY" "$LANGFLOW_API_URL/api/v1/build/$FLOW_ID/status" 2>/dev/null)

if echo "$BUILD_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    echo "No build status available or endpoint not supported"
else
    if [ -n "$BUILD_RESPONSE" ] && [ "$BUILD_RESPONSE" != "null" ]; then
        echo "$BUILD_RESPONSE" | jq '.' 2>/dev/null || echo "Could not parse build status"
    else
        echo "No build status available"
    fi
fi

# Try to get any error logs
echo ""
echo ">>> ERROR CHECK (Test Run)"
echo "----------------------------------------"
echo "Executing test query to check for errors..."

TEST_RESPONSE=$(curl -sL --compressed -X POST \
    -H "x-api-key:$LANGFLOW_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"input_value": "test"}' \
    "$LANGFLOW_API_URL/api/v1/run/$FLOW_ID" 2>&1)

if echo "$TEST_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    echo ""
    echo "ERROR DETECTED:"
    echo "----------------------------------------"
    echo "$TEST_RESPONSE" | jq -r '.detail' 2>/dev/null || echo "$TEST_RESPONSE"

    # Try to extract more error details
    if echo "$TEST_RESPONSE" | jq -e '.message' >/dev/null 2>&1; then
        echo ""
        echo "Error Message:"
        echo "$TEST_RESPONSE" | jq -r '.message'
    fi

    if echo "$TEST_RESPONSE" | jq -e '.traceback' >/dev/null 2>&1; then
        TRACEBACK=$(echo "$TEST_RESPONSE" | jq -r '.traceback')
        if [ "$TRACEBACK" != "null" ] && [ -n "$TRACEBACK" ]; then
            echo ""
            echo "Traceback:"
            echo "$TRACEBACK"
        fi
    fi
else
    OUTPUT=$(echo "$TEST_RESPONSE" | jq -r '.outputs[0].outputs[0].results.message.text // .outputs[0].outputs[0].messages[0].message // "No output"' 2>/dev/null)
    if [ "$OUTPUT" != "No output" ] && [ -n "$OUTPUT" ]; then
        echo "Flow executed successfully!"
        echo "Test response preview: ${OUTPUT:0:200}..."
    else
        echo "Flow executed but no output captured"
        echo "Raw response:"
        echo "$TEST_RESPONSE" | jq '.' 2>/dev/null | head -30
    fi
fi

echo ""
echo "========================================"
echo "MONITOR COMPLETE"
echo "========================================"
echo ""
echo "Tips for debugging:"
echo "  - Check component connections in the Langflow UI"
echo "  - Verify MCP server URLs are accessible"
echo "  - Confirm LLM endpoint and API key are valid"
echo "  - Review the error message above for specific issues"
