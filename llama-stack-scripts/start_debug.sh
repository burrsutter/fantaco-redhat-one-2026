#!/bin/bash
export LLAMA_STACK_LOGGING="all=DEBUG"
export LLAMA_STACK_LOG_FILE="logs/llama-stack-server.log"
mkdir -p logs
uv run --with llama-stack llama stack run starter
