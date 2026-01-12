"""Tests for agent tools and configuration."""

from unittest.mock import MagicMock, patch

import pytest

from agent.orders_agent import SYSTEM_PROMPT, TOOLS, OrdersAgent


class TestOrdersAgent:
    """Test cases for OrdersAgent."""

    @pytest.fixture
    def agent(self):
        """Create an agent for testing."""
        # Patch the SDK to avoid actual initialization
        with patch("agent.orders_agent.query"):
            return OrdersAgent()

    def test_init(self, agent):
        """Test agent initialization."""
        assert agent.model == "claude-sonnet-4-20250514"
        assert agent.conversations == {}

    def test_init_custom_model(self):
        """Test agent initialization with custom model."""
        with patch("agent.orders_agent.query"):
            agent = OrdersAgent(model="claude-opus-4-20250514")
            assert agent.model == "claude-opus-4-20250514"

    def test_tools_defined(self):
        """Test that all required tools are defined."""
        tool_names = [t["name"] for t in TOOLS]
        assert "get_all_orders" in tool_names
        assert "get_orders_by_customer_id" in tool_names
        assert "create_order" in tool_names

    def test_system_prompt_defined(self):
        """Test that system prompt is defined and contains key information."""
        assert "Orders Analytics Agent" in SYSTEM_PROMPT
        assert "get-all-orders" in SYSTEM_PROMPT
        assert "get-orders-by-customer-id" in SYSTEM_PROMPT
        assert "create-order" in SYSTEM_PROMPT

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

    def test_build_options(self, agent):
        """Test that build_options returns correct configuration."""
        options = agent._build_options()

        assert options.model == "claude-sonnet-4-20250514"
        assert options.system_prompt == SYSTEM_PROMPT
        assert options.setting_sources == ["project"]
        assert options.permission_mode == "auto"
        assert options.max_turns == 10


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


class TestMcpConfiguration:
    """Test MCP configuration file."""

    def test_mcp_json_exists(self):
        """Test that .mcp.json configuration file exists."""
        import json
        from pathlib import Path

        mcp_config_path = Path(__file__).parent.parent / ".mcp.json"
        assert mcp_config_path.exists(), ".mcp.json file should exist"

        with open(mcp_config_path) as f:
            config = json.load(f)

        assert "mcpServers" in config
        assert "orders" in config["mcpServers"]

    def test_mcp_json_has_correct_structure(self):
        """Test that .mcp.json has correct structure."""
        import json
        from pathlib import Path

        mcp_config_path = Path(__file__).parent.parent / ".mcp.json"

        with open(mcp_config_path) as f:
            config = json.load(f)

        orders_config = config["mcpServers"]["orders"]
        assert orders_config["type"] == "http"
        assert "url" in orders_config
        assert "headers" in orders_config
        assert "client_id" in orders_config["headers"]
        assert "client_secret" in orders_config["headers"]
