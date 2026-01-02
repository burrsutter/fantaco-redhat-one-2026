"""
Dataset module for evaluation.
Handles loading local test cases and syncing to Langfuse datasets.
"""

import csv
import logging
from typing import Dict, Any, List

from langfuse import get_client

logger = logging.getLogger(__name__)

# Dataset metadata (since CSV doesn't have a header for these)
DATASET_NAME = "customer-service-eval"
DATASET_DESCRIPTION = "Evaluation dataset for customer service chatbot"
DATASET_VERSION = "1.0.0"


def load_local_test_cases(file_path: str) -> Dict[str, Any]:
    """
    Load test cases from local CSV file.

    Args:
        file_path: Path to the CSV file containing test cases

    Returns:
        Dict containing dataset metadata and test cases
    """
    test_cases = []

    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse keywords from comma-separated string
            keywords = [k.strip() for k in row['expected_keywords'].split(',')]

            test_case = {
                "id": row['id'],
                "name": row['name'],
                "input": {
                    "message": row['input_message']
                },
                "expected_output": {
                    "keywords": keywords,
                    "match_mode": row.get('match_mode', 'all')
                },
                "metadata": {
                    "category": row.get('category', ''),
                    "difficulty": row.get('difficulty', '')
                }
            }
            test_cases.append(test_case)

    return {
        "dataset_name": DATASET_NAME,
        "description": DATASET_DESCRIPTION,
        "version": DATASET_VERSION,
        "test_cases": test_cases
    }


def sync_to_langfuse(
    test_cases_path: str,
    force_recreate: bool = False
) -> Dict[str, Any]:
    """
    Sync local test cases to Langfuse dataset.

    Args:
        test_cases_path: Path to local JSON file
        force_recreate: If True, attempts to recreate items

    Returns:
        Dict with sync results
    """
    langfuse = get_client()
    data = load_local_test_cases(test_cases_path)

    dataset_name = data["dataset_name"]
    description = data.get("description", "Evaluation dataset")
    version = data.get("version", "1.0.0")
    test_cases = data["test_cases"]

    # Create or get dataset
    try:
        langfuse.create_dataset(
            name=dataset_name,
            description=f"{description} (v{version})",
            metadata={"version": version, "synced_from": "local_csv"}
        )
        logger.info(f"Created dataset: {dataset_name}")
    except Exception as e:
        # Dataset may already exist, which is fine
        logger.info(f"Dataset {dataset_name} may already exist: {e}")

    # Upload each test case as a dataset item
    items_created = 0
    for test_case in test_cases:
        try:
            langfuse.create_dataset_item(
                dataset_name=dataset_name,
                input=test_case["input"],
                expected_output=test_case["expected_output"],
                metadata={
                    "id": test_case["id"],
                    "name": test_case["name"],
                    **test_case.get("metadata", {})
                }
            )
            items_created += 1
            logger.debug(f"Created dataset item: {test_case['id']}")
        except Exception as e:
            logger.warning(f"Failed to create item {test_case['id']}: {e}")

    langfuse.flush()

    return {
        "dataset_name": dataset_name,
        "items_synced": items_created,
        "total_items": len(test_cases),
        "version": version
    }


def get_dataset_items(dataset_name: str) -> List[Any]:
    """
    Fetch all items from a Langfuse dataset.

    Args:
        dataset_name: Name of the dataset

    Returns:
        List of dataset items
    """
    langfuse = get_client()
    dataset = langfuse.get_dataset(dataset_name)
    return dataset.items
