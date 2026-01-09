# Llama Stack Workshop Materials

![Architecture Diagram](./simple-agent-langgraph/architecture_diagram.png)

## Starting the model server 

For localhost development, use [Ollama](https://ollama.com/) or you can use a remote model server such as vLLM via Model-as-a-Service solution [MaaS](https://maas.apps.prod.rhoai.rh-aiservices-bu.com/admin/applications)
s

```bash
ollama serve
```

Pull down your needed models.  For LLM tool invocations you ofte need a larger model such as Qwen 14B.  The way you know is to test your app/agent + model + model-server-configuration.

```bash
ollama pull llama3.2:3b
ollama pull qwen3:14b-q8_0
```

```bash
cd llama-stack-scripts
```


```bash
export LLAMA_STACK_BASE_URL=http://localhost:8321
export INFERENCE_MODEL=ollama/llama3.2:3b
# export INFERENCE_MODEL=vllm/llama-4-scout-17b-16e-w4a16
export LLAMA_STACK_LOG_FILE=logs/llama-stack-server.log
export LLAMA_STACK_LOGGING="tools=DEBUG,tool_runtime=DEBUG,providers=DEBUG,server=info"
```

If using Ollama

```bash
export OLLAMA_URL=http://localhost:11434 
```


If using [MaaS](https://maas.apps.prod.rhoai.rh-aiservices-bu.com/admin/applications)

```bash
export VLLM_API_TOKEN=blah

export VLLM_URL=https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1
```


```bash
python3.12 -m venv .venv
source .venv/bin/activate

uv run python -V
```

Install Dependencies 

```bash
uv run --with llama-stack llama stack list-deps starter | xargs -L1 uv pip install
```

Run the Llama Stack server attaching itself to ollama


```bash
uv run --with llama-stack llama stack run starter
```

Inspect the server by running the scripts in `llama-stack-scripts`

Note: Llama Stack persists state to `~/.llama/` 
specifically `~/.llama/distributions/starter` when using the `run starter` command above.   If you want a clean start:

```bash
rm -rf ~/.llama/distributions/starter
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
source .venv/bin/activate
```

```bash
python customer-api-mcp-server.py
```

## Finance MCP

```bash
cd fantaco-mcp-servers/finance-mcp
source .venv/bin/activate
```

```bash
python finance-api-mcp-server.py
```

Using `mcp-inspector` to test the MCP Servers

## Agents with Llama Stack

The `agents-llama-stack/` directory contains numbered example scripts that demonstrate progressive agent capabilities. **Run these scripts in order 1 through 6** to learn the concepts step-by-step:

1. `1_hello_world_agent_no_stream.py` - Basic agent without streaming
2. `1_hello_world_agent_streaming.py` - Basic agent with streaming
3. `3_list_customer_tools.py` / `3_list_finance_tools.py` - List available MCP tools
4. `4_agent_customer_mcp.py` / `4_agent_finance_mcp.py` - Single-domain agents
5. `5_agent_customer_and_finance.py` - Multi-domain agent
6. `6_multi_turn_agent.py` - Multi-turn conversational agent

```bash
cd agents-llama-stack
source .venv/bin/activate
python 1_hello_world_agent_no_stream.py
# Continue with 2, 3, 4, 5, 6...
```

## Simple Agent LangGraph

Follow the `REAME.md` in `simple-agent-langgraph`

