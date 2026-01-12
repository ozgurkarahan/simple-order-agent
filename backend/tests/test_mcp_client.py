"""Tests for MCP client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

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

    def test_auth_headers(self, mcp_client):
        """Test that auth headers are set correctly."""
        headers = mcp_client._client.headers
        assert headers["client_id"] == "test-client-id"
        assert headers["client_secret"] == "test-client-secret"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_close(self, mcp_client):
        """Test client close."""
        await mcp_client.close()
        # Should not raise

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_client):
        """Test listing available tools."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "tools": [
                    {"name": "list_orders", "description": "List orders"},
                    {"name": "get_order", "description": "Get order"},
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(mcp_client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            tools = await mcp_client.list_tools()

            assert len(tools) == 2
            assert tools[0]["name"] == "list_orders"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mcp_client):
        """Test successful tool call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "content": [
                    {"type": "text", "text": '{"orders": []}'}
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(mcp_client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await mcp_client.call_tool("list_orders", {"limit": 10})

            assert result == '{"orders": []}'
            mock_request.assert_called_once_with(
                "POST",
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "list_orders",
                        "arguments": {"limit": 10},
                    },
                },
            )

    @pytest.mark.asyncio
    async def test_call_tool_http_error(self, mcp_client):
        """Test tool call with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(mcp_client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(MCPClientError) as exc_info:
                await mcp_client.call_tool("list_orders", {})

            assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_orders(self, mcp_client):
        """Test list_orders convenience method."""
        with patch.object(mcp_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = [{"order_id": "ORD-001"}]

            result = await mcp_client.list_orders(
                status="pending",
                date_from="2024-01-01",
                limit=5,
            )

            mock_call.assert_called_once_with(
                "list_orders",
                {
                    "status": "pending",
                    "date_from": "2024-01-01",
                    "limit": 5,
                },
            )
            assert result == [{"order_id": "ORD-001"}]

    @pytest.mark.asyncio
    async def test_get_order(self, mcp_client):
        """Test get_order convenience method."""
        with patch.object(mcp_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"order_id": "ORD-001", "status": "pending"}

            result = await mcp_client.get_order("ORD-001")

            mock_call.assert_called_once_with("get_order", {"order_id": "ORD-001"})
            assert result["order_id"] == "ORD-001"

    @pytest.mark.asyncio
    async def test_create_order(self, mcp_client):
        """Test create_order convenience method."""
        with patch.object(mcp_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"order_id": "ORD-NEW", "status": "pending"}

            result = await mcp_client.create_order(
                customer_id="CUST-001",
                items=[{"product_id": "PROD-001", "quantity": 2}],
                shipping_address={"city": "Test City"},
            )

            mock_call.assert_called_once_with(
                "create_order",
                {
                    "customer_id": "CUST-001",
                    "items": [{"product_id": "PROD-001", "quantity": 2}],
                    "shipping_address": {"city": "Test City"},
                },
            )
            assert result["order_id"] == "ORD-NEW"
