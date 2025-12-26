#!/usr/bin/env python3
"""
Register datasets/basic-equality-evals.csv with a Llama Stack server.
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
DEFAULT_DATASET_URL = (
    "https://raw.githubusercontent.com/burrsutter/fantaco-redhat-one-2026/main/"
    "evals-llama-stack/datasets/basic-equality-evals.csv"
)


def main():
    # Load environment variables from .env file
    load_dotenv()

    base_url = os.getenv("LLAMA_STACK_BASE_URL")
    if not base_url:
        logger.error("LLAMA_STACK_BASE_URL environment variable is not set")
        sys.exit(1)


    dataset_url = os.getenv("LLAMA_STACK_DATASET_URL", DEFAULT_DATASET_URL)
    if not dataset_url:
        logger.error("LLAMA_STACK_DATASET_URL environment variable is not set")
        sys.exit(1)

    provider_id = os.getenv("LLAMA_STACK_DATASET_PROVIDER_ID", "localfs")

    logger.info(f"Connecting to Llama Stack server at: {base_url}")
    logger.info(f"Registering dataset: {DATASET_ID}")
    logger.info(f"Using dataset provider: {provider_id}")

    # Create the Llama Stack client
    client = LlamaStackClient(base_url=base_url)

    try:
        dataset = client.datasets.register(
            purpose="eval/question-answer",
            source={
                "type": "uri",
                "uri": dataset_url,
            },
            dataset_id=DATASET_ID,
            extra_body={"provider_id": provider_id},
        )
    except Exception as exc:
        logger.error(f"Failed to register dataset: {exc}")
        sys.exit(1)

    if dataset is None:
        logger.warning("No dataset returned from registration")
        return

    identifier = getattr(dataset, "identifier", DATASET_ID)
    logger.info(f"Registered dataset: {identifier}")


if __name__ == "__main__":
    main()
