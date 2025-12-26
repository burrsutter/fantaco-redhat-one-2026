#!/usr/bin/env python3
"""
Register a benchmark with a Llama Stack server.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient, NotFoundError

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

    provider_id = os.getenv("LLAMA_STACK_BENCHMARK_PROVIDER_ID")
    if provider_id:
        logger.info(f"Using benchmark provider: {provider_id}")

    logger.info("Registering benchmark: my-basic-quality-benchmark")

    try:
        client.benchmarks.register(
            benchmark_id="my-basic-quality-benchmark",
            dataset_id="basic-equality-evals",
            scoring_functions=["basic::equality"]
        )
    except NotFoundError as exc:
        logger.error(f"Failed to register benchmark: {exc}")
        logger.error("Benchmark API not found. Enable the eval API in your Llama Stack run.yaml and restart.")
        sys.exit(1)
    except Exception as exc:
        logger.error(f"Failed to register benchmark: {exc}")
        sys.exit(1)

    logger.info("Benchmark registered successfully")


if __name__ == "__main__":
    main()
