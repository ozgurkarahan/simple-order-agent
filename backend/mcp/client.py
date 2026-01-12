"""MCP Client for communicating with the Orders MCP server."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Base exception for MCP client errors."""

    pass


class MCPClient:
    """
    Client for communicating with the Orders MCP server.

    Handles authentication and provides methods for each MCP operation.
    """

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        timeout: float = 30.0,
    ):
        """
        Initialize the MCP client.

        Args:
            base_url: Base URL of the MCP server
            client_id: Client ID for authentication
            client_secret: Client secret for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "client_id": client_id,
                "client_secret": client_secret,
                "Content-Type": "application/json",
            },
        )

        logger.info(f"MCP Client initialized for {self.base_url}")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the MCP server.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for httpx request

        Returns:
            JSON response as dictionary

        Raises:
            MCPClientError: If the request fails
        """
        try:
            response = await self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"MCP HTTP error: {e.response.status_code} - {e.response.text}")
            raise MCPClientError(
                f"MCP server returned {e.response.status_code}: {e.response.text}"
            )

        except httpx.RequestError as e:
            logger.error(f"MCP request error: {e}")
            raise MCPClientError(f"Failed to connect to MCP server: {e}")

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        List available tools from the MCP server.

        Returns:
            List of tool definitions
        """
        response = await self._request("POST", "/mcp", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        })
        return response.get("result", {}).get("tools", [])

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")

        response = await self._request("POST", "/mcp", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
        })

        result = response.get("result", {})
        logger.debug(f"MCP tool response: {result}")

        # Handle MCP content array format
        if "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                # Return the text content from the first item
                first_item = content[0]
                if isinstance(first_item, dict) and "text" in first_item:
                    return first_item["text"]
            return content

        return result

    # Convenience methods for specific tools

    async def list_orders(
        self,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        customer_id: str | None = None,
        limit: int | None = None,
    ) -> Any:
        """
        List orders with optional filters.

        Args:
            status: Filter by order status
            date_from: Filter orders from this date (ISO format)
            date_to: Filter orders until this date (ISO format)
            customer_id: Filter by customer ID
            limit: Maximum number of orders to return

        Returns:
            List of orders
        """
        arguments = {}
        if status:
            arguments["status"] = status
        if date_from:
            arguments["date_from"] = date_from
        if date_to:
            arguments["date_to"] = date_to
        if customer_id:
            arguments["customer_id"] = customer_id
        if limit:
            arguments["limit"] = limit

        return await self.call_tool("list_orders", arguments)

    async def get_order(self, order_id: str) -> Any:
        """
        Get details for a specific order.

        Args:
            order_id: The order ID to retrieve

        Returns:
            Order details
        """
        return await self.call_tool("get_order", {"order_id": order_id})

    async def create_order(
        self,
        customer_id: str,
        items: list[dict[str, Any]],
        shipping_address: dict[str, Any] | None = None,
    ) -> Any:
        """
        Create a new order.

        Args:
            customer_id: Customer ID for the order
            items: List of order items with product_id, quantity, price
            shipping_address: Optional shipping address

        Returns:
            Created order details
        """
        arguments = {
            "customer_id": customer_id,
            "items": items,
        }
        if shipping_address:
            arguments["shipping_address"] = shipping_address

        return await self.call_tool("create_order", arguments)
