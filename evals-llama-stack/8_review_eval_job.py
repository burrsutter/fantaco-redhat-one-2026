#!/usr/bin/env python3
"""
Fetch an eval job result from a Llama Stack server and print scores.
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

    benchmark_id = os.getenv("LLAMA_STACK_BENCHMARK_ID", "my-basic-quality-benchmark")
    job_id = os.getenv("LLAMA_STACK_JOB_ID")
    if not job_id:
        logger.error("LLAMA_STACK_JOB_ID environment variable is not set")
        sys.exit(1)

    logger.info(f"Connecting to Llama Stack server at: {base_url}")
    logger.info(f"Fetching eval job result: benchmark={benchmark_id} job_id={job_id}")

    # Create the Llama Stack client
    client = LlamaStackClient(base_url=base_url)

    try:
        result = client.alpha.eval.jobs.retrieve(job_id, benchmark_id=benchmark_id)
    except Exception as exc:
        logger.error(f"Failed to fetch eval job result: {exc}")
        sys.exit(1)

    if not result:
        logger.warning("No result returned for this job")
        return

    
    if not result.scores:
        logger.warning("No scores returned for this job")
        return

    logger.info("Scores:")
    for scoring_fn_id, scoring_result in result.scores.items():
        print(f"  Scoring Function: {scoring_fn_id}")
        
        if scoring_result.aggregated_results:
            print(f"  Aggregated: {scoring_result.aggregated_results}")
        if scoring_result.score_rows:
            print(f"  Rows: {len(scoring_result.score_rows)}")
            for index, row in enumerate(scoring_result.score_rows, start=1):
                generation = None
                if result.generations and index - 1 < len(result.generations):
                    generation = result.generations[index - 1]
                if generation:
                    print(f"   Row {index}: {row} | Generation: {generation}")
                else:
                    print(f"   Row {index}: {row}")
        print()


if __name__ == "__main__":
    main()
