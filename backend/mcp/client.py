"""MCP Client for communicating with the Orders MCP server."""

import json
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

    Handles authentication, session management, and provides methods for each MCP operation.
    Uses the MCP protocol with SSE transport.
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
        self.session_id: str | None = None
        self._initialized = False

        self._client = httpx.AsyncClient(
            timeout=timeout,
            verify=True,  # Enable SSL verification in production
        )

        logger.info(f"MCP Client initialized for {self.base_url}")

    def _get_headers(self) -> dict[str, str]:
        """Get headers for MCP requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        return headers

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _parse_sse_response(self, response_text: str) -> dict[str, Any]:
        """
        Parse SSE response format from MCP server.

        Args:
            response_text: Raw SSE response text

        Returns:
            Parsed JSON data from the response
        """
        # SSE format: "event: message\ndata: {...}\n\n"
        for line in response_text.split("\n"):
            if line.startswith("data: "):
                data_str = line[6:]  # Remove "data: " prefix
                try:
                    return json.loads(data_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse SSE data: {e}")
                    raise MCPClientError(f"Invalid JSON in SSE response: {data_str}")
        
        # If no data line found, try parsing the whole response as JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            raise MCPClientError(f"Could not parse response: {response_text[:200]}")

    async def _request(
        self,
        method_name: str,
        params: dict[str, Any] | None = None,
        request_id: int = 1,
    ) -> dict[str, Any]:
        """
        Make a JSON-RPC request to the MCP server.

        Args:
            method_name: MCP method name
            params: Method parameters
            request_id: JSON-RPC request ID

        Returns:
            JSON response as dictionary

        Raises:
            MCPClientError: If the request fails
        """
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method_name,
        }
        if params:
            payload["params"] = params

        try:
            response = await self._client.post(
                f"{self.base_url}/",
                headers=self._get_headers(),
                json=payload,
            )
            
            # Store session ID from response headers
            if "mcp-session-id" in response.headers:
                self.session_id = response.headers["mcp-session-id"]
            
            response.raise_for_status()
            
            # Parse SSE response
            result = self._parse_sse_response(response.text)
            
            # Check for JSON-RPC error
            if "error" in result:
                error = result["error"]
                raise MCPClientError(f"MCP error {error.get('code')}: {error.get('message')}")
            
            return result.get("result", {})

        except httpx.HTTPStatusError as e:
            logger.error(f"MCP HTTP error: {e.response.status_code} - {e.response.text}")
            raise MCPClientError(
                f"MCP server returned {e.response.status_code}: {e.response.text}"
            )

        except httpx.RequestError as e:
            logger.error(f"MCP request error: {e}")
            raise MCPClientError(f"Failed to connect to MCP server: {e}")

    async def initialize(self) -> dict[str, Any]:
        """
        Initialize the MCP session.

        Returns:
            Server capabilities and info
        """
        if self._initialized:
            return {}

        result = await self._request(
            "initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "orders-analytics-agent",
                    "version": "1.0.0",
                },
            },
        )
        
        self._initialized = True
        logger.info(f"MCP session initialized: {self.session_id}")
        logger.info(f"Server info: {result.get('serverInfo', {})}")
        
        return result

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        List available tools from the MCP server.

        Returns:
            List of tool definitions
        """
        if not self._initialized:
            await self.initialize()

        result = await self._request("tools/list", request_id=2)
        return result.get("tools", [])

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
        if not self._initialized:
            await self.initialize()

        logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")

        result = await self._request(
            "tools/call",
            params={
                "name": tool_name,
                "arguments": arguments or {},
            },
            request_id=3,
        )

        logger.debug(f"MCP tool response: {result}")

        # Handle MCP content array format
        if "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                # Return the text content from the first item
                first_item = content[0]
                if isinstance(first_item, dict) and "text" in first_item:
                    # Try to parse as JSON if possible
                    try:
                        return json.loads(first_item["text"])
                    except json.JSONDecodeError:
                        return first_item["text"]
            return content

        return result

    # Convenience methods for specific tools

    async def get_all_orders(self) -> Any:
        """
        Get all orders from the system.

        Returns:
            List of all orders
        """
        return await self.call_tool("get-all-orders", {})

    async def get_orders_by_customer_id(self, customer_id: str) -> Any:
        """
        Get orders for a specific customer.

        Args:
            customer_id: The customer ID to look up

        Returns:
            List of orders for the customer
        """
        return await self.call_tool("get-orders-by-customer-id", {"id": customer_id})

    async def create_order(
        self,
        customer_id: str,
        customer_name: str,
        product_name: str,
        price: float,
        order_date: str,
    ) -> Any:
        """
        Create a new order.

        Args:
            customer_id: The unique identifier of the customer
            customer_name: The full name of the customer
            product_name: The name of the product being purchased
            price: The total price of the order
            order_date: The order date in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)

        Returns:
            Created order details with generated orderID
        """
        return await self.call_tool("create-order", {
            "customerID": customer_id,
            "customerName": customer_name,
            "productName": product_name,
            "price": price,
            "orderDate": order_date,
        })
