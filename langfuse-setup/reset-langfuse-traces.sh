#!/bin/bash
# Reset/clear all traces from Langfuse using the Langfuse API
# Usage: ./reset-langfuse-traces.sh
#
# Required environment variables:
#   LANGFUSE_PUBLIC_KEY - Public API key (pk-lf-...)
#   LANGFUSE_SECRET_KEY - Secret API key (sk-lf-...)
#   LANGFUSE_HOST       - Langfuse URL (https://...)
#
# WARNING: This will DELETE ALL traces from Langfuse!

set -e

if [ -z "$LANGFUSE_PUBLIC_KEY" ] || [ -z "$LANGFUSE_SECRET_KEY" ] || [ -z "$LANGFUSE_HOST" ]; then
    echo "Error: Missing Langfuse credentials"
    echo "Required environment variables:"
    echo "  LANGFUSE_PUBLIC_KEY"
    echo "  LANGFUSE_SECRET_KEY"
    echo "  LANGFUSE_HOST"
    exit 1
fi

echo "============================================================"
echo "WARNING: This will DELETE ALL traces from Langfuse!"
echo "Langfuse Host: $LANGFUSE_HOST"
echo "============================================================"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Create basic auth header
AUTH=$(echo -n "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" | base64)

echo "Fetching traces from Langfuse API..."

# Counter for deleted traces
DELETED=0
ITERATIONS=0
MAX_ITERATIONS=5
LIMIT=100

while [ $ITERATIONS -lt $MAX_ITERATIONS ]; do
    ((ITERATIONS++))

    # Fetch traces
    RESPONSE=$(curl -s -X GET \
        "${LANGFUSE_HOST}/api/public/traces?limit=${LIMIT}" \
        -H "Authorization: Basic ${AUTH}" \
        -H "Content-Type: application/json")

    # Check for error
    if echo "$RESPONSE" | grep -q '"error"'; then
        echo "Error fetching traces: $RESPONSE"
        exit 1
    fi

    # Extract trace IDs using jq or grep/sed fallback
    if command -v jq &> /dev/null; then
        TRACE_IDS=$(echo "$RESPONSE" | jq -r '.data[].id // empty' 2>/dev/null)
        TOTAL=$(echo "$RESPONSE" | jq -r '.meta.totalItems // 0' 2>/dev/null)
    else
        # Fallback: extract IDs with grep/sed
        TRACE_IDS=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | sed 's/"id":"//g' | sed 's/"//g')
        TOTAL="unknown"
    fi

    # If no traces found, we're done
    if [ -z "$TRACE_IDS" ]; then
        echo "No more traces found."
        break
    fi

    TRACE_COUNT=$(echo "$TRACE_IDS" | wc -w | tr -d ' ')
    echo "Iteration $ITERATIONS/$MAX_ITERATIONS: Found $TRACE_COUNT traces (Total in system: $TOTAL)..."

    # Delete each trace
    for TRACE_ID in $TRACE_IDS; do
        echo "  Deleting trace: $TRACE_ID"
        DELETE_RESPONSE=$(curl -s -X DELETE \
            "${LANGFUSE_HOST}/api/public/traces/${TRACE_ID}" \
            -H "Authorization: Basic ${AUTH}" \
            -H "Content-Type: application/json")

        if echo "$DELETE_RESPONSE" | grep -q '"error"'; then
            echo "    Warning: Failed to delete trace $TRACE_ID: $DELETE_RESPONSE"
        else
            ((DELETED++))
        fi
    done

    # Wait a moment for ClickHouse to process deletions
    echo "  Waiting for deletions to propagate..."
    sleep 3

    # Check if traces are actually being deleted
    if [ $ITERATIONS -gt 1 ]; then
        NEW_RESPONSE=$(curl -s -X GET \
            "${LANGFUSE_HOST}/api/public/traces?limit=1" \
            -H "Authorization: Basic ${AUTH}" \
            -H "Content-Type: application/json")

        if command -v jq &> /dev/null; then
            NEW_TOTAL=$(echo "$NEW_RESPONSE" | jq -r '.meta.totalItems // 0' 2>/dev/null)
        else
            NEW_TOTAL="unknown"
        fi

        if [ "$NEW_TOTAL" = "$TOTAL" ] && [ "$TOTAL" != "0" ] && [ "$TOTAL" != "unknown" ]; then
            echo ""
            echo "WARNING: Traces are not being deleted from the database."
            echo "This usually means ClickHouse needs 'allow_nondeterministic_mutations' enabled."
            echo "Run: ./fix-clickhouse-mutations.sh"
            echo ""
            break
        fi
    fi
done

if [ $ITERATIONS -ge $MAX_ITERATIONS ]; then
    echo ""
    echo "Reached maximum iterations ($MAX_ITERATIONS). Some traces may remain."
fi

echo ""
echo "============================================================"
echo "Langfuse traces cleared!"
echo "Deleted $DELETED traces."
echo "============================================================"
