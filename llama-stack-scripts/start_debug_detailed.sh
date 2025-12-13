#!/bin/bash

# Enable DEBUG logging for specific categories to see tool calls, messages, and responses
# Available categories: core, server, router, inference, agents, safety, eval, tools,
# client, openai, openai_responses, openai_conversations, testing, providers, models,
# files, vector_io, tool_runtime, cli, post_training, scoring

export LLAMA_STACK_LOGGING="core=DEBUG,inference=DEBUG,agents=DEBUG,tools=DEBUG,providers=DEBUG,tool_runtime=DEBUG"

# Enable file logging
export LLAMA_STACK_LOG_FILE="logs/llama-stack-server.log"

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting Llama Stack with detailed DEBUG logging..."
echo "Logging categories enabled:"
echo "  - core: Core operations (DEBUG)"
echo "  - inference: Chat completions and messages (DEBUG)"
echo "  - agents: Agent operations (DEBUG)"
echo "  - tools: MCP tool operations (DEBUG)"
echo "  - providers: Provider operations (DEBUG)"
echo "  - tool_runtime: Tool execution (DEBUG)"
echo ""
echo "Logs will be written to: logs/llama-stack-server.log"
echo "Press Ctrl+C to stop"
echo ""

# Start the server
uv run --with llama-stack llama stack run starter
