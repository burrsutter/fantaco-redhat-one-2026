#!/usr/bin/env python3
"""
Load test script for the FastAPI LangGraph API.
"""

import requests
import time
import concurrent.futures
import argparse
import statistics
import os
from urllib.parse import urlencode

# Default configuration
SERVICE_URL = os.getenv("SERVICE_URL", "langgraph-fastapi")
DEFAULT_BASE_URL = f"http://{SERVICE_URL}:8001"
DEFAULT_CONCURRENT_USERS = 3
DEFAULT_ITERATIONS = 1

# Test queries based on the curl commands
QUERIES = [
    "list invoices for Thomas Hardy?",
    "find orders for thomashardy@example.com?",
    "get me invoices for Liu Wong?",
    "fetch orders for liuwong@example.com?",
    "fetch invoices for Fran Wilson?",
    "fetch orders for franwilson@example.com?",
]


def make_request(base_url: str, query: str) -> dict:
    """Make a single request to the /question endpoint."""
    url = f"{base_url}/question"
    params = {"q": query}

    start_time = time.time()
    try:
        response = requests.get(url, params=params, timeout=120)
        elapsed = time.time() - start_time

        return {
            "query": query,
            "status_code": response.status_code,
            "elapsed": elapsed,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text,
            "error": None
        }
    except requests.exceptions.RequestException as e:
        elapsed = time.time() - start_time
        return {
            "query": query,
            "status_code": None,
            "elapsed": elapsed,
            "success": False,
            "response": None,
            "error": str(e)
        }


def run_sequential_test(base_url: str, queries: list) -> list:
    """Run queries sequentially."""
    results = []
    for query in queries:
        print(f"  Sending: {query[:50]}...")
        result = make_request(base_url, query)
        status = "✓" if result["success"] else "✗"
        print(f"  {status} {result['elapsed']:.2f}s - Status: {result['status_code']}")
        results.append(result)
    return results


def run_concurrent_test(base_url: str, queries: list, max_workers: int) -> list:
    """Run queries concurrently."""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_query = {
            executor.submit(make_request, base_url, query): query
            for query in queries
        }

        for future in concurrent.futures.as_completed(future_to_query):
            query = future_to_query[future]
            try:
                result = future.result()
                status = "✓" if result["success"] else "✗"
                print(f"  {status} {result['elapsed']:.2f}s - {query[:40]}...")
                results.append(result)
            except Exception as e:
                print(f"  ✗ Error: {e}")
                results.append({
                    "query": query,
                    "status_code": None,
                    "elapsed": 0,
                    "success": False,
                    "response": None,
                    "error": str(e)
                })
    return results


def print_summary(results: list, total_time: float):
    """Print test summary statistics."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"Total requests:     {len(results)}")
    print(f"Successful:         {len(successful)}")
    print(f"Failed:             {len(failed)}")
    print(f"Total time:         {total_time:.2f}s")

    if successful:
        times = [r["elapsed"] for r in successful]
        print(f"\nResponse times (successful requests):")
        print(f"  Min:              {min(times):.2f}s")
        print(f"  Max:              {max(times):.2f}s")
        print(f"  Average:          {statistics.mean(times):.2f}s")
        if len(times) > 1:
            print(f"  Std Dev:          {statistics.stdev(times):.2f}s")
        print(f"  Requests/sec:     {len(successful) / total_time:.2f}")

    if failed:
        print(f"\nFailed requests:")
        for r in failed:
            print(f"  - {r['query'][:50]}...")
            if r["error"]:
                print(f"    Error: {r['error']}")


def main():
    parser = argparse.ArgumentParser(description="Load test the FastAPI LangGraph API")
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL of the API (default: {DEFAULT_BASE_URL}, uses SERVICE_URL env var)"
    )
    parser.add_argument(
        "--concurrent", "-c",
        type=int,
        default=DEFAULT_CONCURRENT_USERS,
        help=f"Number of concurrent requests (default: {DEFAULT_CONCURRENT_USERS})"
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Number of iterations to run all queries (default: {DEFAULT_ITERATIONS})"
    )
    parser.add_argument(
        "--sequential", "-s",
        action="store_true",
        help="Run requests sequentially instead of concurrently"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full response content"
    )

    args = parser.parse_args()

    # Build query list based on iterations
    all_queries = QUERIES * args.iterations

    print("=" * 60)
    print("LOAD TEST - FastAPI LangGraph API")
    print("=" * 60)
    print(f"Target URL:         {args.url}")
    print(f"Total queries:      {len(all_queries)}")
    print(f"Iterations:         {args.iterations}")
    print(f"Mode:               {'Sequential' if args.sequential else f'Concurrent ({args.concurrent} workers)'}")
    print("=" * 60)
    print()

    # Check if server is reachable
    print("Checking server connectivity...")
    try:
        response = requests.get(f"{args.url}/", timeout=5)
        print(f"Server is up! Status: {response.status_code}\n")
    except requests.exceptions.RequestException as e:
        print(f"Error: Cannot connect to server at {args.url}")
        print(f"Details: {e}")
        return 1

    # Run the test
    print("Starting load test...\n")
    start_time = time.time()

    if args.sequential:
        results = run_sequential_test(args.url, all_queries)
    else:
        results = run_concurrent_test(args.url, all_queries, args.concurrent)

    total_time = time.time() - start_time

    # Show verbose output if requested
    if args.verbose:
        print("\n" + "-" * 60)
        print("DETAILED RESPONSES")
        print("-" * 60)
        for r in results:
            print(f"\nQuery: {r['query']}")
            print(f"Status: {r['status_code']}, Time: {r['elapsed']:.2f}s")
            if r['response']:
                print(f"Response: {r['response']}")

    # Print summary
    print_summary(results, total_time)

    return 0 if all(r["success"] for r in results) else 1


if __name__ == "__main__":
    exit(main())
