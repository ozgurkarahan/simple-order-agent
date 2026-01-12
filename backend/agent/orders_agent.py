"""Orders Analytics Agent using Claude Agent SDK with External MCP Server."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any, TYPE_CHECKING

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    query,
)

if TYPE_CHECKING:
    from api.config_models import MCPServerConfig

logger = logging.getLogger(__name__)

# System prompt for the Orders Analytics Agent
SYSTEM_PROMPT = """You are an intelligent Orders Analytics Agent. Your role is to help users query, analyze, and manage order data.

You have access to the following tools from the orders MCP server:
1. **get-all-orders** - Retrieve all orders from the system. Use this for overview queries or when no specific customer is mentioned.
2. **get-orders-by-customer-id** - Get orders for a specific customer by their ID. Use this when the user asks about a particular customer's orders.
3. **create-order** - Create a new order. Requires customer ID, customer name, product name, price, and order date.

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

class OrdersAgent:
    """
    Claude-powered agent for order analytics using External MCP Server.

    Uses the Claude Agent SDK with .mcp.json configuration or dynamic MCP config
    to connect to the Orders MCP server.
    """

    def __init__(
        self, 
        model: str = "claude-sonnet-4-20250514",
        mcp_config: MCPServerConfig | None = None
    ):
        """
        Initialize the Orders Agent.

        Args:
            model: Claude model to use
            mcp_config: Optional MCP server configuration. If None, uses .mcp.json
        """
        self.model = model
        self.mcp_config = mcp_config
        self.conversations: dict[str, list[dict]] = {}

        if mcp_config:
            logger.info(f"Orders Agent initialized with model: {model} using MCP server: {mcp_config.name}")
        else:
            logger.info(f"Orders Agent initialized with model: {model} using .mcp.json config")

    def _get_conversation(self, conversation_id: str | None) -> list[dict]:
        """Get or create conversation history."""
        if not conversation_id:
            return []
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        return self.conversations[conversation_id]

    def _build_options(self) -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions with external MCP server configuration."""
        if self.mcp_config:
            # Use dynamic MCP configuration
            mcp_servers = {
                self.mcp_config.name: {
                    "type": "http",
                    "url": self.mcp_config.url,
                    "headers": self.mcp_config.headers
                }
            }
            return ClaudeAgentOptions(
                model=self.model,
                system_prompt=SYSTEM_PROMPT,
                mcp_servers=mcp_servers,
                permission_mode="bypassPermissions",
                max_turns=10,
            )
        else:
            # Fall back to .mcp.json configuration
            return ClaudeAgentOptions(
                model=self.model,
                system_prompt=SYSTEM_PROMPT,
                setting_sources=["project"],  # Loads .mcp.json automatically
                permission_mode="bypassPermissions",
                max_turns=10,
            )

    async def chat(
        self,
        message: str,
        conversation_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Process a chat message and stream the response using Claude Agent SDK.

        Args:
            message: User's message
            conversation_id: Optional conversation ID for context

        Yields:
            Event dictionaries with type and data for SSE streaming
        """
        options = self._build_options()

        try:
            async for event in query(prompt=message, options=options):
                if isinstance(event, AssistantMessage):
                    for block in event.content:
                        if hasattr(block, "text"):
                            yield {
                                "type": "message",
                                "data": json.dumps({"type": "text", "content": block.text}),
                            }
                        elif hasattr(block, "name"):
                            yield {
                                "type": "tool_use",
                                "data": json.dumps({
                                    "type": "tool_use",
                                    "tool": block.name,
                                    "input": getattr(block, "input", {}),
                                }),
                            }

                elif isinstance(event, ResultMessage):
                    if hasattr(event, "content"):
                        for block in event.content:
                            if hasattr(block, "text"):
                                yield {
                                    "type": "message",
                                    "data": json.dumps({"type": "text", "content": block.text}),
                                }

            if conversation_id:
                history = self._get_conversation(conversation_id)
                history.append({"role": "user", "content": message})

        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield {
                "type": "error",
                "data": json.dumps({"type": "error", "message": str(e)}),
            }

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
