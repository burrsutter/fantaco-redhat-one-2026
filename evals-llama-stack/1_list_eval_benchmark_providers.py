#!/usr/bin/env python3
"""
List eval/benchmark providers from a Llama Stack server.
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

    # List all available providers
    logger.info("Fetching available providers...")
    providers = client.providers.list()

    if not providers:
        logger.warning("No providers found")
        return

    for p in providers:
        if p.api in ("eval", "benchmarks"):
            print(p.provider_id, p.provider_type)


if __name__ == "__main__":
    main()
