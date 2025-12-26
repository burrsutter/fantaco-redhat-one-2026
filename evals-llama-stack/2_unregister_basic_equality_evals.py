#!/usr/bin/env python3
"""
Unregister the basic-equality-evals dataset from a Llama Stack server.
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

DATASET_ID = "basic-equality-evals"


def main():
    # Load environment variables from .env file
    load_dotenv()

    base_url = os.getenv("LLAMA_STACK_BASE_URL")
    if not base_url:
        logger.error("LLAMA_STACK_BASE_URL environment variable is not set")
        sys.exit(1)

    logger.info(f"Connecting to Llama Stack server at: {base_url}")
    logger.info(f"Unregistering dataset: {DATASET_ID}")

    # Create the Llama Stack client
    client = LlamaStackClient(base_url=base_url)

    try:
        client.datasets.unregister(DATASET_ID)
    except Exception as exc:
        logger.error(f"Failed to unregister dataset: {exc}")
        sys.exit(1)

    logger.info("Dataset unregistered successfully")


if __name__ == "__main__":
    main()
