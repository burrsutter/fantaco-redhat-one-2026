echo "LLAMA_STACK_BASE_URL: ${LLAMA_STACK_BASE_URL}"
echo "LLAMA_STACK_API_KEY: ${LLAMA_STACK_API_KEY}"

curl -w "\nHTTP Status: %{http_code}\n" -X DELETE "${LLAMA_STACK_BASE_URL}/v1/toolgroups/customer_mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${LLAMA_STACK_API_KEY}"
