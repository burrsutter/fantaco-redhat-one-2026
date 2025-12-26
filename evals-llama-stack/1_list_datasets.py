#!/usr/bin/env python3
"""
List all available datasets from a Llama Stack server.
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

    # List all available datasets
    logger.info("Fetching available datasets...")
    datasets = client.datasets.list()

    if not datasets:
        logger.warning("No datasets found")
        return

    logger.info(f"Found {len(datasets)} dataset(s):\n")

    for dataset in datasets:
        print(f"  Dataset ID: {dataset.identifier}")
        if hasattr(dataset, 'provider_id') and dataset.provider_id:
            print(f"    Provider: {dataset.provider_id}")
        if hasattr(dataset, 'source') and dataset.source:
            print(f"    Source: {dataset.source.uri if hasattr(dataset.source, 'uri') else dataset.source}")
        if hasattr(dataset, 'metadata') and dataset.metadata:
            description = dataset.metadata.get('description', '')
            if description:
                print(f"    Description: {description}")
        print()

if __name__ == "__main__":
    main()
