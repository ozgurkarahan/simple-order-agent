"""Agent evaluation runner."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import tool definitions from agent
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent.orders_agent import TOOLS, SYSTEM_PROMPT


@dataclass
class EvalResult:
    """Result of a single evaluation."""

    eval_id: str
    passed: bool
    expected_tool: str | None
    actual_tool: str | None
    expected_params: dict | None
    actual_params: dict | None
    error: str | None = None
    response_text: str | None = None
    latency_ms: float = 0


@dataclass
class EvalSummary:
    """Summary of evaluation results."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    tool_accuracy: float = 0.0
    param_accuracy: float = 0.0
    results: list[EvalResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "tool_accuracy": self.tool_accuracy,
            "param_accuracy": self.param_accuracy,
            "timestamp": self.timestamp,
            "results": [
                {
                    "eval_id": r.eval_id,
                    "passed": r.passed,
                    "expected_tool": r.expected_tool,
                    "actual_tool": r.actual_tool,
                    "error": r.error,
                    "latency_ms": r.latency_ms,
                }
                for r in self.results
            ],
        }


class EvalRunner:
    """Runner for agent evaluations."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the eval runner.

        Args:
            api_key: Anthropic API key
            model: Model to use for evaluation
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def run_single_eval(self, eval_case: dict) -> EvalResult:
        """
        Run a single evaluation case.

        Args:
            eval_case: Evaluation case from dataset

        Returns:
            Evaluation result
        """
        eval_id = eval_case["id"]
        input_text = eval_case["input"]
        expected_tool = eval_case.get("expected_tool")
        expected_params = eval_case.get("expected_params", {})
        expected_params_subset = eval_case.get("expected_params_subset", {})
        expected_params_keys = eval_case.get("expected_params_contain_keys", [])
        expected_behavior = eval_case.get("expected_behavior")

        logger.info(f"Running eval: {eval_id}")

        try:
            import time
            start_time = time.time()

            # Call the model
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=[{"role": "user", "content": input_text}],
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract tool use from response
            actual_tool = None
            actual_params = None
            response_text = None

            for block in response.content:
                if block.type == "tool_use":
                    actual_tool = block.name
                    actual_params = block.input
                elif block.type == "text":
                    response_text = block.text

            # Check if this is an expected clarification case
            if expected_behavior in ["ask_for_clarification", "ask_for_order_id"]:
                # For clarification cases, we expect NO tool use and a text response
                passed = actual_tool is None and response_text is not None
                return EvalResult(
                    eval_id=eval_id,
                    passed=passed,
                    expected_tool=None,
                    actual_tool=actual_tool,
                    expected_params=None,
                    actual_params=actual_params,
                    response_text=response_text,
                    latency_ms=latency_ms,
                    error=None if passed else "Expected clarification but got tool use",
                )

            # Check tool selection
            tool_match = actual_tool == expected_tool

            # Check parameters
            param_match = True
            if expected_params and actual_params:
                for key, value in expected_params.items():
                    if actual_params.get(key) != value:
                        param_match = False
                        break

            if expected_params_subset and actual_params:
                for key, value in expected_params_subset.items():
                    if key in actual_params and actual_params[key] != value:
                        param_match = False
                        break

            if expected_params_keys and actual_params:
                for key in expected_params_keys:
                    if key not in actual_params:
                        param_match = False
                        break

            passed = tool_match and param_match

            return EvalResult(
                eval_id=eval_id,
                passed=passed,
                expected_tool=expected_tool,
                actual_tool=actual_tool,
                expected_params=expected_params or expected_params_subset,
                actual_params=actual_params,
                response_text=response_text,
                latency_ms=latency_ms,
                error=None if passed else f"Tool match: {tool_match}, Param match: {param_match}",
            )

        except Exception as e:
            logger.error(f"Error running eval {eval_id}: {e}")
            return EvalResult(
                eval_id=eval_id,
                passed=False,
                expected_tool=expected_tool,
                actual_tool=None,
                expected_params=None,
                actual_params=None,
                error=str(e),
            )

    async def run_evals(
        self,
        dataset_path: str | Path,
        tags: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> EvalSummary:
        """
        Run evaluations from a dataset file.

        Args:
            dataset_path: Path to the dataset JSON file
            tags: Optional list of tags to filter evals
            categories: Optional list of categories to filter evals

        Returns:
            Evaluation summary
        """
        # Load dataset
        with open(dataset_path) as f:
            dataset = json.load(f)

        evals = dataset["evals"]

        # Filter by tags if specified
        if tags:
            evals = [e for e in evals if any(t in e.get("tags", []) for t in tags)]

        # Filter by categories if specified
        if categories:
            evals = [e for e in evals if e.get("category") in categories]

        logger.info(f"Running {len(evals)} evaluations...")

        # Run all evals
        results = []
        for eval_case in evals:
            result = await self.run_single_eval(eval_case)
            results.append(result)

        # Calculate metrics
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        tool_correct = sum(
            1 for r in results
            if r.expected_tool and r.actual_tool == r.expected_tool
        )
        tool_total = sum(1 for r in results if r.expected_tool)

        param_correct = sum(
            1 for r in results
            if r.passed and r.expected_params
        )
        param_total = sum(1 for r in results if r.expected_params)

        summary = EvalSummary(
            total=total,
            passed=passed,
            failed=failed,
            tool_accuracy=tool_correct / tool_total if tool_total > 0 else 0,
            param_accuracy=param_correct / param_total if param_total > 0 else 0,
            results=results,
        )

        return summary


async def main():
    """Run evaluations from command line."""
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return

    runner = EvalRunner(api_key=api_key)

    dataset_path = Path(__file__).parent / "dataset.json"
    summary = await runner.run_evals(dataset_path)

    print("\n" + "=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"Total: {summary.total}")
    print(f"Passed: {summary.passed}")
    print(f"Failed: {summary.failed}")
    print(f"Tool Accuracy: {summary.tool_accuracy:.1%}")
    print(f"Param Accuracy: {summary.param_accuracy:.1%}")
    print("=" * 50)

    if summary.failed > 0:
        print("\nFailed evals:")
        for result in summary.results:
            if not result.passed:
                print(f"  - {result.eval_id}: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
