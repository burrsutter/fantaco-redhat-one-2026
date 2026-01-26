#!/bin/bash
# Execute evaluations from evals.csv and compare responses
# This script must be run from within Claude Code so that Claude can evaluate
# the flow's current answer versus the golden answer in the CSV.
# Claude Code is the judge - it will semantically compare the answers.
#
# Requires: LANGFLOW_API_URL, LANGFLOW_API_KEY, LANGFLOW_FLOW_ID (or uses most recent flow)

set -e

echo "========================================"
echo "LANGFLOW EVALUATION RUNNER"
echo "========================================"
echo ""
echo "IMPORTANT: This script must be run from within Claude Code!"
echo "Claude Code will act as the judge to semantically compare"
echo "the flow's current answers against the golden answers in evals.csv"
echo ""
echo "========================================"

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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_FILE="$SCRIPT_DIR/evals.csv"

if [ ! -f "$EVALS_FILE" ]; then
    echo "Error: evals.csv not found at $EVALS_FILE"
    exit 1
fi

# Determine flow ID
if [ -n "$LANGFLOW_FLOW_ID" ]; then
    FLOW_ID="$LANGFLOW_FLOW_ID"
    echo "Using provided flow ID: $FLOW_ID"
else
    echo "LANGFLOW_FLOW_ID not set, fetching most recent flow..."
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
echo "API URL: $LANGFLOW_API_URL"
echo "Flow ID: $FLOW_ID"
echo ""

# Read and process evals.csv (skip header line)
EVAL_NUM=0
TOTAL_EVALS=$(tail -n +2 "$EVALS_FILE" | wc -l | tr -d ' ')

echo "Found $TOTAL_EVALS evaluations to run"
echo ""

# Process each line (handling CSV with quoted fields)
tail -n +2 "$EVALS_FILE" | while IFS= read -r line; do
    EVAL_NUM=$((EVAL_NUM + 1))

    # Parse CSV line - extract question (first quoted field) and expected answer (second quoted field)
    QUESTION=$(echo "$line" | sed 's/^"\([^"]*\)".*/\1/')
    EXPECTED=$(echo "$line" | sed 's/^"[^"]*","\(.*\)"$/\1/')

    echo "========================================"
    echo "EVALUATION $EVAL_NUM of $TOTAL_EVALS"
    echo "========================================"
    echo ""
    echo "QUESTION: $QUESTION"
    echo ""

    # Execute the query
    RESPONSE=$(curl -sL --compressed -X POST \
        -H "x-api-key:$LANGFLOW_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"input_value\": \"$QUESTION\"}" \
        "$LANGFLOW_API_URL/api/v1/run/$FLOW_ID")

    # Check for API error
    if echo "$RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
        ACTUAL="ERROR: $(echo "$RESPONSE" | jq -r '.detail')"
    else
        ACTUAL=$(echo "$RESPONSE" | jq -r '.outputs[0].outputs[0].results.message.text // .outputs[0].outputs[0].messages[0].message // "No output found"')
    fi

    echo "EXPECTED ANSWER (from evals.csv):"
    echo "----------------------------------------"
    echo "$EXPECTED"
    echo "----------------------------------------"
    echo ""
    echo "ACTUAL ANSWER (from flow):"
    echo "----------------------------------------"
    echo "$ACTUAL"
    echo "----------------------------------------"
    echo ""
    echo "CLAUDE CODE: Please evaluate if the ACTUAL answer is semantically"
    echo "equivalent to the EXPECTED answer. Key data points should match."
    echo ""

done

echo "========================================"
echo "ALL EVALUATIONS COMPLETE"
echo "========================================"
echo ""
echo "Claude Code should now provide a summary judgment:"
echo "- How many evaluations passed (semantically equivalent)?"
echo "- How many evaluations failed (missing or incorrect data)?"
echo "- Any notable discrepancies?"
