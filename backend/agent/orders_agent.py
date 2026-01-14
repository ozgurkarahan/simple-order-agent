"""Oz's Order Management Agent using Claude Agent SDK with External MCP Server."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any, TYPE_CHECKING

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

if TYPE_CHECKING:
    from api.config_models import MCPServerConfig

logger = logging.getLogger(__name__)

# System prompt for Oz's Order Management Agent
SYSTEM_PROMPT = """You are Oz's Order Management Agent. Your role is to help users query, analyze, and manage order data.

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

# Planning prompt for generating execution plans
PLANNING_PROMPT = """You are an expert task planner. Your job is to analyze a user request and create a detailed execution plan.

Given a user request, you must generate a structured plan with the following format:

{
  "description": "Brief summary of what will be accomplished",
  "phases": [
    {
      "id": "phase_1",
      "name": "Data Collection",
      "description": "Gather required data",
      "tasks": [
        {
          "id": "task_1_1",
          "description": "Call get-all-orders tool to retrieve orders"
        },
        {
          "id": "task_1_2",
          "description": "Validate data completeness"
        }
      ]
    },
    {
      "id": "phase_2",
      "name": "Analysis",
      "description": "Process and analyze the data",
      "tasks": [
        {
          "id": "task_2_1",
          "description": "Calculate total revenue per customer"
        },
        {
          "id": "task_2_2",
          "description": "Sort customers by spending"
        },
        {
          "id": "task_2_3",
          "description": "Identify top 5 customers"
        }
      ]
    },
    {
      "id": "phase_3",
      "name": "Presentation",
      "description": "Format and present results",
      "tasks": [
        {
          "id": "task_3_1",
          "description": "Format results as a table"
        },
        {
          "id": "task_3_2",
          "description": "Present findings with key insights"
        }
      ]
    }
  ]
}

Guidelines for creating plans:
1. **Group tasks into logical phases** - Data Collection, Analysis, Presentation, etc.
2. **Be specific but concise** - Each task should be clear and actionable
3. **Use mixed granularity** - Combine high-level goals with technical steps
4. **Include all necessary steps** - Don't skip validation, formatting, or presentation
5. **Order tasks logically** - Ensure dependencies are respected
6. **Think about tools** - Mention which MCP tools will be used

For simple requests (like "show me all orders"), create simpler plans with fewer phases.
For complex requests (like "analyze trends and create a report"), create detailed multi-phase plans.

Return ONLY valid JSON. No additional text or explanation."""

class OrdersAgent:
    """
    Claude-powered agent for order analytics using External MCP Server.

    Uses the Claude Agent SDK with .mcp.json configuration or dynamic MCP config
    to connect to the Orders MCP server.
    """

    def __init__(
        self, 
        model: str = "claude-sonnet-4-20250514",
        mcp_config: MCPServerConfig | None = None,
        mcp_configs: list[MCPServerConfig] | None = None
    ):
        """
        Initialize the Orders Agent.

        Args:
            model: Claude model to use
            mcp_config: Optional single MCP server configuration (legacy, for backward compatibility)
            mcp_configs: Optional list of MCP server configurations
        """
        self.model = model
        
        # Support both single and multiple configs for backward compatibility
        if mcp_configs is not None:
            self.mcp_configs = mcp_configs
        elif mcp_config is not None:
            self.mcp_configs = [mcp_config]
        else:
            self.mcp_configs = []
        
        self.clients: dict[str, ClaudeSDKClient] = {}

        if self.mcp_configs:
            active_count = sum(1 for c in self.mcp_configs if c.is_active)
            server_names = [c.name for c in self.mcp_configs if c.is_active]
            logger.info(f"Orders Agent initialized with model: {model} using {active_count} active MCP server(s): {', '.join(server_names)}")
        else:
            logger.info(f"Orders Agent initialized with model: {model} using .mcp.json config")

    def _get_or_create_client(self, conversation_id: str) -> ClaudeSDKClient:
        """
        Get or create a ClaudeSDKClient for a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            ClaudeSDKClient instance for this conversation
        """
        if conversation_id not in self.clients:
            options = self._build_options()
            self.clients[conversation_id] = ClaudeSDKClient(options)
            logger.debug(f"Created new client for conversation: {conversation_id}")
        return self.clients[conversation_id]

    def _build_options(self) -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions with external MCP server configuration."""
        if self.mcp_configs:
            # Use dynamic MCP configuration with multiple servers
            mcp_servers = {}
            for config in self.mcp_configs:
                if config.is_active:  # Only include active servers
                    mcp_servers[config.name] = {
                        "type": "http",
                        "url": config.url,
                        "headers": config.headers
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
        # Use default conversation ID if none provided
        conv_id = conversation_id or "default"
        
        # Get or create client for this conversation
        client = self._get_or_create_client(conv_id)

        try:
            # Send message and stream response
            # ClaudeSDKClient automatically maintains conversation history
            async with client:
                await client.query(message)
                async for event in client.receive_response():                    
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
                        # Emit tool result event
                        if hasattr(event, "result") and event.result:
                            yield {
                                "type": "tool_result",
                                "data": json.dumps({"result": str(event.result)}),
                            }

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

    def clear_conversation(self, conversation_id: str) -> None:
        """
        Clear conversation history by removing the client.
        
        Args:
            conversation_id: Conversation ID to clear
        """
        if conversation_id in self.clients:
            del self.clients[conversation_id]
            logger.info(f"Cleared conversation: {conversation_id}")

    def clear_all_conversations(self) -> None:
        """Clear all conversation histories."""
        self.clients.clear()
        logger.info("Cleared all conversations")

    async def generate_plan(self, message: str, conversation_id: str | None = None) -> dict[str, Any]:
        """
        Generate an execution plan for a user request.

        Args:
            message: User's request
            conversation_id: Optional conversation ID for context

        Returns:
            Plan dictionary with description and phases
        """
        conv_id = conversation_id or "default"

        # Create a temporary client for planning (doesn't maintain conversation history)
        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=PLANNING_PROMPT,
            permission_mode="bypassPermissions",
            max_turns=1,  # Single turn for planning
        )

        try:
            async with ClaudeSDKClient(options) as planning_client:
                await planning_client.query(f"Create a plan for this request:\n\n{message}")

                plan_text = []
                async for event in planning_client.receive_response():
                    if isinstance(event, AssistantMessage):
                        for block in event.content:
                            if hasattr(block, "text"):
                                plan_text.append(block.text)

                # Parse the JSON plan
                full_text = "".join(plan_text)
                # Extract JSON from potential markdown code blocks
                if "```json" in full_text:
                    full_text = full_text.split("```json")[1].split("```")[0]
                elif "```" in full_text:
                    full_text = full_text.split("```")[1].split("```")[0]

                plan = json.loads(full_text.strip())
                logger.info(f"Generated plan with {len(plan.get('phases', []))} phases")
                return plan

        except Exception as e:
            logger.error(f"Plan generation error: {e}")
            # Return a simple fallback plan
            return {
                "description": "Execute the requested task",
                "phases": [
                    {
                        "id": "phase_1",
                        "name": "Execution",
                        "description": "Process the request",
                        "tasks": [
                            {
                                "id": "task_1_1",
                                "description": message
                            }
                        ]
                    }
                ]
            }
