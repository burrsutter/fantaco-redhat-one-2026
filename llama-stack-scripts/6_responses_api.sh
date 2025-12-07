export QUESTION="What is the capital of France?"

curl -sS "$LLAMA_STACK_BASE_URL/v1/responses" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
      \"model\": \"$INFERENCE_MODEL\",
      \"input\": \"$QUESTION\"
    }" | jq -r '.output[0].content[0].text'