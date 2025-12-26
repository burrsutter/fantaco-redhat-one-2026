#!/usr/bin/env python3
"""
List all available benchmarks from a Llama Stack server.
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

    logger.info("Fetching available benchmarks...")
    benchmarks = client.benchmarks.list()

    if not benchmarks:
        logger.warning("No benchmarks found")
        return

    logger.info(f"Found {len(benchmarks)} benchmark(s):\n")

    for benchmark in benchmarks:
        print(f"  Benchmark ID: {benchmark.identifier}")
        if hasattr(benchmark, 'dataset_id') and benchmark.dataset_id:
            print(f"    Dataset: {benchmark.dataset_id}")
        if hasattr(benchmark, 'scoring_functions') and benchmark.scoring_functions:
            print(f"    Scoring Functions: {benchmark.scoring_functions}")
        if hasattr(benchmark, 'provider_id') and benchmark.provider_id:
            print(f"    Provider: {benchmark.provider_id}")
        print()


if __name__ == "__main__":
    main()
