"""Orders Analytics Agent using Claude with MCP tools."""

import json
import logging
from typing import Any, AsyncGenerator

import anthropic

from mcp import MCPClient

logger = logging.getLogger(__name__)

# System prompt for the Orders Analytics Agent
SYSTEM_PROMPT = """You are an intelligent Orders Analytics Agent. Your role is to help users query, analyze, and manage order data.

You have access to the following tools:
1. **list_orders** - Query orders with filters (status, date range, customer ID, limit)
2. **get_order** - Get detailed information about a specific order by ID
3. **create_order** - Create a new order with customer ID, items, and shipping address

When users ask about orders, you should:
- Use the appropriate tool to fetch data
- Analyze the results and provide clear, actionable insights
- Format monetary values properly (e.g., $1,234.56)
- Summarize large datasets with key statistics
- Ask clarifying questions if the request is ambiguous

For analytics queries:
- Calculate totals, averages, and trends when relevant
- Highlight important patterns or anomalies
- Suggest follow-up analyses that might be useful

Be conversational but concise. Focus on delivering value through actionable insights."""

# Tool definitions for Claude
TOOLS = [
    {
        "name": "list_orders",
        "description": "List and filter orders from the order management system. Use this to query orders by status, date range, customer, or to get recent orders.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by order status (e.g., 'pending', 'processing', 'shipped', 'delivered', 'cancelled')",
                },
                "date_from": {
                    "type": "string",
                    "description": "Filter orders from this date (ISO 8601 format, e.g., '2024-01-01')",
                },
                "date_to": {
                    "type": "string",
                    "description": "Filter orders until this date (ISO 8601 format, e.g., '2024-01-31')",
                },
                "customer_id": {
                    "type": "string",
                    "description": "Filter by customer ID",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of orders to return (default: 10)",
                },
            },
        },
    },
    {
        "name": "get_order",
        "description": "Get detailed information about a specific order by its ID. Use this when the user asks about a specific order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The unique order ID to retrieve",
                },
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "create_order",
        "description": "Create a new order in the system. Use this when the user wants to place a new order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID for the order",
                },
                "items": {
                    "type": "array",
                    "description": "List of items in the order",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "string",
                                "description": "Product ID",
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "Quantity of the product",
                            },
                            "price": {
                                "type": "number",
                                "description": "Unit price of the product",
                            },
                        },
                        "required": ["product_id", "quantity"],
                    },
                },
                "shipping_address": {
                    "type": "object",
                    "description": "Shipping address for the order",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "state": {"type": "string"},
                        "zip": {"type": "string"},
                        "country": {"type": "string"},
                    },
                },
            },
            "required": ["customer_id", "items"],
        },
    },
]


class OrdersAgent:
    """
    Claude-powered agent for order analytics.

    Uses MCP tools to interact with the Orders server and provides
    natural language analytics capabilities.
    """

    def __init__(
        self,
        api_key: str,
        mcp_client: MCPClient,
        model: str = "claude-sonnet-4-20250514",
    ):
        """
        Initialize the Orders Agent.

        Args:
            api_key: Anthropic API key
            mcp_client: MCP client for orders server
            model: Claude model to use
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.mcp_client = mcp_client
        self.model = model

        # Conversation history storage (in-memory for now)
        self.conversations: dict[str, list[dict]] = {}

        logger.info(f"Orders Agent initialized with model: {model}")

    def _get_conversation(self, conversation_id: str | None) -> list[dict]:
        """Get or create conversation history."""
        if not conversation_id:
            return []
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        return self.conversations[conversation_id]

    async def _execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        """
        Execute a tool call via MCP.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters

        Returns:
            Tool execution result
        """
        logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

        if tool_name == "list_orders":
            return await self.mcp_client.list_orders(
                status=tool_input.get("status"),
                date_from=tool_input.get("date_from"),
                date_to=tool_input.get("date_to"),
                customer_id=tool_input.get("customer_id"),
                limit=tool_input.get("limit"),
            )

        elif tool_name == "get_order":
            return await self.mcp_client.get_order(
                order_id=tool_input["order_id"],
            )

        elif tool_name == "create_order":
            return await self.mcp_client.create_order(
                customer_id=tool_input["customer_id"],
                items=tool_input["items"],
                shipping_address=tool_input.get("shipping_address"),
            )

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def chat(
        self,
        message: str,
        conversation_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Process a chat message and stream the response.

        Args:
            message: User's message
            conversation_id: Optional conversation ID for context

        Yields:
            Event dictionaries with type and data
        """
        # Get conversation history
        history = self._get_conversation(conversation_id)

        # Add user message to history
        messages = history + [{"role": "user", "content": message}]

        # Keep processing until we get a final response
        while True:
            # Create the API request
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Process each content block
            for block in response.content:
                if block.type == "text":
                    yield {
                        "type": "message",
                        "data": json.dumps({"type": "text", "content": block.text}),
                    }

                elif block.type == "tool_use":
                    # Notify about tool use
                    yield {
                        "type": "tool_use",
                        "data": json.dumps({
                            "type": "tool_use",
                            "tool": block.name,
                            "input": block.input,
                        }),
                    }

                    # Execute the tool
                    try:
                        result = await self._execute_tool(block.name, block.input)
                        tool_result = {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result) if not isinstance(result, str) else result,
                        }
                    except Exception as e:
                        logger.error(f"Tool execution error: {e}")
                        tool_result = {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error executing tool: {str(e)}",
                            "is_error": True,
                        }

                    # Notify about tool result
                    yield {
                        "type": "tool_result",
                        "data": json.dumps({
                            "type": "tool_result",
                            "result": tool_result["content"],
                        }),
                    }

                    # Add assistant message and tool result to continue conversation
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": [tool_result]})

            # Check if we need to continue (tool use) or stop
            if response.stop_reason == "end_turn":
                # Save conversation history
                if conversation_id:
                    # Only save user message and final assistant response
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": response.content})
                break

            elif response.stop_reason != "tool_use":
                # Unexpected stop reason
                logger.warning(f"Unexpected stop reason: {response.stop_reason}")
                break

    async def chat_sync(
        self,
        message: str,
        conversation_id: str | None = None,
    ) -> str:
        """
        Process a chat message and return the complete response.

        Args:
            message: User's message
            conversation_id: Optional conversation ID for context

        Returns:
            Complete response text
        """
        response_text = []

        async for event in self.chat(message, conversation_id):
            if event["type"] == "message":
                data = json.loads(event["data"])
                if data.get("type") == "text":
                    response_text.append(data["content"])

        return "\n".join(response_text)
