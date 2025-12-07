curl -sS $LLAMA_STACK_BASE_URL/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer fake" \
    -d "{
       \"model\": \"$INFERENCE_MODEL\",
       \"messages\": [{\"role\": \"user\", \"content\": \"what model are you?\"}],
       \"temperature\": 0.0
     }" | jq -r '.choices[0].message.content'