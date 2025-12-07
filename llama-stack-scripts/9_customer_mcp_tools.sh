curl -sS -H "Content-Type: application/json" \
  "$LLAMA_STACK_BASE_URL/v1/tool-runtime/list-tools?tool_group_id=customer_mcp" | jq -r '.data[].name'
