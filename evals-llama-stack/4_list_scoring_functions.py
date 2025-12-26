#!/usr/bin/env python3
"""
List all available scoring functions from a Llama Stack server.
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

    # List all available scoring functions
    logger.info("Fetching available scoring functions...")
    scoring_functions = client.scoring_functions.list()

    if not scoring_functions:
        logger.warning("No scoring functions found")
        return

    logger.info(f"Found {len(scoring_functions)} scoring function(s):\n")

    for scoring_function in scoring_functions:
        print(f"  Scoring Function ID: {scoring_function.identifier}")
        if hasattr(scoring_function, 'provider_id') and scoring_function.provider_id:
            print(f"    Provider: {scoring_function.provider_id}")
        if hasattr(scoring_function, 'description') and scoring_function.description:
            print(f"    Description: {scoring_function.description}")
        print()


if __name__ == "__main__":
    main()
