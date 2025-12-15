#!/bin/bash

# Get base URL from environment or use default
LLAMA_STACK_BASE_URL=${LLAMA_STACK_BASE_URL:-http://localhost:8321}

# List all vector stores
echo "Fetching vector stores from: $LLAMA_STACK_BASE_URL"
echo "----------------------------------------"

#curl -s "$LLAMA_STACK_BASE_URL/v1/vector_stores" \
#  -H "Content-Type: application/json" | jq '.'


curl -sS $LLAMA_STACK_BASE_URL/v1/vector_stores | jq -r '.data[] | "\(.name) \(.id)"'