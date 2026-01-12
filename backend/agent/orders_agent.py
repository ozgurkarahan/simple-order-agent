"""Orders Analytics Agent using Claude with MCP tools."""

import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator

import anthropic

from mcp import MCPClient

logger = logging.getLogger(__name__)

# System prompt for the Orders Analytics Agent
SYSTEM_PROMPT = """You are an intelligent Orders Analytics Agent. Your role is to help users query, analyze, and manage order data.

You have access to the following tools:
1. **get_all_orders** - Retrieve all orders from the system. Use this for overview queries or when no specific customer is mentioned.
2. **get_orders_by_customer_id** - Get orders for a specific customer by their ID. Use this when the user asks about a particular customer's orders.
3. **create_order** - Create a new order. Requires customer ID, customer name, product name, price, and order date.

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

For order creation:
- Ensure all required fields are provided
- Use ISO 8601 format for dates (YYYY-MM-DDTHH:MM:SS)
- Confirm the order details with the user before creating

Be conversational but concise. Focus on delivering value through actionable insights."""

# Tool definitions for Claude - matching the actual MCP server tools
TOOLS = [
    {
        "name": "get_all_orders",
        "description": "Retrieve all customer orders from the system. Each order record contains the product name, amount, size, and order date. Use this for overview queries, analytics, or when no specific customer is mentioned.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_orders_by_customer_id",
        "description": "Get a customer's complete order history by their customer ID. Returns a list of their orders including product name, quantity, price, size, and order date. Use this when the user asks about a specific customer's orders.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The unique identifier of the customer (e.g., 'CUST001', 'C12345')",
                },
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "create_order",
        "description": "Create a new order record in the system. All fields are required. Returns the generated order ID for tracking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The unique identifier of the customer placing the order",
                },
                "customer_name": {
                    "type": "string",
                    "description": "The full name of the customer",
                },
                "product_name": {
                    "type": "string",
                    "description": "The name of the product being purchased",
                },
                "price": {
                    "type": "number",
                    "description": "The total price or cost of the order",
                },
                "order_date": {
                    "type": "string",
                    "description": "The order timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). Use current date/time if not specified.",
                },
            },
            "required": ["customer_id", "customer_name", "product_name", "price", "order_date"],
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

        if tool_name == "get_all_orders":
            return await self.mcp_client.get_all_orders()

        elif tool_name == "get_orders_by_customer_id":
            return await self.mcp_client.get_orders_by_customer_id(
                customer_id=tool_input["customer_id"],
            )

        elif tool_name == "create_order":
            # Use current datetime if not provided
            order_date = tool_input.get("order_date")
            if not order_date:
                order_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
            return await self.mcp_client.create_order(
                customer_id=tool_input["customer_id"],
                customer_name=tool_input["customer_name"],
                product_name=tool_input["product_name"],
                price=tool_input["price"],
                order_date=order_date,
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
