#!/bin/bash

# Get feedback score and comment for a Langfuse trace
# Usage: ./get-trace-feedback.sh [trace_id]
#        If no trace_id provided, gets the latest trace

# Load environment variables from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/langgraph-agent/backend/.env"

if [ -f "$ENV_FILE" ]; then
    # Extract values, removing quotes
    LANGFUSE_PUBLIC_KEY=$(grep "^LANGFUSE_PUBLIC_KEY" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')
    LANGFUSE_SECRET_KEY=$(grep "^LANGFUSE_SECRET_KEY" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')
    LANGFUSE_HOST=$(grep "^LANGFUSE_HOST" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')
else
    echo "Error: .env file not found at $ENV_FILE"
    echo "Using environment variables if set..."
fi

# Check required variables
if [ -z "$LANGFUSE_PUBLIC_KEY" ] || [ -z "$LANGFUSE_SECRET_KEY" ] || [ -z "$LANGFUSE_HOST" ]; then
    echo "Error: Missing Langfuse credentials"
    echo "Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST"
    exit 1
fi

TRACE_ID="$1"

# If no trace ID provided, get the latest
if [ -z "$TRACE_ID" ]; then
    echo "No trace ID provided, fetching latest trace..."
    TRACE_ID=$(curl -s -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
        "${LANGFUSE_HOST}/api/public/traces?limit=1" | \
        python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data'][0]['id'] if d.get('data') else '')" 2>/dev/null)

    if [ -z "$TRACE_ID" ]; then
        echo "Error: No traces found"
        exit 1
    fi
    echo "Latest trace ID: $TRACE_ID"
fi

echo ""
echo "Fetching trace: $TRACE_ID"
echo "================================================"

# Get trace details with scores
curl -s -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
    "${LANGFUSE_HOST}/api/public/traces/${TRACE_ID}" | \
python3 -c "
import sys, json

try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    print('Error: Invalid response from Langfuse')
    sys.exit(1)

if 'error' in d or 'message' in d:
    print(f'Error: {d.get(\"message\", d.get(\"error\", \"Unknown error\"))}')
    sys.exit(1)

print(f'Name: {d.get(\"name\", \"N/A\")}')
print(f'Timestamp: {d.get(\"timestamp\", \"N/A\")}')

input_data = d.get('input', {})
if isinstance(input_data, dict):
    print(f'Input: {input_data.get(\"message\", input_data)}')
else:
    print(f'Input: {input_data}')

output_data = d.get('output', {})
if isinstance(output_data, dict):
    response = output_data.get('response', str(output_data))
    if len(response) > 200:
        response = response[:200] + '...'
    print(f'Output: {response}')
else:
    print(f'Output: {str(output_data)[:200]}')

scores = d.get('scores', [])
print('')
print('Feedback:')
print('---------')
if not scores:
    print('  No feedback found for this trace')
else:
    for score in scores:
        name = score.get('name', 'unknown')
        value = score.get('value')
        comment = score.get('comment', '')
        timestamp = score.get('timestamp', '')

        # Interpret value for user-feedback
        if name == 'user-feedback':
            rating = 'thumbs up' if value == 1 else 'thumbs down'
            print(f'  Score: {rating} ({value})')
        else:
            print(f'  {name}: {value}')

        if comment:
            print(f'  Comment: {comment}')
        if timestamp:
            print(f'  Time: {timestamp}')
        print('')
"
