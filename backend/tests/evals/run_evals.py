"""Agent E2E evaluation runner using OrdersAgent with MCP server."""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for agent imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.orders_agent import OrdersAgent
from api.config_models import MCPServerConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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


def get_mcp_config_from_env() -> MCPServerConfig:
    """
    Load MCP configuration from environment variables.

    Required env vars:
        MCP_BASE_URL: MCP server endpoint
        MCP_CLIENT_ID: Client ID for authentication
        MCP_CLIENT_SECRET: Client secret for authentication
    """
    url = os.environ.get("MCP_BASE_URL")
    client_id = os.environ.get("MCP_CLIENT_ID")
    client_secret = os.environ.get("MCP_CLIENT_SECRET")

    if not url:
        raise ValueError("MCP_BASE_URL environment variable not set")
    if not client_id or not client_secret:
        raise ValueError("MCP_CLIENT_ID and MCP_CLIENT_SECRET environment variables required")

    return MCPServerConfig(
        name="orders",
        url=url,
        headers={
            "client_id": client_id,
            "client_secret": client_secret,
        },
        is_active=True,
    )


class AgentEvalRunner:
    """
    E2E evaluation runner using OrdersAgent with real MCP server.

    This runner tests the complete agent flow:
    user query -> tool selection -> tool execution via MCP -> response generation
    """

    def __init__(self, mcp_config: MCPServerConfig | None = None):
        """
        Initialize the eval runner.

        Args:
            mcp_config: MCP server configuration. If None, loads from environment.
        """
        if mcp_config is None:
            mcp_config = get_mcp_config_from_env()

        self.mcp_config = mcp_config
        self.agent = OrdersAgent(mcp_config=mcp_config)
        logger.info(f"AgentEvalRunner initialized with MCP server: {mcp_config.url}")

    async def run_single_eval(self, eval_case: dict) -> EvalResult:
        """
        Run a single E2E evaluation case.

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
        response_must_contain = eval_case.get("response_must_contain", [])

        logger.info(f"Running eval: {eval_id}")

        try:
            start_time = time.time()

            # Collect events from agent chat
            actual_tool = None
            actual_params = None
            response_texts = []

            async for event in self.agent.chat(input_text):
                if event["type"] == "tool_use":
                    data = json.loads(event["data"])
                    raw_tool = data.get("tool", "")
                    # MCP tools have prefix like "mcp__orders__get_all_orders"
                    # Extract just the tool name and normalize hyphens to underscores
                    if raw_tool.startswith("mcp__"):
                        # Format: mcp__<server>__<tool_name>
                        parts = raw_tool.split("__")
                        actual_tool = parts[-1] if len(parts) >= 3 else raw_tool
                    else:
                        actual_tool = raw_tool
                    actual_tool = actual_tool.replace("-", "_")
                    actual_params = data.get("input", {})
                elif event["type"] == "message":
                    data = json.loads(event["data"])
                    if data.get("type") == "text":
                        response_texts.append(data.get("content", ""))

            latency_ms = (time.time() - start_time) * 1000
            response_text = "\n".join(response_texts) if response_texts else None

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

            # Normalize expected tool (MCP uses hyphens, convert to underscores)
            normalized_expected_tool = expected_tool.replace("-", "_") if expected_tool else None

            # Check tool selection
            tool_match = actual_tool == normalized_expected_tool

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

            # Check response content (for E2E tests)
            response_match = True
            if response_must_contain and response_text:
                response_lower = response_text.lower()
                for keyword in response_must_contain:
                    if keyword.lower() not in response_lower:
                        response_match = False
                        break

            passed = tool_match and param_match and response_match

            error_parts = []
            if not tool_match:
                error_parts.append(f"Tool mismatch: expected {normalized_expected_tool}, got {actual_tool}")
            if not param_match:
                error_parts.append("Param mismatch")
            if not response_match:
                error_parts.append(f"Response missing keywords: {response_must_contain}")

            return EvalResult(
                eval_id=eval_id,
                passed=passed,
                expected_tool=expected_tool,
                actual_tool=actual_tool,
                expected_params=expected_params or expected_params_subset,
                actual_params=actual_params,
                response_text=response_text,
                latency_ms=latency_ms,
                error="; ".join(error_parts) if error_parts else None,
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
            1 for r in results if r.expected_tool and r.actual_tool == r.expected_tool.replace("-", "_")
        )
        tool_total = sum(1 for r in results if r.expected_tool)

        param_correct = sum(1 for r in results if r.passed and r.expected_params)
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
    # Check for required environment variables
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return

    try:
        runner = AgentEvalRunner()
    except ValueError as e:
        print(f"Error: {e}")
        return

    dataset_path = Path(__file__).parent / "dataset.json"
    summary = await runner.run_evals(dataset_path)

    print("\n" + "=" * 50)
    print("E2E EVALUATION RESULTS")
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
