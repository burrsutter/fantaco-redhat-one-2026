"""
Scoring module for evaluation.
Provides substring matching scorer for comparing LLM responses against expected keywords.
"""

from typing import List
from dataclasses import dataclass


@dataclass
class ScoreResult:
    """Result of scoring a single test case"""
    passed: bool
    score: float  # 0.0 to 1.0
    matched_keywords: List[str]
    missing_keywords: List[str]
    details: str


def substring_score(
    response: str,
    keywords: List[str],
    match_mode: str = "all",
    case_sensitive: bool = False
) -> ScoreResult:
    """
    Score a response based on substring matching.

    Args:
        response: The LLM response text
        keywords: List of expected keywords/phrases
        match_mode: "all" (all must match) or "any" (at least one)
        case_sensitive: Whether matching is case-sensitive

    Returns:
        ScoreResult with pass/fail and details
    """
    if not keywords:
        return ScoreResult(
            passed=True,
            score=1.0,
            matched_keywords=[],
            missing_keywords=[],
            details="No keywords to match"
        )

    check_response = response if case_sensitive else response.lower()

    matched = []
    missing = []

    for keyword in keywords:
        check_keyword = keyword if case_sensitive else keyword.lower()
        if check_keyword in check_response:
            matched.append(keyword)
        else:
            missing.append(keyword)

    if match_mode == "all":
        passed = len(missing) == 0
        score = len(matched) / len(keywords)
    else:  # "any"
        passed = len(matched) > 0
        score = 1.0 if passed else 0.0

    details = f"Matched {len(matched)}/{len(keywords)} keywords"
    if missing:
        details += f". Missing: {missing}"

    return ScoreResult(
        passed=passed,
        score=score,
        matched_keywords=matched,
        missing_keywords=missing,
        details=details
    )
