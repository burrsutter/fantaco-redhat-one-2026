

## Starting the Llama Stack Server

```bash
ollama serve
```

Pull down your needed models

```bash
ollama pull llama3.2:3b
```

```bash
export LLAMA_STACK_MODEL="meta-llama/Llama-3.2-3B-Instruct"
export INFERENCE_MODEL="meta-llama/Llama-3.2-3B-Instruct"
export LLAMA_STACK_PORT=8321
export LLAMA_STACK_SERVER=http://localhost:$LLAMA_STACK_PORT
export LLAMA_STACK_ENDPOINT=$LLAMA_STACK_SERVER
export LLAMA_STACK_ENDPOINT_OPENAI=$LLAMA_STACK_ENDPOINT/v1/openai/v1
```

```bash
python3.13 -m venv .venv
source .venv/bin/activate

uv run python -v
```

Install Deps 

```bash
uv run --with llama-stack llama stack list-deps starter | xargs -L1 uv pip install
```

Run the Llama Stack server attaching itself to ollama


```bash
OLLAMA_URL=http://localhost:11434 uv run --with llama-stack llama stack run starter
```

```bash
cd llama-stack-scripts
```

### What models are registered with Llama Stack 

```bash
export LLAMA_STACK_BASE_URL=http://localhost:8321
export LLAMA_STACK_OPENAI_ENDPOINT=http://localhost:8321/v1
export INFERENCE_MODEL=ollama/llama3.2:3b
export API_KEY=fake
```

```bash
curl -sS $LLAMA_STACK_BASE_URL/v1/models -H "Content-Type: application/json" | jq -r '.data[].identifier'
```

### What are the APIs

```bash
curl -sS $LLAMA_STACK_BASE_URL/openapi.json | jq '.paths | keys'
```

### Test Chat Completions API

```bash
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

```bash
export QUESTION="What is the capital of France?"

curl -sS "$LLAMA_STACK_BASE_URL/v1/responses" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "{
      \"model\": \"$INFERENCE_MODEL\",
      \"input\": \"$QUESTION\"
    }" | jq -r '.output[0].content[0].text'
```

### What tools does Llama Stack have?

```bash
curl -sS -H "Content-Type: application/json" $LLAMA_STACK_BASE_URL/v1/toolgroups | jq
```

What MCP tools

```bash
curl -sS -H "Content-Type: application/json" $LLAMA_STACK_BASE_URL/v1/toolgroups | jq -r '.data[] | select(.identifier | endswith("mcp")) | .identifier'
```

```bash
curl -sS -H "Content-Type: application/json" $LLAMA_STACK_BASE_URL/v1/toolgroups | jq -r '.data[] | select(.provider_id == 
  "model-context-protocol") | .identifier'
```

## Start Customer Backend

Assumes Postgres is up and running with appropriate database pre-created.  See the deeper dive README.MD

```bash
cd fantaco-customer-main
open README.md
```

Run the Customer REST API

```bash
java -jar target/fantaco-customer-main-1.0.0.jar
```

### Quick test of Customer REST API

```bash
curl -sS -L "$CUST_URL/api/customers?companyName=Around" | jq
```

## Start Finance Backend

```bash
cd fantaco-finance-main
open README.md
```

Run the Finance REST API

```bash
java -jar target/fantaco-finance-main-1.0.0.jar
```

### Quick test for Finance REST API

```bash
curl -sS -X POST $FIN_URL/api/finance/orders/history \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "AROUT",
    "limit": 10
  }' | jq
```

## Customer MCP

```bash
cd fantaco-mcp-servers/customer-mcp
```

```bash
python customer-api-mcp-server.py
```

## Finance MCP

```bash
cd fantaco-mcp-servers/finance-mcp
```

```bash
python finance-api-mcp-server.py
```

Using `mcp-inspector` to test

