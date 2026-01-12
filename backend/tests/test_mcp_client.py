"""Tests for MCP client."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mcp.client import MCPClient, MCPClientError


class TestMCPClient:
    """Test cases for MCPClient."""

    @pytest.fixture
    def mcp_client(self):
        """Create an MCP client for testing."""
        return MCPClient(
            base_url="https://test-mcp-server.example.com/orders-mcp/",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

    def test_init(self, mcp_client):
        """Test client initialization."""
        assert mcp_client.base_url == "https://test-mcp-server.example.com/orders-mcp"
        assert mcp_client.client_id == "test-client-id"
        assert mcp_client.client_secret == "test-client-secret"
        assert mcp_client.session_id is None
        assert mcp_client._initialized is False

    def test_get_headers_without_session(self, mcp_client):
        """Test headers without session."""
        headers = mcp_client._get_headers()
        assert headers["client_id"] == "test-client-id"
        assert headers["client_secret"] == "test-client-secret"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json, text/event-stream"
        assert "mcp-session-id" not in headers

    def test_get_headers_with_session(self, mcp_client):
        """Test headers with session."""
        mcp_client.session_id = "test-session-123"
        headers = mcp_client._get_headers()
        assert headers["mcp-session-id"] == "test-session-123"

    @pytest.mark.asyncio
    async def test_close(self, mcp_client):
        """Test client close."""
        await mcp_client.close()
        # Should not raise

    def test_parse_sse_response(self, mcp_client):
        """Test SSE response parsing."""
        sse_response = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"tools":[]}}\n\n'
        result = mcp_client._parse_sse_response(sse_response)
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert result["result"] == {"tools": []}

    def test_parse_sse_response_invalid_json(self, mcp_client):
        """Test SSE response parsing with invalid JSON."""
        sse_response = "event: message\ndata: not-json\n\n"
        with pytest.raises(MCPClientError) as exc_info:
            mcp_client._parse_sse_response(sse_response)
        assert "Invalid JSON" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_initialize(self, mcp_client):
        """Test session initialization."""
        mock_response = MagicMock()
        mock_response.text = """event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","serverInfo":{"name":"test-server","version":"1.0.0"}}}

"""
        mock_response.headers = {"mcp-session-id": "session-abc123"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(mcp_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await mcp_client.initialize()

            assert mcp_client._initialized is True
            assert mcp_client.session_id == "session-abc123"
            assert result["serverInfo"]["name"] == "test-server"

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_client):
        """Test listing available tools."""
        # First mock initialize
        init_response = MagicMock()
        init_response.text = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\n\n'
        init_response.headers = {"mcp-session-id": "session-123"}
        init_response.raise_for_status = MagicMock()

        # Then mock tools/list
        tools_response = MagicMock()
        tools_response.text = """event: message
data: {"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"get-all-orders","description":"Get all orders"}]}}

"""
        tools_response.headers = {"mcp-session-id": "session-123"}
        tools_response.raise_for_status = MagicMock()

        with patch.object(mcp_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [init_response, tools_response]

            tools = await mcp_client.list_tools()

            assert len(tools) == 1
            assert tools[0]["name"] == "get-all-orders"

    @pytest.mark.asyncio
    async def test_call_tool_http_error(self, mcp_client):
        """Test tool call with HTTP error."""
        mcp_client._initialized = True  # Skip initialization

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(mcp_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(MCPClientError) as exc_info:
                await mcp_client.call_tool("get-all-orders", {})

            assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_all_orders(self, mcp_client):
        """Test get_all_orders convenience method."""
        mcp_client._initialized = True

        mock_response = MagicMock()
        mock_response.text = """event: message
data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"[{\\"orderID\\":\\"ORD001\\"}]"}]}}

"""
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        with patch.object(mcp_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await mcp_client.get_all_orders()

            # Verify the call was made correctly
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["method"] == "tools/call"
            assert payload["params"]["name"] == "get-all-orders"

    @pytest.mark.asyncio
    async def test_get_orders_by_customer_id(self, mcp_client):
        """Test get_orders_by_customer_id convenience method."""
        mcp_client._initialized = True

        mock_response = MagicMock()
        mock_response.text = """event: message
data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"[{\\"orderID\\":\\"ORD001\\"}]"}]}}

"""
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        with patch.object(mcp_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await mcp_client.get_orders_by_customer_id("CUST001")

            # Verify the call was made correctly
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["method"] == "tools/call"
            assert payload["params"]["name"] == "get-orders-by-customer-id"
            assert payload["params"]["arguments"]["id"] == "CUST001"

    @pytest.mark.asyncio
    async def test_create_order(self, mcp_client):
        """Test create_order convenience method."""
        mcp_client._initialized = True

        mock_response = MagicMock()
        mock_response.text = """event: message
data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"{\\"orderID\\":\\"ORD-NEW\\"}"}]}}

"""
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        with patch.object(mcp_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await mcp_client.create_order(
                customer_id="CUST001",
                customer_name="John Doe",
                product_name="Widget",
                price=99.99,
                order_date="2024-01-15T10:00:00",
            )

            # Verify the call was made correctly
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["method"] == "tools/call"
            assert payload["params"]["name"] == "create-order"
            assert payload["params"]["arguments"]["customerID"] == "CUST001"
            assert payload["params"]["arguments"]["customerName"] == "John Doe"
            assert payload["params"]["arguments"]["productName"] == "Widget"
            assert payload["params"]["arguments"]["price"] == 99.99
