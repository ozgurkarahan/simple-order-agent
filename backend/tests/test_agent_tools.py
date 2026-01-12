"""Tests for agent tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.orders_agent import OrdersAgent, TOOLS, SYSTEM_PROMPT


class TestOrdersAgent:
    """Test cases for OrdersAgent."""

    @pytest.fixture
    def mock_mcp_client(self):
        """Create a mock MCP client."""
        client = AsyncMock()
        client.list_orders.return_value = [{"order_id": "ORD-001"}]
        client.get_order.return_value = {"order_id": "ORD-001", "status": "pending"}
        client.create_order.return_value = {"order_id": "ORD-NEW"}
        return client

    @pytest.fixture
    def agent(self, mock_mcp_client):
        """Create an agent for testing."""
        with patch("agent.orders_agent.anthropic.AsyncAnthropic"):
            return OrdersAgent(
                api_key="test-api-key",
                mcp_client=mock_mcp_client,
            )

    def test_init(self, agent):
        """Test agent initialization."""
        assert agent.model == "claude-sonnet-4-20250514"
        assert agent.conversations == {}

    def test_tools_defined(self):
        """Test that all required tools are defined."""
        tool_names = [t["name"] for t in TOOLS]
        assert "list_orders" in tool_names
        assert "get_order" in tool_names
        assert "create_order" in tool_names

    def test_system_prompt_defined(self):
        """Test that system prompt is defined and contains key information."""
        assert "Orders Analytics Agent" in SYSTEM_PROMPT
        assert "list_orders" in SYSTEM_PROMPT
        assert "get_order" in SYSTEM_PROMPT
        assert "create_order" in SYSTEM_PROMPT

    def test_list_orders_tool_schema(self):
        """Test list_orders tool schema."""
        tool = next(t for t in TOOLS if t["name"] == "list_orders")

        assert "description" in tool
        assert tool["input_schema"]["type"] == "object"

        props = tool["input_schema"]["properties"]
        assert "status" in props
        assert "date_from" in props
        assert "date_to" in props
        assert "customer_id" in props
        assert "limit" in props

    def test_get_order_tool_schema(self):
        """Test get_order tool schema."""
        tool = next(t for t in TOOLS if t["name"] == "get_order")

        assert "description" in tool
        assert tool["input_schema"]["type"] == "object"
        assert "order_id" in tool["input_schema"]["properties"]
        assert "order_id" in tool["input_schema"]["required"]

    def test_create_order_tool_schema(self):
        """Test create_order tool schema."""
        tool = next(t for t in TOOLS if t["name"] == "create_order")

        assert "description" in tool
        props = tool["input_schema"]["properties"]
        assert "customer_id" in props
        assert "items" in props
        assert "shipping_address" in props

        required = tool["input_schema"]["required"]
        assert "customer_id" in required
        assert "items" in required

    @pytest.mark.asyncio
    async def test_execute_tool_list_orders(self, agent, mock_mcp_client):
        """Test executing list_orders tool."""
        result = await agent._execute_tool("list_orders", {"status": "pending"})

        mock_mcp_client.list_orders.assert_called_once_with(
            status="pending",
            date_from=None,
            date_to=None,
            customer_id=None,
            limit=None,
        )
        assert result == [{"order_id": "ORD-001"}]

    @pytest.mark.asyncio
    async def test_execute_tool_get_order(self, agent, mock_mcp_client):
        """Test executing get_order tool."""
        result = await agent._execute_tool("get_order", {"order_id": "ORD-001"})

        mock_mcp_client.get_order.assert_called_once_with(order_id="ORD-001")
        assert result["order_id"] == "ORD-001"

    @pytest.mark.asyncio
    async def test_execute_tool_create_order(self, agent, mock_mcp_client):
        """Test executing create_order tool."""
        result = await agent._execute_tool(
            "create_order",
            {
                "customer_id": "CUST-001",
                "items": [{"product_id": "PROD-001", "quantity": 2}],
            },
        )

        mock_mcp_client.create_order.assert_called_once()
        assert result["order_id"] == "ORD-NEW"

    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self, agent):
        """Test executing unknown tool raises error."""
        with pytest.raises(ValueError) as exc_info:
            await agent._execute_tool("unknown_tool", {})

        assert "Unknown tool" in str(exc_info.value)

    def test_get_conversation_new(self, agent):
        """Test getting a new conversation."""
        conv = agent._get_conversation("new-conv-id")
        assert conv == []
        assert "new-conv-id" in agent.conversations

    def test_get_conversation_existing(self, agent):
        """Test getting an existing conversation."""
        agent.conversations["existing-id"] = [{"role": "user", "content": "Hello"}]

        conv = agent._get_conversation("existing-id")
        assert len(conv) == 1

    def test_get_conversation_none(self, agent):
        """Test getting conversation with None ID."""
        conv = agent._get_conversation(None)
        assert conv == []


class TestToolDefinitions:
    """Test tool definition structure and validation."""

    def test_all_tools_have_required_fields(self):
        """Test that all tools have required fields."""
        for tool in TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["input_schema"]["type"] == "object"
            assert "properties" in tool["input_schema"]

    def test_tool_descriptions_are_meaningful(self):
        """Test that tool descriptions are meaningful."""
        for tool in TOOLS:
            assert len(tool["description"]) > 20
            # Descriptions should not be generic
            assert tool["description"] != "A tool"
            assert tool["description"] != "Does something"

    def test_property_descriptions_exist(self):
        """Test that properties have descriptions."""
        for tool in TOOLS:
            for prop_name, prop_def in tool["input_schema"]["properties"].items():
                assert "description" in prop_def, f"Missing description for {tool['name']}.{prop_name}"
                assert len(prop_def["description"]) > 5
