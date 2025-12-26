#!/usr/bin/env python3
"""
List all available models from a Llama Stack server.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("llama_stack_client").setLevel(logging.WARNING)

def main():
    # Load environment variables from .env file
    load_dotenv()

    base_url = os.getenv("LLAMA_STACK_BASE_URL")
    if not base_url:
        logger.error("LLAMA_STACK_BASE_URL environment variable is not set")
        sys.exit(1)

    logger.info(f"Connecting to Llama Stack server at: {base_url}")

    # Create the Llama Stack client
    client = LlamaStackClient(base_url=base_url)

    # List all available models
    logger.info("Fetching available models...")
    models = client.models.list()

    if not models:
        logger.warning("No models found")
        return

    logger.info(f"Found {len(models)} model(s):\n")

    for model in models:
        print(f"  Model ID: {model.identifier}")
        print(f"    Type: {model.model_type}")
        print(f"    Provider: {model.provider_id}")
        if hasattr(model, 'metadata') and model.metadata:
            print(f"    Metadata: {model.metadata}")
        print()

if __name__ == "__main__":
    main()
