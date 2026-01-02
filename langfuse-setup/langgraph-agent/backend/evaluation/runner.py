"""
Evaluation runner module.
Executes test cases against the chatbot and records results to Langfuse.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict

from langfuse import get_client

from .scorer import substring_score, ScoreResult
from .dataset import load_local_test_cases

logger = logging.getLogger(__name__)


@dataclass
class TestCaseResult:
    """Result for a single test case"""
    test_id: str
    test_name: str
    passed: bool
    score: float
    response: str
    trace_id: Optional[str]
    matched_keywords: List[str]
    missing_keywords: List[str]
    details: str
    duration_ms: float


@dataclass
class EvaluationResult:
    """Overall evaluation results"""
    run_name: str
    timestamp: str
    dataset_name: str
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    average_score: float
    duration_ms: float
    results: List[TestCaseResult]


async def run_evaluation(
    test_cases_path: str,
    process_chat_fn: Callable[[str, Optional[str], Optional[str]], Awaitable[tuple]],
    run_name: Optional[str] = None,
    record_to_langfuse: bool = True
) -> EvaluationResult:
    """
    Run evaluation against all test cases.

    Args:
        test_cases_path: Path to local JSON test cases file
        process_chat_fn: The async function to call for each test (process_chat)
        run_name: Optional name for this evaluation run
        record_to_langfuse: Whether to record results to Langfuse dataset

    Returns:
        EvaluationResult with all test results
    """
    start_time = time.time()

    # Load test cases from local file
    data = load_local_test_cases(test_cases_path)
    dataset_name = data["dataset_name"]
    test_cases = data["test_cases"]

    # Generate run name if not provided
    if not run_name:
        run_name = f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    langfuse = get_client() if record_to_langfuse else None

    results: List[TestCaseResult] = []

    for test_case in test_cases:
        test_start = time.time()
        test_id = test_case["id"]
        test_name = test_case["name"]
        input_message = test_case["input"]["message"]
        expected = test_case["expected_output"]
        keywords = expected.get("keywords", [])
        match_mode = expected.get("match_mode", "all")

        logger.info(f"Running test: {test_name} ({test_id})")

        try:
            # Execute the chat function
            response, trace_id = await process_chat_fn(
                input_message,
                f"eval-session-{test_id}",
                "evaluation-runner"
            )

            # Score the response
            score_result = substring_score(
                response=response,
                keywords=keywords,
                match_mode=match_mode,
                case_sensitive=False
            )

            # Record score to Langfuse trace if we have a trace_id
            if langfuse and record_to_langfuse and trace_id:
                try:
                    langfuse.create_score(
                        trace_id=trace_id,
                        name="substring_match",
                        value=score_result.score,
                        comment=score_result.details
                    )
                    langfuse.create_score(
                        trace_id=trace_id,
                        name="pass_fail",
                        value=1.0 if score_result.passed else 0.0,
                        comment="Test passed" if score_result.passed else "Test failed"
                    )
                    logger.info(f"Recorded scores for trace {trace_id}")
                except Exception as e:
                    logger.warning(f"Failed to record scores to Langfuse: {e}")

            test_duration = (time.time() - test_start) * 1000

            # Truncate response if too long
            display_response = response[:500] + "..." if len(response) > 500 else response

            result = TestCaseResult(
                test_id=test_id,
                test_name=test_name,
                passed=score_result.passed,
                score=score_result.score,
                response=display_response,
                trace_id=trace_id,
                matched_keywords=score_result.matched_keywords,
                missing_keywords=score_result.missing_keywords,
                details=score_result.details,
                duration_ms=test_duration
            )

            status = "PASSED" if score_result.passed else "FAILED"
            logger.info(f"  {status}: {score_result.details}")

        except Exception as e:
            logger.error(f"Test {test_id} failed with error: {e}")
            test_duration = (time.time() - test_start) * 1000
            result = TestCaseResult(
                test_id=test_id,
                test_name=test_name,
                passed=False,
                score=0.0,
                response=f"ERROR: {str(e)}",
                trace_id=None,
                matched_keywords=[],
                missing_keywords=keywords,
                details=f"Execution error: {str(e)}",
                duration_ms=test_duration
            )

        results.append(result)

    # Flush Langfuse to ensure all data is sent
    if langfuse:
        langfuse.flush()

    # Calculate summary
    total_duration = (time.time() - start_time) * 1000
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    avg_score = sum(r.score for r in results) / len(results) if results else 0.0
    pass_rate = passed_count / len(results) if results else 0.0

    logger.info(f"Evaluation complete: {passed_count}/{len(results)} passed ({pass_rate:.1%})")

    return EvaluationResult(
        run_name=run_name,
        timestamp=datetime.now().isoformat(),
        dataset_name=dataset_name,
        total_tests=len(results),
        passed=passed_count,
        failed=failed_count,
        pass_rate=pass_rate,
        average_score=avg_score,
        duration_ms=total_duration,
        results=results
    )
