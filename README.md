# Starting the Llama Stack Server


```
ollama serve
```

```
ollama run llama3.2:3b --keepalive 60m
```

```
export LLAMA_STACK_MODEL="meta-llama/Llama-3.2-3B-Instruct"
export INFERENCE_MODEL="meta-llama/Llama-3.2-3B-Instruct"
export LLAMA_STACK_PORT=8321
export LLAMA_STACK_SERVER=http://localhost:$LLAMA_STACK_PORT
export LLAMA_STACK_ENDPOINT=$LLAMA_STACK_SERVER
export LLAMA_STACK_ENDPOINT_OPENAI=$LLAMA_STACK_ENDPOINT/v1/openai/v1
```

```
brew install podman
```

```
podman machine start
```

### Start the Llama Stack Server

```
python3.13 -m venv .venv
source .venv/bin/activate

uv run python -v
```

```
uv run --with llama-stack llama stack list-deps starter | xargs -L1 uv pip install
```

```
OLLAMA_URL=http://localhost:11434 uv run --with llama-stack llama stack run starter
```


### What models are registered with Llama Stack 

```
export LLAMA_STACK_BASE_URL=http://localhost:8321
export LLAMA_STACK_OPENAI_ENDPOINT=http://localhost:8321/v1
export INFERENCE_MODEL=ollama/llama3.2:3b
export API_KEY=fake
export QUESTION="What is the capital of France?"
```

```
curl -sS $LLAMA_STACK_BASE_URL/v1/models -H "Content-Type: application/json" | jq -r '.data[].identifier'
```

### What are the APIs

```
curl $LLAMA_STACK_BASE_URL/openapi.json | jq '.paths | keys'
```

### Test Chat Completions API

```
curl -sS $LLAMA_STACK_BASE_URL/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer fake" \
    -d '{
       "model": "ollama/llama3.2:3b",
       "messages": [{"role": "user", "content": "what model are you?"}],
       "temperature": 0.0
     }' | jq -r '.choices[0].message.content'
```   

### Test the Responses API

```
curl -sS "$LLAMA_STACK_BASE_URL/v1/responses" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
      \"model\": \"$INFERENCE_MODEL\",
      \"input\": \"$QUESTION\"
    }" | jq -r '.output[0].content[0].text'
```