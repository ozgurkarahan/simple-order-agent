"""Pytest integration for E2E agent evaluations."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
import pytest

# Load environment variables before skip markers are evaluated
load_dotenv()


@pytest.fixture
def dataset():
    """Load the evaluation dataset."""
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path) as f:
        return json.load(f)


@pytest.fixture
def eval_runner():
    """Create an E2E eval runner using OrdersAgent with MCP server."""
    from .run_evals import AgentEvalRunner, get_mcp_config_from_env

    mcp_config = get_mcp_config_from_env()
    return AgentEvalRunner(mcp_config=mcp_config)


# Mark tests that require API key and MCP server
requires_api_and_mcp = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY") or not os.environ.get("MCP_BASE_URL"),
    reason="ANTHROPIC_API_KEY and MCP_BASE_URL required for E2E tests",
)


class TestE2EAgentEvals:
    """E2E agent evaluation tests using real MCP server."""

    @requires_api_and_mcp
    @pytest.mark.asyncio
    async def test_list_orders_basic(self, eval_runner, dataset):
        """Test basic list orders query - full E2E flow."""
        eval_case = next(e for e in dataset["evals"] if e["id"] == "get_all_orders_basic")
        result = await eval_runner.run_single_eval(eval_case)

        assert result.actual_tool == "get_all_orders", (
            f"Expected get_all_orders, got {result.actual_tool}"
        )
        # E2E test: verify we got a response with actual order data
        assert result.response_text is not None, "Expected response text from agent"

    @requires_api_and_mcp
    @pytest.mark.asyncio
    async def test_get_customer_orders(self, eval_runner, dataset):
        """Test get orders by customer ID - full E2E flow."""
        eval_case = next(e for e in dataset["evals"] if e["id"] == "get_customer_orders_basic")
        result = await eval_runner.run_single_eval(eval_case)

        assert result.actual_tool == "get_orders_by_customer_id"
        assert result.actual_params is not None
        assert "id" in result.actual_params  # MCP uses 'id' not 'customer_id'
        # E2E: verify response exists
        assert result.response_text is not None

    @requires_api_and_mcp
    @pytest.mark.asyncio
    async def test_create_order_basic(self, eval_runner, dataset):
        """Test create order - full E2E flow."""
        eval_case = next(e for e in dataset["evals"] if e["id"] == "create_order_full")
        result = await eval_runner.run_single_eval(eval_case)

        assert result.actual_tool == "create_order"
        assert result.actual_params is not None
        assert "customerID" in result.actual_params  # MCP uses camelCase
        assert "productName" in result.actual_params  # MCP uses camelCase


class TestE2EBatchEvals:
    """Batch E2E evaluation runs."""

    @requires_api_and_mcp
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_happy_path_evals(self, eval_runner):
        """Run all happy path evaluations - full E2E."""
        dataset_path = Path(__file__).parent / "dataset.json"
        summary = await eval_runner.run_evals(
            dataset_path,
            tags=["happy_path"],
        )

        print("\nHappy Path E2E Results:")
        print(f"  Total: {summary.total}")
        print(f"  Passed: {summary.passed}")
        print(f"  Tool Accuracy: {summary.tool_accuracy:.1%}")

        # We expect high accuracy on happy path cases
        assert summary.tool_accuracy >= 0.9, f"Tool accuracy {summary.tool_accuracy:.1%} below 90%"

    @requires_api_and_mcp
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_all_tool_selection_evals(self, eval_runner):
        """Run all tool selection evaluations - full E2E."""
        dataset_path = Path(__file__).parent / "dataset.json"
        summary = await eval_runner.run_evals(
            dataset_path,
            categories=["tool_selection"],
        )

        print("\nTool Selection E2E Results:")
        print(f"  Total: {summary.total}")
        print(f"  Passed: {summary.passed}")
        print(f"  Tool Accuracy: {summary.tool_accuracy:.1%}")

        # We expect good accuracy
        assert summary.tool_accuracy >= 0.85, f"Tool accuracy {summary.tool_accuracy:.1%} below 85%"

    @requires_api_and_mcp
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_e2e_response_quality(self, eval_runner):
        """Run E2E tests that validate response quality."""
        dataset_path = Path(__file__).parent / "dataset.json"
        summary = await eval_runner.run_evals(
            dataset_path,
            categories=["e2e"],
        )

        print("\nE2E Response Quality Results:")
        print(f"  Total: {summary.total}")
        print(f"  Passed: {summary.passed}")

        if summary.total > 0:
            pass_rate = summary.passed / summary.total
            assert pass_rate >= 0.8, f"E2E pass rate {pass_rate:.1%} below 80%"


class TestDatasetValidity:
    """Test that the dataset is valid - no API key required."""

    def test_dataset_loads(self, dataset):
        """Test that dataset loads successfully."""
        assert "version" in dataset
        assert "evals" in dataset
        assert len(dataset["evals"]) > 0

    def test_all_evals_have_required_fields(self, dataset):
        """Test that all evals have required fields."""
        for eval_case in dataset["evals"]:
            assert "id" in eval_case, "Eval missing id"
            assert "category" in eval_case, f"Eval {eval_case.get('id')} missing category"
            assert "input" in eval_case, f"Eval {eval_case.get('id')} missing input"

    def test_tool_selection_evals_have_expected_tool(self, dataset):
        """Test that tool selection evals have expected_tool."""
        for eval_case in dataset["evals"]:
            if eval_case["category"] == "tool_selection":
                assert "expected_tool" in eval_case, f"Eval {eval_case['id']} missing expected_tool"

    def test_eval_ids_are_unique(self, dataset):
        """Test that all eval IDs are unique."""
        ids = [e["id"] for e in dataset["evals"]]
        assert len(ids) == len(set(ids)), "Duplicate eval IDs found"

    def test_categories_are_valid(self, dataset):
        """Test that categories are from allowed set."""
        valid_categories = {
            "tool_selection",
            "response_quality",
            "clarification",
            "error_handling",
            "e2e",
        }
        for eval_case in dataset["evals"]:
            assert eval_case["category"] in valid_categories, (
                f"Invalid category {eval_case['category']} in eval {eval_case['id']}"
            )

    def test_expected_tools_are_valid(self, dataset):
        """Test that expected tools match actual agent tools."""
        # Support both hyphen (MCP style) and underscore (Python style)
        valid_tools = {
            "get_all_orders",
            "get-all-orders",
            "get_orders_by_customer_id",
            "get-orders-by-customer-id",
            "create_order",
            "create-order",
        }
        for eval_case in dataset["evals"]:
            if "expected_tool" in eval_case:
                assert eval_case["expected_tool"] in valid_tools, (
                    f"Invalid expected_tool {eval_case['expected_tool']} in eval {eval_case['id']}"
                )
