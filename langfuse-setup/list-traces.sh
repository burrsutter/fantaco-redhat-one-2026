#!/bin/bash

# List the last N traces with their IDs and user queries
# Usage: ./list-traces.sh [count]
#        Default: 10 traces

# Load environment variables from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/langgraph-agent/backend/.env"

if [ -f "$ENV_FILE" ]; then
    LANGFUSE_PUBLIC_KEY=$(grep "^LANGFUSE_PUBLIC_KEY" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')
    LANGFUSE_SECRET_KEY=$(grep "^LANGFUSE_SECRET_KEY" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')
    LANGFUSE_HOST=$(grep "^LANGFUSE_HOST" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')
else
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

if [ -z "$LANGFUSE_PUBLIC_KEY" ] || [ -z "$LANGFUSE_SECRET_KEY" ] || [ -z "$LANGFUSE_HOST" ]; then
    echo "Error: Missing Langfuse credentials"
    exit 1
fi

COUNT="${1:-10}"

echo "Fetching last $COUNT traces..."
echo ""

curl -s -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
    "${LANGFUSE_HOST}/api/public/traces?limit=${COUNT}" | \
python3 -c "
import sys, json

try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    print('Error: Invalid response from Langfuse')
    sys.exit(1)

traces = d.get('data', [])
if not traces:
    print('No traces found')
    sys.exit(0)

# Print header
print(f'{'TRACE ID':<34} {'QUERY':<50}')
print('=' * 85)

for trace in traces:
    trace_id = trace.get('id', 'N/A')

    # Extract query from input
    input_data = trace.get('input', {})
    if isinstance(input_data, dict):
        query = input_data.get('message', str(input_data))
    else:
        query = str(input_data) if input_data else 'N/A'

    # Truncate query if too long
    if len(query) > 48:
        query = query[:45] + '...'

    print(f'{trace_id:<34} {query:<50}')
"
