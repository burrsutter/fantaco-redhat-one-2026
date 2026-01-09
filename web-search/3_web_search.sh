#!/bin/bash

# Set defaults
LLAMA_STACK_BASE_URL="${LLAMA_STACK_BASE_URL:-http://localhost:8321}"
INFERENCE_MODEL="${INFERENCE_MODEL:-vllm/qwen3-14b}"
API_KEY="${API_KEY:-not-applicable}"
QUESTION="${QUESTION:-Who won the last Super Bowl?}"

# Display configuration
echo "Base URL:   $LLAMA_STACK_BASE_URL"
echo "Model:      $INFERENCE_MODEL"
echo "API Key:    $API_KEY"
if [ -n "$TAVILY_SEARCH_API_KEY" ]; then
    echo "Tavily Key: Set"
else
    echo "Tavily Key: NOT SET (web search will fail)"
fi
echo ""
echo "Question:   $QUESTION"
echo ""

# Make the API call
cat << EOF | curl -sS "$LLAMA_STACK_BASE_URL/v1/responses" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -H "X-LlamaStack-Provider-Data: {\"tavily_search_api_key\": \"$TAVILY_SEARCH_API_KEY\"}" \
    -d @- | jq -r '.output[] | select(.type == "message") | .content[0].text'
{
  "model": "$INFERENCE_MODEL",
  "input": "$QUESTION",
  "tools": [{"type": "web_search"}],
  "stream": false
}
EOF

echo ""
