"""Agent Card configuration for A2A discovery."""

from functools import lru_cache

from .models import AgentCard, AgentCapabilities, AuthConfig, AuthType, Skill


@lru_cache
def get_agent_card() -> AgentCard:
    """
    Get the Agent Card for A2A discovery.

    The Agent Card describes this agent's capabilities and is served
    at /.well-known/agent.json for discovery by other agents.
    """
    return AgentCard(
        name="Orders Analytics Agent",
        description="AI-powered agent for querying and analyzing order data. "
        "Supports natural language queries for order analytics, "
        "order lookup, and order creation.",
        version="1.0.0",
        url="http://localhost:8000",  # Updated dynamically in production
        documentation_url="http://localhost:8000/docs",
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=True,
        ),
        skills=[
            Skill(
                id="list_orders",
                name="List Orders",
                description="Query and filter orders by various criteria including "
                "status, date range, customer ID. Returns order summaries.",
                tags=["orders", "query", "analytics"],
                examples=[
                    "Show me all orders from last week",
                    "List pending orders",
                    "Find orders for customer C12345",
                    "Show the 5 most recent orders",
                ],
            ),
            Skill(
                id="get_order",
                name="Get Order Details",
                description="Get detailed information about a specific order by ID. "
                "Returns complete order data including items, status, and shipping.",
                tags=["orders", "details", "lookup"],
                examples=[
                    "What's the status of order #ORD-12345?",
                    "Get details for order ABC123",
                    "Show me order information for ORD-2024-001",
                ],
            ),
            Skill(
                id="create_order",
                name="Create Order",
                description="Create a new order with customer ID, items, and optional "
                "shipping address. Returns the created order details.",
                tags=["orders", "create", "transaction"],
                examples=[
                    "Create an order for customer C001 with 2 units of product P100",
                    "Place a new order with items X, Y, Z for customer ABC",
                ],
            ),
            Skill(
                id="analyze_orders",
                name="Analyze Orders",
                description="Perform analytics queries on order data. Calculate totals, "
                "averages, trends, and provide insights from order data.",
                tags=["analytics", "insights", "reporting"],
                examples=[
                    "What's our total revenue this month?",
                    "Which products are selling the most?",
                    "Show me order trends for the last quarter",
                    "What's the average order value?",
                ],
            ),
        ],
        authentication=AuthConfig(
            type=AuthType.BEARER,
        ),
        default_input_modes=["text"],
        default_output_modes=["text"],
    )
