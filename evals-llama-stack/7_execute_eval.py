#!/usr/bin/env python3
"""
Run an eval job on a benchmark with a Llama Stack server.
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

    model_id = os.getenv("INFERENCE_MODEL")
    if not model_id:
        logger.error("INFERENCE_MODEL environment variable is not set")
        sys.exit(1)

    benchmark_id = os.getenv("LLAMA_STACK_BENCHMARK_ID", "my-basic-quality-benchmark")

    logger.info(f"Connecting to Llama Stack server at: {base_url}")    
    logger.info(f"Running eval for benchmark: {benchmark_id}")
    logger.info(f"Using candidate model: {model_id}")

    # Create the Llama Stack client
    client = LlamaStackClient(base_url=base_url)

    benchmark_config = {
        "eval_candidate": {
            "type": "model",
            "model": model_id,
            "sampling_params": {
                "strategy": {"type": "greedy"},
                "max_tokens": 64,
            },
        },
        "scoring_params": {
            "basic::subset_of": {
                "type": "basic",
                "aggregation_functions": ["accuracy"],
            },
        },
    }

    try:
        job = client.alpha.eval.run_eval(
            benchmark_id,
            benchmark_config=benchmark_config,
        )
    except Exception as exc:
        logger.error(f"Failed to run eval: {exc}")
        sys.exit(1)

    job_id = getattr(job, "job_id", None)
    if job_id:
        logger.info(f"Eval job started: {job_id}")
    else:
        logger.info("Eval job started")


if __name__ == "__main__":
    main()
