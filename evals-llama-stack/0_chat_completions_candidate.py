#!/usr/bin/env python3
"""
Simple chat completions example using the Llama Stack API.
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

    model = os.getenv("CANDIDATE_MODEL")
    if not model:
        logger.error("CANDIDATE_MODEL environment variable is not set")
        sys.exit(1)

    logger.info(f"Connecting to Llama Stack server at: {base_url}")
    logger.info(f"Using model: {model}")

    # Create the Llama Stack client
    client = LlamaStackClient(base_url=base_url)

    questions = [
        # "What color is the sky?",
        # "Who wrote Romeo and Juliet?",
        "Sally's mother has 4 children: Spring, Summer, Fall, and ____. What is the fourth child's name?",
        "A farmer has 17 sheep. All but 9 run away. How many sheep does the farmer have left?",
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?",
    ]

    try:
        for q in questions:
            logger.info(f"\nQuestion: {q}")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": q}],
                temperature=0.0,
            )

            # Extract the message content (equivalent to jq '.choices[0].message.content')
            content = response.choices[0].message.content
            print(content)

    except Exception as exc:
        logger.error(f"Failed to get chat completion: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
