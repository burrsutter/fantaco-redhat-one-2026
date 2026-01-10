#!/bin/bash

# List the last N traces with their IDs and user queries
# Usage: ./list-traces.sh [count]
#        Default: 10 traces
#
# Required environment variables:
#   LANGFUSE_PUBLIC_KEY - Public API key (pk-lf-...)
#   LANGFUSE_SECRET_KEY - Secret API key (sk-lf-...)
#   LANGFUSE_HOST       - Langfuse URL (https://...)

if [ -z "$LANGFUSE_PUBLIC_KEY" ] || [ -z "$LANGFUSE_SECRET_KEY" ] || [ -z "$LANGFUSE_HOST" ]; then
    echo "Error: Missing Langfuse credentials"
    echo "Required environment variables:"
    echo "  LANGFUSE_PUBLIC_KEY"
    echo "  LANGFUSE_SECRET_KEY"
    echo "  LANGFUSE_HOST"
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
