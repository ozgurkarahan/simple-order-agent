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
        client.get_all_orders.return_value = [{"orderID": "ORD-001", "productName": "Widget"}]
        client.get_orders_by_customer_id.return_value = [{"orderID": "ORD-001", "customerID": "CUST001"}]
        client.create_order.return_value = {"orderID": "ORD-NEW", "status": "created"}
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
        assert "get_all_orders" in tool_names
        assert "get_orders_by_customer_id" in tool_names
        assert "create_order" in tool_names

    def test_system_prompt_defined(self):
        """Test that system prompt is defined and contains key information."""
        assert "Orders Analytics Agent" in SYSTEM_PROMPT
        assert "get_all_orders" in SYSTEM_PROMPT
        assert "get_orders_by_customer_id" in SYSTEM_PROMPT
        assert "create_order" in SYSTEM_PROMPT

    def test_get_all_orders_tool_schema(self):
        """Test get_all_orders tool schema."""
        tool = next(t for t in TOOLS if t["name"] == "get_all_orders")

        assert "description" in tool
        assert tool["input_schema"]["type"] == "object"
        assert tool["input_schema"]["properties"] == {}

    def test_get_orders_by_customer_id_tool_schema(self):
        """Test get_orders_by_customer_id tool schema."""
        tool = next(t for t in TOOLS if t["name"] == "get_orders_by_customer_id")

        assert "description" in tool
        assert tool["input_schema"]["type"] == "object"
        assert "customer_id" in tool["input_schema"]["properties"]
        assert "customer_id" in tool["input_schema"]["required"]

    def test_create_order_tool_schema(self):
        """Test create_order tool schema."""
        tool = next(t for t in TOOLS if t["name"] == "create_order")

        assert "description" in tool
        props = tool["input_schema"]["properties"]
        assert "customer_id" in props
        assert "customer_name" in props
        assert "product_name" in props
        assert "price" in props
        assert "order_date" in props

        required = tool["input_schema"]["required"]
        assert "customer_id" in required
        assert "customer_name" in required
        assert "product_name" in required
        assert "price" in required
        assert "order_date" in required

    @pytest.mark.asyncio
    async def test_execute_tool_get_all_orders(self, agent, mock_mcp_client):
        """Test executing get_all_orders tool."""
        result = await agent._execute_tool("get_all_orders", {})

        mock_mcp_client.get_all_orders.assert_called_once()
        assert result == [{"orderID": "ORD-001", "productName": "Widget"}]

    @pytest.mark.asyncio
    async def test_execute_tool_get_orders_by_customer_id(self, agent, mock_mcp_client):
        """Test executing get_orders_by_customer_id tool."""
        result = await agent._execute_tool("get_orders_by_customer_id", {"customer_id": "CUST001"})

        mock_mcp_client.get_orders_by_customer_id.assert_called_once_with(customer_id="CUST001")
        assert result == [{"orderID": "ORD-001", "customerID": "CUST001"}]

    @pytest.mark.asyncio
    async def test_execute_tool_create_order(self, agent, mock_mcp_client):
        """Test executing create_order tool."""
        result = await agent._execute_tool(
            "create_order",
            {
                "customer_id": "CUST001",
                "customer_name": "John Doe",
                "product_name": "Widget",
                "price": 99.99,
                "order_date": "2024-01-15T10:00:00",
            },
        )

        mock_mcp_client.create_order.assert_called_once_with(
            customer_id="CUST001",
            customer_name="John Doe",
            product_name="Widget",
            price=99.99,
            order_date="2024-01-15T10:00:00",
        )
        assert result["orderID"] == "ORD-NEW"

    @pytest.mark.asyncio
    async def test_execute_tool_create_order_auto_date(self, agent, mock_mcp_client):
        """Test create_order tool auto-generates date if not provided."""
        result = await agent._execute_tool(
            "create_order",
            {
                "customer_id": "CUST001",
                "customer_name": "John Doe",
                "product_name": "Widget",
                "price": 99.99,
            },
        )

        # Verify create_order was called with a generated date
        call_args = mock_mcp_client.create_order.call_args
        assert call_args.kwargs["order_date"] is not None

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

    def test_required_params_have_descriptions(self):
        """Test that required parameters have descriptions."""
        for tool in TOOLS:
            required = tool["input_schema"].get("required", [])
            for param_name in required:
                prop = tool["input_schema"]["properties"].get(param_name)
                assert prop is not None, f"Required param {param_name} not in properties for {tool['name']}"
                assert "description" in prop, f"Missing description for {tool['name']}.{param_name}"
